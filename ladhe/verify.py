#!/usr/bin/env python3
"""
verify.py — Standalone Ladhe signature verifier.

NO external dependencies. Just Python 3.9+ and the standard library.
Drop into any folder containing a Ladhe demo kit and run it.

Usage
-----
Auto-detect mode (the easy one):
    python3 verify.py

    Looks in the current directory for:
        ca.cert.pem
        alice.cert.pem  (or any *.cert.pem signed by ca.cert.pem)
        <document>.<ext>  with matching <document>.<ext>.sig

Explicit mode (for ad-hoc checks):
    python3 verify.py verify-cert  <subject_cert> <ca_cert>
    python3 verify.py verify-doc   <document> <signature> <subject_cert>

Exit codes
----------
    0  all verifications passed
    1  one or more verifications failed
    2  usage / file-not-found error

License: CC BY 4.0 — same as the rest of the Ladhe reference.
"""

import base64
import hashlib
import json
import os
import random
import struct
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------
# Constants — must match ladhe.py
# ---------------------------------------------------------------------
HASH = hashlib.sha256
LAMBDA_BYTES = 32
ENCODING_VERSION = 0x01

PEM_BEGIN_CERT = "-----BEGIN LADHE CERTIFICATE-----"
PEM_END_CERT = "-----END LADHE CERTIFICATE-----"

# Match terminal capability (TTY) for colour output, else plain text.
_TTY = sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"
GREEN = "\033[92m" if _TTY else ""
RED = "\033[91m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


# ---------------------------------------------------------------------
# Primality (Miller-Rabin)
# ---------------------------------------------------------------------
_SMALL_PRIMES = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109,
)


def is_prime(n: int, rounds: int = 20) -> bool:
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


# ---------------------------------------------------------------------
# Indexed-pair compression and canonical encoding
# ---------------------------------------------------------------------
def pair_compress(primes: Sequence[int]) -> Tuple[int, ...]:
    k = len(primes)
    if k < 3 or k % 2 == 0:
        raise ValueError(f"k must be odd and >= 3, got {k}")
    W: List[int] = []
    for i in range(0, k - 1, 2):
        W.append(primes[i] + primes[i + 1])
    W.append(primes[-1])
    return tuple(W)


def _int_to_be(n: int) -> bytes:
    if n == 0:
        return b"\x00"
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


def encode_W(W: Sequence[int]) -> bytes:
    m = len(W)
    if m > 255:
        raise ValueError("tuple length exceeds 255")
    out = bytearray([ENCODING_VERSION, m])
    for w in W:
        wb = _int_to_be(w)
        out += struct.pack(">H", len(wb))
        out += wb
    return bytes(out)


# ---------------------------------------------------------------------
# Signature decoding (matches ladhe.Signature.encode/decode)
# ---------------------------------------------------------------------
def decode_signature(data: bytes) -> Tuple[Tuple[int, ...], bytes]:
    """Return (primes, message)."""
    if len(data) < 1:
        raise ValueError("signature too short")
    k = data[0]
    off = 1
    primes: List[int] = []
    for _ in range(k):
        if off + 2 > len(data):
            raise ValueError("signature truncated (length prefix)")
        (ln,) = struct.unpack_from(">H", data, off)
        off += 2
        if off + ln > len(data):
            raise ValueError("signature truncated (prime bytes)")
        primes.append(int.from_bytes(data[off:off + ln], "big"))
        off += ln
    if off + 4 > len(data):
        raise ValueError("signature truncated (message length)")
    (ml,) = struct.unpack_from(">I", data, off)
    off += 4
    if off + ml > len(data):
        raise ValueError("signature truncated (message bytes)")
    message = bytes(data[off:off + ml])
    return tuple(primes), message


# ---------------------------------------------------------------------
# Core Ladhe verify
# ---------------------------------------------------------------------
def verify_ladhe(message: bytes, sig_primes: Tuple[int, ...],
                 sig_message: bytes, pk_prime: int, pk_h: bytes) -> bool:
    """Verify a Ladhe one-time signature."""
    if sig_message != message:
        return False
    primes = sig_primes
    k = len(primes)
    if k < 3 or k % 2 == 0:
        return False
    for p in primes:
        if p <= 2 or not is_prime(p):
            return False
    if list(primes) != sorted(set(primes)) or len(set(primes)) != k:
        return False
    if sum(primes) != pk_prime:
        return False
    W = pair_compress(primes)
    h = HASH(encode_W(W)).digest()
    return h == pk_h


# ---------------------------------------------------------------------
# Cert parsing
# ---------------------------------------------------------------------
def parse_cert_pem(text: str) -> dict:
    """Parse a -----BEGIN LADHE CERTIFICATE----- block and return the JSON."""
    text = text.strip()
    lines = text.splitlines()
    if not lines or lines[0].strip() != PEM_BEGIN_CERT:
        raise ValueError(f"expected {PEM_BEGIN_CERT}")
    if lines[-1].strip() != PEM_END_CERT:
        raise ValueError(f"expected {PEM_END_CERT}")
    body = "".join(l.strip() for l in lines[1:-1])
    raw = base64.b64decode(body.encode("ascii")).decode("utf-8")
    return json.loads(raw)


def cert_body_bytes(cert: dict) -> bytes:
    """The canonical bytes the CA signed (everything except the signature)."""
    body = {k: v for k, v in cert.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def cert_public_key(cert: dict) -> Tuple[int, bytes]:
    """Return (prime, h) from a parsed cert's public_key field."""
    pk = cert["public_key"]
    return int(pk["prime"]), bytes.fromhex(pk["h"])


# ---------------------------------------------------------------------
# High-level verifications
# ---------------------------------------------------------------------
def verify_cert_against_ca(subject_cert_text: str, ca_cert_text: str) -> Tuple[bool, str]:
    """Return (ok, reason)."""
    subj = parse_cert_pem(subject_cert_text)
    ca = parse_cert_pem(ca_cert_text)

    if subj.get("issuer") != ca.get("subject"):
        return False, ("subject's issuer does not match the CA's subject "
                       f"({subj.get('issuer')} != {ca.get('subject')})")

    sig_value_hex = subj["signature"]["value"]
    sig_bytes = bytes.fromhex(sig_value_hex)
    sig_primes, sig_message = decode_signature(sig_bytes)
    body = cert_body_bytes(subj)
    ca_prime, ca_h = cert_public_key(ca)

    ok = verify_ladhe(body, sig_primes, sig_message, ca_prime, ca_h)
    return ok, ("ok" if ok else "signature does not verify against the CA")


def verify_document(doc_bytes: bytes, sig_bytes: bytes,
                    subject_cert_text: str) -> Tuple[bool, str]:
    """Return (ok, reason)."""
    subj = parse_cert_pem(subject_cert_text)
    sig_primes, sig_message = decode_signature(sig_bytes)
    subj_prime, subj_h = cert_public_key(subj)

    ok = verify_ladhe(doc_bytes, sig_primes, sig_message, subj_prime, subj_h)
    return ok, ("ok" if ok else "signature does not match the document or the cert")


# ---------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------
def pass_(msg: str) -> None:
    print(f"  {GREEN}✓ PASS{RESET}  {msg}")


def fail_(msg: str, detail: str = "") -> None:
    print(f"  {RED}✗ FAIL{RESET}  {msg}")
    if detail:
        print(f"           {detail}")


def header(msg: str) -> None:
    print(f"\n{BOLD}{msg}{RESET}")


# ---------------------------------------------------------------------
# Auto-detect mode
# ---------------------------------------------------------------------
def auto_detect(folder: Path) -> int:
    """Find canonical files in `folder` and verify everything.
    Returns process exit code."""
    ca_path = folder / "ca.cert.pem"
    if not ca_path.exists():
        print(f"{RED}error:{RESET} ca.cert.pem not found in {folder}")
        return 2

    subject_paths = sorted(
        p for p in folder.glob("*.cert.pem") if p.name != "ca.cert.pem"
    )
    if not subject_paths:
        print(f"{RED}error:{RESET} no subject certs (*.cert.pem) found in {folder}")
        return 2

    sig_paths = sorted(folder.glob("*.sig"))

    print(f"{BOLD}Ladhe verification report{RESET}")
    print(f"  Folder: {folder}")
    print(f"  CA:     {ca_path.name}")
    for sp in subject_paths:
        print(f"  Subject cert: {sp.name}")
    for sp in sig_paths:
        print(f"  Signed file:  {sp.name[:-4]}  (sig: {sp.name})")

    ca_text = ca_path.read_text(encoding="utf-8")
    all_ok = True

    header("Step 1 — Cert chain checks")
    for subj_path in subject_paths:
        subj_text = subj_path.read_text(encoding="utf-8")
        ok, reason = verify_cert_against_ca(subj_text, ca_text)
        if ok:
            pass_(f"{subj_path.name} chains to CA")
        else:
            fail_(f"{subj_path.name} does NOT chain to CA", reason)
            all_ok = False

    header("Step 2 — Document signatures")
    if not sig_paths:
        print(f"  {YELLOW}(no .sig files found — nothing to verify){RESET}")
    else:
        for sig_path in sig_paths:
            doc_path = sig_path.with_suffix("")  # strips .sig
            if doc_path.suffix == "":
                # Means the original file had no suffix — try removing only ".sig"
                doc_path = Path(str(sig_path)[:-4])
            if not doc_path.exists():
                fail_(f"document for {sig_path.name} not found "
                      f"(expected {doc_path.name})")
                all_ok = False
                continue
            doc_bytes = doc_path.read_bytes()
            sig_bytes = sig_path.read_bytes()

            # Find which subject cert signed this — try each.
            verified_with = None
            last_reason = "no matching cert"
            for subj_path in subject_paths:
                subj_text = subj_path.read_text(encoding="utf-8")
                ok, reason = verify_document(doc_bytes, sig_bytes, subj_text)
                if ok:
                    verified_with = subj_path
                    break
                last_reason = reason

            if verified_with:
                pass_(f"{doc_path.name}  signed by  {verified_with.name}")
            else:
                fail_(f"{doc_path.name}  signature INVALID", last_reason)
                all_ok = False

    print()
    if all_ok:
        print(f"{GREEN}{BOLD}All verifications passed.{RESET}")
        return 0
    print(f"{RED}{BOLD}One or more verifications FAILED.{RESET}")
    print(f"{RED}Hint: if you tampered with a document or substituted a "
          f"file, that's the expected behaviour — the math caught you.{RESET}")
    return 1


# ---------------------------------------------------------------------
# Explicit mode
# ---------------------------------------------------------------------
def cmd_verify_cert(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 verify.py verify-cert <subject_cert.pem> <ca_cert.pem>")
        return 2
    subj_text = Path(argv[0]).read_text(encoding="utf-8")
    ca_text = Path(argv[1]).read_text(encoding="utf-8")
    ok, reason = verify_cert_against_ca(subj_text, ca_text)
    print(f"verify: {ok} ({reason})")
    return 0 if ok else 1


def cmd_verify_doc(argv: List[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 verify.py verify-doc <document> <signature> <subject_cert.pem>")
        return 2
    doc_bytes = Path(argv[0]).read_bytes()
    sig_bytes = Path(argv[1]).read_bytes()
    subj_text = Path(argv[2]).read_text(encoding="utf-8")
    ok, reason = verify_document(doc_bytes, sig_bytes, subj_text)
    print(f"verify: {ok} ({reason})")
    return 0 if ok else 1


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
def main(argv: List[str]) -> int:
    if len(argv) == 0:
        return auto_detect(Path.cwd())
    cmd = argv[0]
    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if cmd == "verify-cert":
        return cmd_verify_cert(argv[1:])
    if cmd == "verify-doc":
        return cmd_verify_doc(argv[1:])
    print(f"unknown command: {cmd}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
