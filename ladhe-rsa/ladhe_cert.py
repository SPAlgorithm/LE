"""
ladhe_cert.py — Experimental certificate format backed by
Ladhe signatures.

This is NOT yet an X.509 certificate. As of April 2026 the
signature algorithm has a registered OID — 1.3.6.1.4.1.65644.1.1
(id-ladhe-signature) under IANA PEN 65644 — but full X.509
interop still requires ASN.1 DER encoding and an OpenSSL provider
plugin, both of which are future work. For now, this format is a
self-contained JSON-based structure (with the OID embedded in
every certificate and signature) suitable for:

    * Local testing
    * Demonstrating what a Ladhe PKI would look like
    * Educational purposes
    * Prototype interop between Ladhe-aware tools

It is NOT suitable for:

    * Real TLS / HTTPS
    * Apple Keychain, macOS code signing
    * Interoperating with browsers, OpenSSL, or any standards-
      compliant PKI software

See CERTIFICATES.md in this folder for the full rationale and
the path toward real-world interop.
"""

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import ladhe_rsa as LR


CERT_VERSION = 1
# "ladhe-sig-v1" is the human-readable algorithm name; the OID below
# is the globally unique identifier registered under IANA PEN 65644
# (LESecure AI / SPAlgorithm). See OID_REGISTRY.md for the full arc.
CERT_ALGORITHM = "ladhe-sig-v1"
CERT_ALGORITHM_OID = "1.3.6.1.4.1.65644.1.1"       # id-ladhe-signature
PUBLIC_KEY_OID     = "1.3.6.1.4.1.65644.1.2"       # id-ladhe-publicKey
CERT_PROFILE_OID   = "1.3.6.1.4.1.65644.2.1"       # id-ladhe-cert-v1
PEM_BEGIN = "-----BEGIN LADHE CERTIFICATE-----"
PEM_END   = "-----END LADHE CERTIFICATE-----"
KEY_PEM_BEGIN = "-----BEGIN LADHE PRIVATE KEY-----"
KEY_PEM_END   = "-----END LADHE PRIVATE KEY-----"


# ----------------------------------------------------------------------
# Certificate data structure
# ----------------------------------------------------------------------
@dataclass
class LadheCertificate:
    version: int
    serial: str                       # hex string
    issuer: dict                      # e.g. {"CN": "My CA"}
    subject: dict                     # e.g. {"CN": "alice@example.com"}
    not_before: str                   # ISO 8601
    not_after: str                    # ISO 8601
    public_key: dict                  # {"algorithm", "algorithm_oid", "prime", "h"}
    extensions: dict                  # arbitrary dict
    signature: dict = field(
        default_factory=lambda: {"algorithm": CERT_ALGORITHM, "value": ""}
    )

    # --- serialization -------------------------------------------------
    def body_bytes(self) -> bytes:
        """Canonical bytes of the cert body (everything except signature),
        used as the message to sign / verify."""
        d = asdict(self)
        d.pop("signature", None)
        return json.dumps(
            d, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, indent=2)

    def to_pem(self) -> str:
        """PEM-like format with base64-encoded JSON body."""
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        # Wrap at 64 chars for readability (PEM convention)
        wrapped = "\n".join(
            encoded[i:i + 64] for i in range(0, len(encoded), 64)
        )
        return f"{PEM_BEGIN}\n{wrapped}\n{PEM_END}\n"

    @classmethod
    def from_pem(cls, text: str) -> "LadheCertificate":
        lines = text.strip().splitlines()
        if not lines or lines[0].strip() != PEM_BEGIN:
            raise ValueError("missing PEM begin marker")
        if lines[-1].strip() != PEM_END:
            raise ValueError("missing PEM end marker")
        body = "".join(lines[1:-1])
        raw = base64.b64decode(body.encode("ascii")).decode("utf-8")
        d = json.loads(raw)
        return cls(**d)

    # --- key helpers --------------------------------------------------
    def subject_public_key(self) -> LR.PublicKey:
        pk = self.public_key
        return LR.PublicKey(
            prime=int(pk["prime"]),
            h=bytes.fromhex(pk["h"]),
        )


# ----------------------------------------------------------------------
# Private-key storage (PEM-like)
# ----------------------------------------------------------------------
def encode_private_key(sk: LR.PrivateKey) -> str:
    """Serialize a private key to PEM-like format. UNENCRYPTED —
    demo only; do not use for real keys."""
    d = {
        "prime": str(sk.prime),
        "primes": [str(x) for x in sk.primes],
    }
    raw = json.dumps(d, sort_keys=True, separators=(",", ":"))
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    wrapped = "\n".join(
        encoded[i:i + 64] for i in range(0, len(encoded), 64)
    )
    return f"{KEY_PEM_BEGIN}\n{wrapped}\n{KEY_PEM_END}\n"


def decode_private_key(text: str) -> LR.PrivateKey:
    lines = text.strip().splitlines()
    if not lines or lines[0].strip() != KEY_PEM_BEGIN:
        raise ValueError("missing private-key PEM begin marker")
    if lines[-1].strip() != KEY_PEM_END:
        raise ValueError("missing private-key PEM end marker")
    body = "".join(lines[1:-1])
    raw = base64.b64decode(body.encode("ascii")).decode("utf-8")
    d = json.loads(raw)
    return LR.PrivateKey(
        prime=int(d["prime"]),
        primes=tuple(int(x) for x in d["primes"]),
    )


# ----------------------------------------------------------------------
# CA operations
# ----------------------------------------------------------------------
def _pk_to_dict(pk: LR.PublicKey) -> dict:
    return {
        "algorithm": CERT_ALGORITHM,
        "algorithm_oid": PUBLIC_KEY_OID,
        "prime": str(pk.prime),
        "h": pk.h.hex(),
    }


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_ca(
    common_name: str,
    validity_days: int = 3650,
    up1: int = 8,
) -> Tuple[LadheCertificate, LR.PrivateKey]:
    """Create a self-signed CA certificate + its private key."""
    pk, sk = LR.keygen(up1=up1)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    cert = LadheCertificate(
        version=CERT_VERSION,
        serial=secrets.token_hex(16),
        issuer={"CN": common_name},
        subject={"CN": common_name},           # self-signed
        not_before=now.isoformat(),
        not_after=(now + timedelta(days=validity_days)).isoformat(),
        public_key=_pk_to_dict(pk),
        extensions={
            "basicConstraints": {"CA": True, "pathLenConstraint": 0},
            "keyUsage": ["keyCertSign", "cRLSign"],
        },
    )
    sig = LR.sign(cert.body_bytes(), sk, pk)
    cert.signature = {
        "algorithm": CERT_ALGORITHM,
        "algorithm_oid": CERT_ALGORITHM_OID,
        "value": sig.encode().hex(),
    }
    return cert, sk


def issue_certificate(
    ca_cert: LadheCertificate,
    ca_sk: LR.PrivateKey,
    subject_cn: str,
    subject_pk: LR.PublicKey,
    validity_days: int = 365,
    extensions: Optional[dict] = None,
) -> LadheCertificate:
    """CA issues a certificate for a subject's public key."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    cert = LadheCertificate(
        version=CERT_VERSION,
        serial=secrets.token_hex(16),
        issuer=ca_cert.subject,
        subject={"CN": subject_cn},
        not_before=now.isoformat(),
        not_after=(now + timedelta(days=validity_days)).isoformat(),
        public_key=_pk_to_dict(subject_pk),
        extensions=extensions or {
            "basicConstraints": {"CA": False},
            "keyUsage": ["digitalSignature"],
        },
    )
    ca_pk = ca_cert.subject_public_key()
    sig = LR.sign(cert.body_bytes(), ca_sk, ca_pk)
    cert.signature = {
        "algorithm": CERT_ALGORITHM,
        "algorithm_oid": CERT_ALGORITHM_OID,
        "value": sig.encode().hex(),
    }
    return cert


# ----------------------------------------------------------------------
# Verification
# ----------------------------------------------------------------------
def _is_within_validity(cert: LadheCertificate, now: Optional[datetime] = None) -> bool:
    now = now or datetime.now(timezone.utc)
    nb = datetime.fromisoformat(cert.not_before)
    na = datetime.fromisoformat(cert.not_after)
    return nb <= now <= na


def verify_certificate(
    cert: LadheCertificate,
    issuer_cert: LadheCertificate,
    now: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """Check that `cert` was signed by `issuer_cert`'s key, and is
    currently within its validity window.

    Returns (ok, reason). On success, reason is 'ok'.
    """
    if cert.signature.get("algorithm") != CERT_ALGORITHM:
        return False, f"unknown algorithm: {cert.signature.get('algorithm')}"
    if cert.issuer != issuer_cert.subject:
        return False, "issuer name does not match issuer cert subject"
    if not _is_within_validity(cert, now):
        return False, "certificate not within validity period"
    if not _is_within_validity(issuer_cert, now):
        return False, "issuer certificate not within validity period"

    # Reconstruct signature + issuer public key
    try:
        sig_bytes = bytes.fromhex(cert.signature["value"])
        sig = LR.Signature.decode(sig_bytes)
    except Exception as e:
        return False, f"signature decode error: {e}"

    issuer_pk = issuer_cert.subject_public_key()
    try:
        ok = LR.verify(cert.body_bytes(), sig, issuer_pk)
    except Exception as e:
        return False, f"signature verification error: {e}"
    return (ok, "ok" if ok else "signature does not verify")


def verify_chain(
    end_cert: LadheCertificate,
    intermediates: List[LadheCertificate],
    trust_anchor: LadheCertificate,
    now: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """Verify a chain: end_cert -> intermediates... -> trust_anchor.

    `trust_anchor` must be self-signed (root CA). All intermediates
    are verified bottom-up against their parents.
    """
    # Trust anchor must be self-signed and valid.
    if trust_anchor.issuer != trust_anchor.subject:
        return False, "trust anchor is not self-signed"
    ok, reason = verify_certificate(trust_anchor, trust_anchor, now)
    if not ok:
        return False, f"trust anchor: {reason}"

    chain = list(intermediates) + [trust_anchor]
    cur = end_cert
    for parent in chain:
        ok, reason = verify_certificate(cur, parent, now)
        if not ok:
            return False, f"link {cur.subject.get('CN')} -> "\
                          f"{parent.subject.get('CN')}: {reason}"
        cur = parent
    return True, "ok"


# ----------------------------------------------------------------------
# Document signing with a subject key
# ----------------------------------------------------------------------
def sign_document(
    document: bytes,
    subject_cert: LadheCertificate,
    subject_sk: LR.PrivateKey,
) -> bytes:
    """Sign a document under a subject's certificate key.
    Returns opaque bytes (the signature blob); pair with the
    subject cert for verification."""
    subject_pk = subject_cert.subject_public_key()
    sig = LR.sign(document, subject_sk, subject_pk)
    return sig.encode()


def verify_document(
    document: bytes,
    signature_bytes: bytes,
    subject_cert: LadheCertificate,
) -> bool:
    """Verify a document against a subject certificate's public key."""
    sig = LR.Signature.decode(signature_bytes)
    return LR.verify(document, sig, subject_cert.subject_public_key())


# ----------------------------------------------------------------------
# File helpers
# ----------------------------------------------------------------------
def write_cert(path: Path, cert: LadheCertificate) -> None:
    Path(path).write_text(cert.to_pem(), encoding="utf-8")


def read_cert(path: Path) -> LadheCertificate:
    return LadheCertificate.from_pem(Path(path).read_text(encoding="utf-8"))


def write_private_key(path: Path, sk: LR.PrivateKey) -> None:
    Path(path).write_text(encode_private_key(sk), encoding="utf-8")


def read_private_key(path: Path) -> LR.PrivateKey:
    return decode_private_key(Path(path).read_text(encoding="utf-8"))
