"""
demo_cert.py — End-to-end demonstration of Ladhe-RSA
certificates.

Simulates a small PKI:

  1.  Root CA self-signs its own certificate.
  2.  Subject (Alice) generates a key pair.
  3.  CA issues Alice a certificate.
  4.  A third party verifies Alice's cert against the CA cert.
  5.  Alice signs a document under her cert.
  6.  Bob verifies the document + cert chain.
  7.  Tampered document fails verification.

All cert and key files are written to ./demo_pki/ so you can
inspect them (open them in TextEdit — they're PEM-wrapped JSON).
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

import ladhe_rsa as LR
import ladhe_cert as LC


OUTDIR = Path(__file__).resolve().parent / "demo_pki"


def banner(text: str) -> None:
    print()
    print("=" * 64)
    print(f"  {text}")
    print("=" * 64)


def pretty_cert(cert: LC.LadheCertificate) -> None:
    print(f"  issuer:     {cert.issuer}")
    print(f"  subject:    {cert.subject}")
    print(f"  serial:     {cert.serial}")
    print(f"  not_before: {cert.not_before}")
    print(f"  not_after:  {cert.not_after}")
    print(f"  key algo:   {cert.public_key['algorithm']}")
    print(f"  key prime:  {cert.public_key['prime']}")
    print(f"  sig bytes:  {len(cert.signature['value']) // 2}")


def main() -> int:
    if OUTDIR.exists():
        shutil.rmtree(OUTDIR)
    OUTDIR.mkdir(parents=True)

    # -----------------------------------------------------------
    banner("1. Bootstrap the root CA (self-signed)")
    # -----------------------------------------------------------
    ca_cert, ca_sk = LC.create_ca("Ladhe Test Root CA")
    LC.write_cert(OUTDIR / "ca.cert.pem", ca_cert)
    LC.write_private_key(OUTDIR / "ca.key.pem", ca_sk)
    print(f"  wrote:  {OUTDIR / 'ca.cert.pem'}")
    print(f"  wrote:  {OUTDIR / 'ca.key.pem'}  (keep secret)")
    pretty_cert(ca_cert)

    # -----------------------------------------------------------
    banner("2. Alice generates her own key pair")
    # -----------------------------------------------------------
    alice_pk, alice_sk = LR.keygen(min_prime_bits=24)
    LC.write_private_key(OUTDIR / "alice.key.pem", alice_sk)
    print(f"  wrote:  {OUTDIR / 'alice.key.pem'}  (Alice keeps secret)")
    print(f"  Alice's prime:      {alice_pk.prime}")
    print(f"  Alice's commitment: {alice_pk.commitment.hex()[:32]}...")

    # -----------------------------------------------------------
    banner("3. CA issues Alice a certificate")
    # -----------------------------------------------------------
    alice_cert = LC.issue_certificate(
        ca_cert, ca_sk,
        subject_cn="alice@example.com",
        subject_pk=alice_pk,
        validity_days=365,
    )
    LC.write_cert(OUTDIR / "alice.cert.pem", alice_cert)
    print(f"  wrote:  {OUTDIR / 'alice.cert.pem'}")
    pretty_cert(alice_cert)

    # -----------------------------------------------------------
    banner("4. A third party verifies Alice's cert against the CA")
    # -----------------------------------------------------------
    # Load from disk — simulates a verifier that never touched
    # the in-memory objects.
    ca_loaded    = LC.read_cert(OUTDIR / "ca.cert.pem")
    alice_loaded = LC.read_cert(OUTDIR / "alice.cert.pem")

    ok, reason = LC.verify_certificate(alice_loaded, ca_loaded)
    print(f"  alice.cert verifies under ca.cert:  {ok}  ({reason})")

    ok, reason = LC.verify_chain(alice_loaded, [], ca_loaded)
    print(f"  chain(alice -> ca) verifies:        {ok}  ({reason})")

    # Negative test: pretend a different CA tries to vouch for Alice
    rogue_cert, _rogue_sk = LC.create_ca("Rogue CA")
    ok, reason = LC.verify_certificate(alice_loaded, rogue_cert)
    print(f"  alice.cert under ROGUE CA (expect False): "
          f"{ok}  ({reason})")

    # -----------------------------------------------------------
    banner("5. Alice signs a document under her cert")
    # -----------------------------------------------------------
    document = b"I, Alice, hereby authorise the quantum-era migration."
    doc_sig = LC.sign_document(document, alice_cert, alice_sk)
    (OUTDIR / "document.txt").write_bytes(document)
    (OUTDIR / "document.sig").write_bytes(doc_sig)
    print(f"  document  ({len(document)} bytes)  -> {OUTDIR/'document.txt'}")
    print(f"  signature ({len(doc_sig)} bytes) -> {OUTDIR/'document.sig'}")

    # -----------------------------------------------------------
    banner("6. Bob verifies the document and the cert chain")
    # -----------------------------------------------------------
    loaded_doc = (OUTDIR / "document.txt").read_bytes()
    loaded_sig = (OUTDIR / "document.sig").read_bytes()
    loaded_alice_cert = LC.read_cert(OUTDIR / "alice.cert.pem")
    loaded_ca_cert    = LC.read_cert(OUTDIR / "ca.cert.pem")

    ok, reason = LC.verify_chain(loaded_alice_cert, [], loaded_ca_cert)
    print(f"  cert chain:                {ok}  ({reason})")
    doc_ok = LC.verify_document(loaded_doc, loaded_sig, loaded_alice_cert)
    print(f"  document signature valid:  {doc_ok}")
    print(f"  overall trust:             {ok and doc_ok}")

    # -----------------------------------------------------------
    banner("7. Tamper with the document — verification must fail")
    # -----------------------------------------------------------
    tampered = loaded_doc.replace(b"Alice", b"Mallory")
    tampered_ok = LC.verify_document(tampered, loaded_sig, loaded_alice_cert)
    print(f"  tampered document verifies (expect False):  {tampered_ok}")

    # -----------------------------------------------------------
    banner("Files written")
    # -----------------------------------------------------------
    for p in sorted(OUTDIR.iterdir()):
        size = p.stat().st_size
        print(f"  {size:>6d}  {p.name}")

    print()
    print("Open any of these in TextEdit or `cat` to inspect.")
    print("The cert files are base64-encoded JSON wrapped in PEM markers.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
