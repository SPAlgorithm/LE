#!/usr/bin/env python3
"""brute_force_baseline.py — reference brute-force solver for Ladhe
cryptanalysis challenges.

What this is:
  A *baseline* attacker. It enumerates valid prime tuples summing to P
  and hashes each, looking for a match against h. No cryptographic
  shortcuts. Pure brute force — exactly the work an attacker must do
  in the worst case.

What this is NOT:
  - A cryptanalytic break. Brute force at λ = 256 is infeasible
    (~2^256 hash evaluations). This solver succeeds only at
    sub-cryptographic parameter sizes.
  - Optimized. The code is written for clarity, not speed. A
    determined attacker with a tuned C/Rust solver could be
    100-1000× faster.

Tier expectations (laptop, 1 core, this script):
  bits=32   solves in seconds to a few minutes
  bits=48   solves in minutes
  bits=64   solves in hours
  bits=96   weeks (in principle; consider the result a baseline)
  bits=128  infeasible

If this baseline solves a challenge at BRONZE tier (256-bit) or
higher, that means SHA-256 itself is broken — call your local
cryptographer.

Usage:
  python3 brute_force_baseline.py manifest.json <challenge-id>
  python3 brute_force_baseline.py --raw <P> <h_hex>
  python3 brute_force_baseline.py --raw <P> <h_hex> --max-time 600

Exit codes:
  0  found a witness (printed to stdout)
  1  exhausted candidate space (no witness within reach)
  2  usage error / file not found
  3  --max-time elapsed before finding a witness
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ladhe import HASH, encode_W, is_prime, pair_compress  # noqa: E402


def all_odd_primes_below(n: int):
    """Yield odd primes < n in ascending order using Miller-Rabin.

    For larger n this is the bottleneck; smarter solvers would use a
    segmented sieve. For baseline / teaching purposes this is fine.
    """
    p = 3
    while p < n:
        if is_prime(p):
            yield p
        p += 2


def attempt_k(P: int, h_target: bytes, k: int,
              max_seconds: float | None,
              start: float) -> tuple[int, ...] | None:
    """Try to find a k-prime decomposition of P producing h_target.

    Strategy: enumerate p_1 < p_2 < ... < p_{k-1}, derive p_k as
    P − sum(others), and check primality + the hash.
    """
    primes_cache: list[int] = []
    cache_iter = all_odd_primes_below(P)

    def get_primes_up_to(idx: int) -> list[int]:
        # Lazy cache
        while len(primes_cache) <= idx:
            try:
                primes_cache.append(next(cache_iter))
            except StopIteration:
                break
        return primes_cache

    # Outer loop: enumerate the first k-1 primes in ascending order.
    # We bound them so that the smallest possible p_k is still > p_{k-1}.
    # Because primes are positive: p_1 + p_2 + ... + p_{k-1} < P,
    # and p_k = P - sum > p_{k-1}.

    # Guard: enumerate index ranges with checkpoint progress prints.
    last_progress = time.time()
    candidates_tried = 0

    if k == 3:
        get_primes_up_to(64)  # warmup
        i = 0
        while True:
            p1 = next_prime(primes_cache, i, cache_iter)
            if p1 is None:
                break
            if p1 * 3 >= P:  # smallest possible 3-prime sum exceeds P
                break
            j = i + 1
            while True:
                p2 = next_prime(primes_cache, j, cache_iter)
                if p2 is None:
                    break
                if p1 + p2 * 2 >= P:
                    break
                p3 = P - p1 - p2
                if p3 > p2 and p3 % 2 == 1 and is_prime(p3):
                    candidates_tried += 1
                    primes = (p1, p2, p3)
                    h = HASH(encode_W(pair_compress(primes))).digest()
                    if h == h_target:
                        return primes

                if max_seconds is not None and time.time() - start > max_seconds:
                    return None

                if time.time() - last_progress > 5.0:
                    elapsed = time.time() - start
                    print(f"  [k=3] p1={p1}, p2={p2}, "
                          f"candidates tried={candidates_tried}, "
                          f"elapsed={elapsed:.1f}s",
                          file=sys.stderr)
                    last_progress = time.time()
                j += 1
            i += 1
        return None

    # Generic k=5 or k=7 — enumerate combinations of k-1 small primes
    # then derive p_k. Slower but works.
    base_primes = []
    for p in all_odd_primes_below(P):
        base_primes.append(p)
        if len(base_primes) > 100_000:
            break  # bound the candidate base; baseline solver

    for combo in itertools.combinations(base_primes, k - 1):
        if max_seconds is not None and time.time() - start > max_seconds:
            return None
        ssum = sum(combo)
        if ssum >= P:
            continue
        last = P - ssum
        if last <= combo[-1]:
            continue
        if last % 2 == 0:
            continue
        if not is_prime(last):
            continue
        primes = tuple(list(combo) + [last])
        h = HASH(encode_W(pair_compress(primes))).digest()
        candidates_tried += 1
        if h == h_target:
            return primes
        if time.time() - last_progress > 5.0:
            elapsed = time.time() - start
            print(f"  [k={k}] candidates tried={candidates_tried}, "
                  f"elapsed={elapsed:.1f}s",
                  file=sys.stderr)
            last_progress = time.time()

    return None


def next_prime(cache: list[int], idx: int, gen) -> int | None:
    while idx >= len(cache):
        try:
            cache.append(next(gen))
        except StopIteration:
            return None
    return cache[idx]


def solve(P: int, h_hex: str, max_seconds: float | None
          ) -> tuple[int, ...] | None:
    h_target = bytes.fromhex(h_hex)
    print(f"Brute-force search:")
    print(f"  P     = {P}  ({P.bit_length()} bits)")
    print(f"  h     = {h_hex}")
    print(f"  max_time = {max_seconds}s" if max_seconds else
          "  max_time = unbounded")
    print()

    start = time.time()

    for k in (3, 5, 7):
        print(f"Trying k = {k} ...")
        result = attempt_k(P, h_target, k, max_seconds, start)
        if result is not None:
            elapsed = time.time() - start
            print(f"\nFOUND k={k}: {result}")
            print(f"sum(primes) = {sum(result)}  (matches P)")
            print(f"elapsed: {elapsed:.2f}s")
            return result
        if max_seconds is not None and time.time() - start > max_seconds:
            print(f"\n--max-time reached ({max_seconds}s); aborting.")
            return None

    return None


def usage() -> None:
    print(__doc__)
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="brute_force_baseline.py",
        description="Reference brute-force solver for Ladhe challenges.",
    )
    parser.add_argument("manifest_or_raw",
                        help="path to manifest.json, or '--raw'")
    parser.add_argument("challenge_id_or_P",
                        help="challenge id (manifest mode) or P "
                             "(raw mode)")
    parser.add_argument("h_hex", nargs="?",
                        help="h as hex (raw mode only)")
    parser.add_argument("--max-time", type=float, default=None,
                        help="maximum seconds to spend before giving up")
    args = parser.parse_args()

    if args.manifest_or_raw == "--raw":
        try:
            P = int(args.challenge_id_or_P)
        except ValueError:
            print(f"could not parse P = {args.challenge_id_or_P}")
            sys.exit(2)
        if args.h_hex is None:
            usage()
        h_hex = args.h_hex
    else:
        manifest_path = Path(args.manifest_or_raw)
        if not manifest_path.exists():
            print(f"Manifest not found: {manifest_path}")
            sys.exit(2)
        with open(manifest_path) as f:
            manifest = json.load(f)

        challenge_id = args.challenge_id_or_P
        challenge = next(
            (c for c in manifest["challenges"]
             if c["id"] == challenge_id),
            None,
        )
        if challenge is None:
            ids = ", ".join(c["id"] for c in manifest["challenges"])
            print(f"Challenge id {challenge_id!r} not in manifest.")
            print(f"Available: {ids}")
            sys.exit(2)
        P = int(challenge["P"])
        h_hex = challenge["h_hex"]

        if challenge["bits"] >= 96:
            print(f"⚠️  This is a {challenge['tier']} challenge.")
            print(f"    Brute force at bits={challenge['bits']} is "
                  f"likely impractical with this baseline solver.")
            print(f"    Use --max-time to bound runtime.\n")

    result = solve(P, h_hex, args.max_time)
    if result is None:
        print("\nNo witness found within bounds.")
        if args.max_time:
            sys.exit(3)
        sys.exit(1)


if __name__ == "__main__":
    main()
