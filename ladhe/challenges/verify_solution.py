#!/usr/bin/env python3
"""verify_solution.py — adjudicator for Ladhe cryptanalysis claims.

Given a challenge `(P, h)` and a candidate prime tuple, this script
applies every check the bounty's "what counts as a break" criterion
requires:

  1. Each entry is a positive integer
  2. Each entry is an odd prime (Miller-Rabin)
  3. The tuple is strictly ascending (p_1 < p_2 < ... < p_k)
  4. k ∈ {3, 5, 7}
  5. sum(primes) == P
  6. SHA-256(encode(pair_compress(primes))) == h

If all six pass, the submission is a valid Ladhe witness for (P, h).

Usage:
  python3 verify_solution.py manifest.json <challenge-id> <p_1> <p_2> ... <p_k>
  python3 verify_solution.py --raw <P> <h_hex> <p_1> <p_2> ... <p_k>

Exit codes:
  0  valid witness — break confirmed at the challenge tier
  1  invalid — one or more checks failed (with the failing check named)
  2  usage error / file not found
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Reuse the canonical implementations from the parent package.
# (Same encoding, hash, primality test the verifier in the demo kit
# uses — keeps adjudication consistent with the live verifier.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ladhe import HASH, encode_W, is_prime, pair_compress  # noqa: E402


def fail(reason: str) -> None:
    print(f"FAIL: {reason}")
    sys.exit(1)


def verify(P: int, h_hex: str, primes: list[int]) -> None:
    print(f"Verifying solution against (P, h):")
    print(f"  P     = {P}")
    print(f"  h     = {h_hex}")
    print(f"  k     = {len(primes)}")
    print(f"  primes = {tuple(primes)}")
    print()

    if len(primes) not in (3, 5, 7):
        fail(f"k = {len(primes)} not in {{3, 5, 7}} — required by the scheme")

    if any(p <= 0 for p in primes):
        fail("at least one entry is non-positive")

    if any(p % 2 == 0 for p in primes):
        fail("at least one entry is even — primes must be odd "
             "(p_1 ≥ 3, not 2)")

    for i, p in enumerate(primes):
        if not is_prime(p):
            fail(f"entry p_{i+1} = {p} is not prime")

    if primes != sorted(primes):
        fail("tuple is not in ascending order")

    if len(set(primes)) != len(primes):
        fail("entries are not distinct")

    if sum(primes) != P:
        fail(f"sum(primes) = {sum(primes)} ≠ P = {P}")

    W = pair_compress(tuple(primes))
    encoded = encode_W(W)
    h_computed = HASH(encoded).hexdigest()

    print(f"  W      = {W}")
    print(f"  encode(W).hex() = {encoded.hex()}")
    print(f"  SHA-256(encode(W)).hex() = {h_computed}")
    print()

    if h_computed != h_hex.lower():
        fail(f"SHA-256 mismatch:\n"
             f"  computed = {h_computed}\n"
             f"  expected = {h_hex.lower()}")

    print("PASS — all six checks succeeded.")
    print("This submission is a valid Ladhe witness for the given "
          "(P, h).")
    print()
    print("If this challenge is at BRONZE tier or higher, you have")
    print("achieved a cryptographic break. Submit via:")
    print("  GitHub: https://github.com/SPAlgorithm/LE/issues")
    print("  Email:  spalgorithm@gmail.com")


def usage() -> None:
    print(__doc__)
    sys.exit(2)


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        usage()

    if argv[1] == "--raw":
        # Direct (P, h) form — no manifest lookup.
        if len(argv) < 5:
            usage()
        try:
            P = int(argv[2])
        except ValueError:
            fail(f"could not parse P = {argv[2]} as integer")
        h_hex = argv[3]
        try:
            primes = [int(x) for x in argv[4:]]
        except ValueError:
            fail("could not parse primes as integers")
        verify(P, h_hex, primes)
        return

    # Manifest mode: file path + challenge id + primes
    if len(argv) < 4:
        usage()

    manifest_path = Path(argv[1])
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        sys.exit(2)

    challenge_id = argv[2]
    try:
        primes = [int(x) for x in argv[3:]]
    except ValueError:
        fail("could not parse primes as integers")

    with open(manifest_path) as f:
        manifest = json.load(f)

    challenge = next(
        (c for c in manifest["challenges"] if c["id"] == challenge_id),
        None,
    )
    if challenge is None:
        ids = ", ".join(c["id"] for c in manifest["challenges"])
        print(f"Challenge id {challenge_id!r} not found in manifest.")
        print(f"Available ids: {ids}")
        sys.exit(2)

    print(f"Challenge:  {challenge['id']}  ({challenge['tier']}, "
          f"bits={challenge['bits']})")
    print(f"Reward:     {challenge.get('reward', 'see CRYPTANALYSIS.md')}")
    print()

    verify(int(challenge["P"]), challenge["h_hex"], primes)


if __name__ == "__main__":
    main(sys.argv)
