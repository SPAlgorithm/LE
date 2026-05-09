#!/usr/bin/env python3
"""demo_pair_compress_noninj.py

Demonstrates the non-injectivity of pair_compress on prime tuples.

Two distinct ascending tuples of distinct odd primes can yield the
same compressed witness W, hence the same SHA-256 hash, hence both
verify against the same Ladhe public key (P, h).

This is a deliberate property of the scheme, documented in
SP_Paper.tex Remark rmk:pc-noninj (§3.4). h commits to W, not to a
specific prime tuple; any prime tuple opening to the same W verifies
identically. An attacker who only sees (P, h) still has to find some
preimage of h in the encoded-W space — a SHA-256 preimage problem.

Run:
    python3 demo_pair_compress_noninj.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ladhe import (  # noqa: E402
    HASH,
    PrivateKey,
    PublicKey,
    Signature,
    encode_W,
    pair_compress,
    sign,
    verify,
)


def main() -> None:
    A = (3, 17, 23, 29, 1009)
    B = (7, 13, 23, 29, 1009)

    print("Two ascending tuples of distinct odd primes:")
    print(f"  A = {A}")
    print(f"  B = {B}")
    print()
    print(f"  sum(A) = {sum(A)}")
    print(f"  sum(B) = {sum(B)}")
    assert sum(A) == sum(B), "tuples must sum to the same P"

    WA = pair_compress(A)
    WB = pair_compress(B)
    print()
    print(f"  pair_compress(A) = {WA}")
    print(f"  pair_compress(B) = {WB}")
    assert WA == WB, "pair_compress collision did not occur"

    encA = encode_W(WA)
    encB = encode_W(WB)
    print()
    print(f"  encode_W(WA) = {encA.hex()}")
    print(f"  encode_W(WB) = {encB.hex()}")

    hA = HASH(encA).digest()
    hB = HASH(encB).digest()
    print()
    print(f"  SHA-256(encA) = {hA.hex()}")
    print(f"  SHA-256(encB) = {hB.hex()}")
    assert hA == hB, "hashes should be identical"

    P = sum(A)
    pk = PublicKey(prime=P, h=hA)
    sk = PrivateKey(prime=P, primes=A)
    msg = b"hello"

    sig_legit = sign(msg, sk)
    sig_alt = Signature(primes=B, message=msg)

    legit_ok = verify(msg, sig_legit, pk)
    alt_ok = verify(msg, sig_alt, pk)
    print()
    print(f"  verify(legit witness A) = {legit_ok}")
    print(f"  verify(alt witness B)   = {alt_ok}")
    assert legit_ok and alt_ok

    print()
    print("Result: both A and B are valid witnesses for the same (P, h).")
    print("This matches SP_Paper.tex Remark rmk:pc-noninj. The hash h")
    print("commits to W, not to a specific prime tuple; recovering any")
    print("opening from (P, h) alone still requires a SHA-256 preimage.")


if __name__ == "__main__":
    main()
