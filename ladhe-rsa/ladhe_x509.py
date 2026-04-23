"""ladhe_x509.py — DER-encoded X.509 export for Ladhe-RSA certificates.

Converts LadheCertificate objects (the internal JSON format used by
ladhe_cert.py) into standards-compliant DER / PEM X.509 certificates
bearing the IANA-registered OIDs:

    1.3.6.1.4.1.65644.1.1   id-ladhe-rsa-signature
    1.3.6.1.4.1.65644.1.2   id-ladhe-rsa-publicKey

Once written, the resulting .der / .pem files can be inspected by
standard tools:

    openssl asn1parse -in cert.der -inform DER
    openssl x509 -in cert.pem -text -noout

OpenSSL will print "Signature Algorithm: 1.3.6.1.4.1.65644.1.1" and
"Public Key Algorithm: 1.3.6.1.4.1.65644.1.2" — both unrecognised
as the plugin-provider work is still ahead — but the cert structure
itself parses and validates at the ASN.1 level.

Requires: asn1crypto  (install via:  pip install asn1crypto)
"""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from asn1crypto import x509, algos, keys, core
except ImportError as e:
    raise ImportError(
        "ladhe_x509 requires asn1crypto. Install with:\n"
        "    pip install asn1crypto"
    ) from e

import ladhe_rsa as LR
import ladhe_cert as LC


# OIDs — must match OID_REGISTRY.md
OID_LADHE_SIG = "1.3.6.1.4.1.65644.1.1"   # id-ladhe-rsa-signature
OID_LADHE_PK  = "1.3.6.1.4.1.65644.1.2"   # id-ladhe-rsa-publicKey
OID_LADHE_CERT_V1 = "1.3.6.1.4.1.65644.2.1"


# ----------------------------------------------------------------------
# Make our algorithm OIDs round-trip cleanly through asn1crypto's
# ObjectIdentifier map (so .native returns a friendly name, not the
# raw dotted form). Purely cosmetic; the DER output is unchanged.
# ----------------------------------------------------------------------
keys.PublicKeyAlgorithmId._map[OID_LADHE_PK] = "ladhe_rsa"
keys.PublicKeyAlgorithmId._reverse_map = None
algos.SignedDigestAlgorithmId._map[OID_LADHE_SIG] = "ladhe_rsa_signature"
algos.SignedDigestAlgorithmId._reverse_map = None


# ----------------------------------------------------------------------
# Our own SubjectPublicKeyInfo variant. asn1crypto's built-in
# PublicKeyInfo has a spec_callback that only knows about RSA/EC/DSA,
# so it rejects any unknown algorithm. We bypass it entirely by
# defining a sibling class with a plain OctetBitString for the
# `public_key` field. DER bytes produced by this class are identical
# in shape to a standard SubjectPublicKeyInfo.
# ----------------------------------------------------------------------
class LadheAlgorithmIdentifier(core.Sequence):
    _fields = [
        ("algorithm",  core.ObjectIdentifier),
        ("parameters", core.Any, {"optional": True}),
    ]


class LadheSubjectPublicKeyInfo(core.Sequence):
    _fields = [
        ("algorithm",  LadheAlgorithmIdentifier),
        ("public_key", core.OctetBitString),
    ]


class LadheValidity(core.Sequence):
    _fields = [
        ("not_before", x509.Time),
        ("not_after",  x509.Time),
    ]


class LadheTbsCertificate(core.Sequence):
    _fields = [
        ("version",              x509.Version, {"explicit": 0, "default": "v1"}),
        ("serial_number",        core.Integer),
        ("signature",            LadheAlgorithmIdentifier),
        ("issuer",               x509.Name),
        ("validity",             LadheValidity),
        ("subject",              x509.Name),
        ("subject_public_key_info", LadheSubjectPublicKeyInfo),
    ]


class LadheASN1Certificate(core.Sequence):
    _fields = [
        ("tbs_certificate",     LadheTbsCertificate),
        ("signature_algorithm", LadheAlgorithmIdentifier),
        ("signature_value",     core.OctetBitString),
    ]


# ----------------------------------------------------------------------
# LadheRSAPublicKey ::= SEQUENCE {
#     prime       INTEGER,
#     commitment  OCTET STRING,
#     salt        OCTET STRING
# }
# ----------------------------------------------------------------------
class LadheRSAPublicKey(core.Sequence):
    _fields = [
        ("prime",      core.Integer),
        ("commitment", core.OctetString),
        ("salt",       core.OctetString),
    ]


def _publickey_der(pk: LR.PublicKey) -> bytes:
    """Encode a Ladhe-RSA public key as DER bytes."""
    return LadheRSAPublicKey({
        "prime":      pk.prime,
        "commitment": pk.commitment,
        "salt":       pk.salt,
    }).dump()


def _publickey_from_der(data: bytes) -> LR.PublicKey:
    parsed = LadheRSAPublicKey.load(data)
    return LR.PublicKey(
        prime=int(parsed["prime"].native),
        commitment=bytes(parsed["commitment"].native),
        salt=bytes(parsed["salt"].native),
    )


# ----------------------------------------------------------------------
# Name helpers — we only use CN, which keeps encoding simple
# ----------------------------------------------------------------------
def _make_name(name_dict: dict) -> x509.Name:
    # asn1crypto's Name.build accepts a dict keyed by full attribute names.
    long_keys = {
        "CN": "common_name",
        "O":  "organization_name",
        "OU": "organizational_unit_name",
        "C":  "country_name",
        "ST": "state_or_province_name",
        "L":  "locality_name",
    }
    return x509.Name.build({
        long_keys.get(k, k): v for k, v in name_dict.items()
    })


def _name_to_dict(name: x509.Name) -> dict:
    short = {
        "common_name":                "CN",
        "organization_name":          "O",
        "organizational_unit_name":   "OU",
        "country_name":               "C",
        "state_or_province_name":     "ST",
        "locality_name":              "L",
    }
    return {short.get(k, k): v for k, v in name.native.items()}


# ----------------------------------------------------------------------
# Time helpers — ISO 8601 <-> ASN.1 Time
# ----------------------------------------------------------------------
def _iso_to_time(iso: str) -> x509.Time:
    dt = datetime.fromisoformat(iso)
    # RFC 5280: use UTCTime for dates before 2050, GeneralizedTime otherwise.
    if dt.year < 2050:
        return x509.Time(name="utc_time", value=dt)
    return x509.Time(name="general_time", value=dt)


def _time_to_iso(t: x509.Time) -> str:
    return t.native.replace(microsecond=0).isoformat()


# ----------------------------------------------------------------------
# Certificate  <->  DER
# ----------------------------------------------------------------------
def cert_to_x509_der(ladhe_cert: LC.LadheCertificate) -> bytes:
    """Convert a LadheCertificate to DER-encoded X.509 bytes."""
    lr_pk = ladhe_cert.subject_public_key()
    pk_der = _publickey_der(lr_pk)

    spki = LadheSubjectPublicKeyInfo({
        "algorithm": LadheAlgorithmIdentifier({
            "algorithm":  OID_LADHE_PK,
            "parameters": core.Null(),
        }),
        "public_key": core.OctetBitString(pk_der),
    })

    sig_algo = LadheAlgorithmIdentifier({
        "algorithm":  OID_LADHE_SIG,
        "parameters": core.Null(),
    })

    tbs = LadheTbsCertificate({
        "version":       "v3",
        "serial_number": int(ladhe_cert.serial, 16),
        "signature":     sig_algo,
        "issuer":        _make_name(ladhe_cert.issuer),
        "validity": LadheValidity({
            "not_before": _iso_to_time(ladhe_cert.not_before),
            "not_after":  _iso_to_time(ladhe_cert.not_after),
        }),
        "subject":       _make_name(ladhe_cert.subject),
        "subject_public_key_info": spki,
    })

    sig_value = bytes.fromhex(ladhe_cert.signature["value"])

    certificate = LadheASN1Certificate({
        "tbs_certificate":     tbs,
        "signature_algorithm": sig_algo,
        "signature_value":     sig_value,
    })

    return certificate.dump()


def cert_to_x509_pem(ladhe_cert: LC.LadheCertificate) -> str:
    """Convert a LadheCertificate to PEM-encoded X.509."""
    der = cert_to_x509_der(ladhe_cert)
    b64 = base64.b64encode(der).decode("ascii")
    wrapped = "\n".join(b64[i:i + 64] for i in range(0, len(b64), 64))
    return f"-----BEGIN CERTIFICATE-----\n{wrapped}\n-----END CERTIFICATE-----\n"


def cert_from_x509_der(der: bytes) -> LC.LadheCertificate:
    """Convert DER-encoded X.509 bytes back into a LadheCertificate."""
    parsed = LadheASN1Certificate.load(der)
    tbs = parsed["tbs_certificate"]

    inner_oid = tbs["signature"]["algorithm"].dotted
    outer_oid = parsed["signature_algorithm"]["algorithm"].dotted
    if inner_oid != OID_LADHE_SIG or outer_oid != OID_LADHE_SIG:
        raise ValueError(
            f"not a Ladhe-RSA certificate — signature OID is "
            f"{outer_oid} (expected {OID_LADHE_SIG})"
        )

    spki = tbs["subject_public_key_info"]
    pk_der = spki["public_key"].native
    lr_pk = _publickey_from_der(pk_der)

    sig_value = parsed["signature_value"].native

    return LC.LadheCertificate(
        version=LC.CERT_VERSION,
        serial=format(int(tbs["serial_number"].native), "x").zfill(2),
        issuer=_name_to_dict(tbs["issuer"]),
        subject=_name_to_dict(tbs["subject"]),
        not_before=_time_to_iso(tbs["validity"]["not_before"]),
        not_after=_time_to_iso(tbs["validity"]["not_after"]),
        public_key={
            "algorithm":     LC.CERT_ALGORITHM,
            "algorithm_oid": OID_LADHE_PK,
            "prime":      str(lr_pk.prime),
            "commitment": lr_pk.commitment.hex(),
            "salt":       lr_pk.salt.hex(),
        },
        extensions={},
        signature={
            "algorithm":     LC.CERT_ALGORITHM,
            "algorithm_oid": OID_LADHE_SIG,
            "value":         sig_value.hex(),
        },
    )


def cert_from_x509_pem(pem: str) -> LC.LadheCertificate:
    """Convert PEM-encoded X.509 text back into a LadheCertificate."""
    lines = [l.strip() for l in pem.strip().splitlines()
             if l and "BEGIN" not in l and "END" not in l]
    der = base64.b64decode("".join(lines))
    return cert_from_x509_der(der)


# ----------------------------------------------------------------------
# File helpers
# ----------------------------------------------------------------------
def write_x509_der(path: Path, ladhe_cert: LC.LadheCertificate) -> Path:
    der = cert_to_x509_der(ladhe_cert)
    Path(path).write_bytes(der)
    return Path(path)


def write_x509_pem(path: Path, ladhe_cert: LC.LadheCertificate) -> Path:
    pem = cert_to_x509_pem(ladhe_cert)
    Path(path).write_text(pem, encoding="utf-8")
    return Path(path)


def read_x509_der(path: Path) -> LC.LadheCertificate:
    return cert_from_x509_der(Path(path).read_bytes())


def read_x509_pem(path: Path) -> LC.LadheCertificate:
    return cert_from_x509_pem(Path(path).read_text(encoding="utf-8"))
