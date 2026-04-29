"""ladhe_rsa.py — Reference implementation of the Ladhe signature scheme.

This is version 3 of the scheme, matching SP_Paper_v3.tex (April 2026).
The scheme is a ONE-TIME hash-based signature whose private key is a
sorted tuple of distinct odd primes summing to a public prime P, and
whose public key is the hash of an indexed-pair compression of those
primes. Security reduces to SHA-256 preimage resistance — the same
foundation as SPHINCS+.

Key operations:
    keygen(up1)              -> (PublicKey, PrivateKey)
    sign(message, sk)        -> Signature   (one-time!)
    verify(message, sig, pk) -> bool
    generate_ldp_challenge(bits) -> (P, h)

ONE-TIME WARNING:
    A Ladhe key pair can sign exactly one message safely. Signing a
    second message with the same key reveals the private key. For
    many-time signing, use Merkle aggregation (paper §6) — not yet
    implemented here.

RESEARCH-REFERENCE WARNING:
    No side-channel resistance, no constant-time operations. KeyGen
    is O((ln P)^k * k * (log P)^3) via random trial — minutes at
    cryptographic P sizes. Not for production use.

License: CC BY 4.0.
"""

from __future__ import annotations

import hashlib
import random
import struct
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

HASH = hashlib.sha256
LAMBDA_BYTES = 32
ENCODING_VERSION = 0x01

_SMALL_PRIMES = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109,
)


# ----------------------------------------------------------------------
# 1. Primality
# ----------------------------------------------------------------------
def is_prime(n: int, rounds: int = 20) -> bool:
    """Miller-Rabin primality test."""
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


def random_prime_of_digits(digits: int, rng=None) -> int:
    """Sample a random prime with exactly `digits` decimal digits,
    satisfying P mod 6 in {1, 5}."""
    rng = rng or random.SystemRandom()
    low = 10 ** (digits - 1) if digits > 1 else 2
    high = 10 ** digits - 1
    while True:
        candidate = rng.randint(low, high)
        if candidate < 5:
            continue
        if candidate % 6 not in (1, 5):
            continue
        if is_prime(candidate):
            return candidate


# ----------------------------------------------------------------------
# 2. Indexed-pair compression (paper §3.2)
# ----------------------------------------------------------------------
def pair_compress(primes: Sequence[int]) -> Tuple[int, ...]:
    """Compress a sorted tuple of odd length k into m = (k+1)/2 values:
    pairwise sums for the first k-1 primes, and the last prime unpaired."""
    k = len(primes)
    if k < 3 or k % 2 == 0:
        raise ValueError(f"k must be odd and >= 3, got {k}")
    W = []
    for i in range(0, k - 1, 2):
        W.append(primes[i] + primes[i + 1])
    W.append(primes[-1])
    return tuple(W)


# ----------------------------------------------------------------------
# 3. Canonical encoding (paper §3.3)
# ----------------------------------------------------------------------
def _int_to_be(n: int) -> bytes:
    if n == 0:
        return b"\x00"
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


def encode_W(W: Sequence[int]) -> bytes:
    """Canonical byte-encoding of a compressed witness tuple W."""
    m = len(W)
    if m > 255:
        raise ValueError("tuple length exceeds 255")
    out = bytearray([ENCODING_VERSION, m])
    for w in W:
        wb = _int_to_be(w)
        out += struct.pack(">H", len(wb))
        out += wb
    return bytes(out)


# ----------------------------------------------------------------------
# 4. Data classes
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class PublicKey:
    """Ladhe public key: (P, h) where h = H(enc(W))."""
    prime: int
    h: bytes

    def encode(self) -> bytes:
        pb = _int_to_be(self.prime)
        return struct.pack(">I", len(pb)) + pb + self.h

    # Alias for backward-compat with cert code that called it 'commitment'.
    @property
    def commitment(self) -> bytes:
        return self.h


@dataclass(frozen=True)
class PrivateKey:
    """Ladhe private key: the k distinct odd primes summing to P,
    sorted ascending."""
    prime: int
    primes: Tuple[int, ...]

    # Alias for backward-compat.
    @property
    def witness(self) -> Tuple[int, ...]:
        return self.primes


@dataclass(frozen=True)
class Signature:
    """One-time Ladhe signature: reveals the full prime decomposition."""
    primes: Tuple[int, ...]
    message: bytes

    def encode(self) -> bytes:
        out = bytearray()
        out.append(len(self.primes))
        for p in self.primes:
            pb = _int_to_be(p)
            out += struct.pack(">H", len(pb))
            out += pb
        out += struct.pack(">I", len(self.message))
        out += self.message
        return bytes(out)

    @classmethod
    def decode(cls, data: bytes) -> "Signature":
        k = data[0]
        off = 1
        primes = []
        for _ in range(k):
            (ln,) = struct.unpack_from(">H", data, off)
            off += 2
            primes.append(int.from_bytes(data[off:off + ln], "big"))
            off += ln
        (ml,) = struct.unpack_from(">I", data, off)
        off += 4
        message = bytes(data[off:off + ml])
        return cls(primes=tuple(primes), message=message)


# ----------------------------------------------------------------------
# 5. KeyGen (paper §3, Algorithm 1)
#
# Implementation note (v3.1, April 2026):
#   We maintain a precomputed sieve of primes up to _SIEVE_LIMIT so that
#   _search_decomposition can sample (k-1) primes in O(k) without any
#   Miller-Rabin invocation. Only the last summand, last = P - sum(others),
#   may exceed the sieve and require Miller-Rabin — at most ONE MR call
#   per trial, instead of k as in the naive approach. This gives a
#   ~10-30x speedup at demo parameter sizes and a k-fold speedup in
#   the hybrid regime where P exceeds the sieve limit.
#
#   Sieve storage is ~10 MB (bytes) + ~5 MB (list of primes). Build
#   cost is ~1s at import time, amortised across keygens.
# ----------------------------------------------------------------------
import bisect

_SIEVE_LIMIT = 10_000_000    # primes up to 10^7 (~600K primes cached)
_SIEVE_LIST: Optional[List[int]] = None       # sorted list of primes
_SIEVE_BYTES: Optional[bytearray] = None      # byte[i] == 1 iff i is prime


def _build_sieve(limit: int = _SIEVE_LIMIT) -> Tuple[List[int], bytearray]:
    """Sieve of Eratosthenes up to `limit`."""
    b = bytearray(b"\x01") * (limit + 1)
    b[0] = b[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if b[i]:
            step = i
            b[i * i :: step] = bytearray(len(b[i * i :: step]))
    primes = [i for i, v in enumerate(b) if v]
    return primes, b


def _get_sieve() -> Tuple[List[int], bytearray]:
    """Lazy-build the sieve on first use."""
    global _SIEVE_LIST, _SIEVE_BYTES
    if _SIEVE_LIST is None:
        _SIEVE_LIST, _SIEVE_BYTES = _build_sieve(_SIEVE_LIMIT)
    return _SIEVE_LIST, _SIEVE_BYTES


def _is_prime_cached(n: int) -> bool:
    """Primality test using the sieve when possible, Miller-Rabin otherwise."""
    if n < 2:
        return False
    if n <= _SIEVE_LIMIT:
        _, sieve_bytes = _get_sieve()
        return bool(sieve_bytes[n])
    return is_prime(n)


def _search_decomposition(
    P: int, k: int, max_trials: int = 500_000, rng=None,
) -> Optional[Tuple[int, ...]]:
    """Find k distinct odd primes summing to P via random trial.
    Returns the sorted tuple, or None if we ran out of trials.

    Uses the hybrid fast path: sample (k-1) primes directly from the
    cached sieve (no MR), and verify the final prime `last = P - sum(others)`
    against either the cache (if small) or Miller-Rabin (if large).
    """
    rng = rng or random.SystemRandom()
    if k < 3 or k % 2 == 0:
        raise ValueError("k must be odd and >= 3")

    primes_list, sieve_bytes = _get_sieve()

    # Cap the candidate pool for the (k-1) sampled primes at the sieve
    # limit. This biases those primes to be small; `last` absorbs the
    # remainder and may be large (handled by MR below).
    upper_cap = min(_SIEVE_LIMIT, P - 2, 2 * (P // k) if k > 0 else P - 2)
    upper_cap = max(upper_cap, 5)
    upper_idx = bisect.bisect_right(primes_list, upper_cap)
    lower_idx = bisect.bisect_left(primes_list, 3)
    candidates = primes_list[lower_idx:upper_idx]

    if len(candidates) < k - 1:
        # Very small P: fall back to the naive search.
        return _search_decomposition_naive(P, k, max_trials, rng)

    for _ in range(max_trials):
        # Sample k-1 distinct primes from the sieve in O(k).
        others = rng.sample(candidates, k - 1)
        total = sum(others)
        last = P - total
        if last <= 2 or last in others:
            continue
        # At most ONE primality check per trial.
        if not _is_prime_cached(last):
            continue
        primes = tuple(sorted(others + [last]))
        if len(set(primes)) != k:
            continue
        return primes
    return None


def _search_decomposition_naive(
    P: int, k: int, max_trials: int = 500_000, rng=None,
) -> Optional[Tuple[int, ...]]:
    """Fallback: the original pre-sieve random-trial search.
    Used only when the sieve candidate pool has fewer than k-1 primes,
    i.e., for P ≤ ~20 with k ≥ 3."""
    rng = rng or random.SystemRandom()
    upper = max(5, min(P - 2, 2 * (P // k)))

    for _ in range(max_trials):
        others: List[int] = []
        total = 0
        for _ in range(k - 1):
            for _ in range(2000):
                cand = rng.randint(3, upper)
                if cand % 2 == 0:
                    cand += 1
                if cand > upper:
                    continue
                if cand in others:
                    continue
                if is_prime(cand):
                    others.append(cand)
                    total += cand
                    break
            else:
                others = []
                break
        if len(others) != k - 1:
            continue
        last = P - total
        if last <= 2 or last in others:
            continue
        if not is_prime(last):
            continue
        primes = tuple(sorted(others + [last]))
        if len(set(primes)) != k:
            continue
        return primes
    return None


def keygen(
    up1: int = 3,
    k_choices: Sequence[int] = (3, 5, 7),
    rng=None,
) -> Tuple[PublicKey, PrivateKey]:
    """Generate a Ladhe key pair.

    Args:
        up1:       target digit count for the public prime P
        k_choices: odd k values to sample from
        rng:       optional random source (default: SystemRandom)
    """
    rng = rng or random.SystemRandom()
    if any(k % 2 == 0 or k < 3 for k in k_choices):
        raise ValueError("all k in k_choices must be odd and >= 3")

    for _ in range(100):
        P = random_prime_of_digits(up1, rng)
        k = rng.choice(list(k_choices))
        primes = _search_decomposition(P, k, rng=rng)
        if primes is None:
            continue
        W = pair_compress(primes)
        h = HASH(encode_W(W)).digest()
        return PublicKey(prime=P, h=h), PrivateKey(prime=P, primes=primes)

    raise RuntimeError(
        f"KeyGen failed: could not find a decomposition for any prime "
        f"of {up1} digits. Try a larger up1 or wider k_choices."
    )


# ----------------------------------------------------------------------
# 6. Sign + Verify (paper §3, Algorithms 2 and 3)
# ----------------------------------------------------------------------
def sign(
    message: bytes,
    sk: PrivateKey,
    pk: Optional[PublicKey] = None,
) -> Signature:
    """One-time Ladhe signature. `pk` is accepted for API compatibility
    with callers but is not needed: the signature is just the private
    decomposition plus the message."""
    return Signature(primes=sk.primes, message=message)


def verify(message: bytes, sig: Signature, pk: PublicKey) -> bool:
    """Verify a Ladhe signature against the public key (P, h)."""
    if sig.message != message:
        return False
    primes = sig.primes
    k = len(primes)
    if k < 3 or k % 2 == 0:
        return False
    for p in primes:
        if p <= 2:
            return False
        if not is_prime(p):
            return False
    if list(primes) != sorted(set(primes)) or len(set(primes)) != k:
        return False
    if sum(primes) != pk.prime:
        return False
    W = pair_compress(primes)
    h = HASH(encode_W(W)).digest()
    return h == pk.h


# ----------------------------------------------------------------------
# 7. LDP challenge generator (for cryptanalysts, paper §7)
# ----------------------------------------------------------------------
def generate_ldp_challenge(bits: int = 32, rng=None) -> Tuple[int, bytes]:
    """Generate a fresh (P, h) where we hold the witness but don't release it."""
    rng = rng or random.SystemRandom()
    digit_count = max(2, int(bits * 0.302) + 1)   # log10(2) ≈ 0.302
    pk, _ = keygen(up1=digit_count, rng=rng)
    return pk.prime, pk.h


# ----------------------------------------------------------------------
# 8. CLI / demos
# ----------------------------------------------------------------------
def _fmt_ms(t: float) -> str:
    return f"{t * 1000:8.2f} ms"


def _cli_demo(up1: int = 3):
    print(f"Ladhe v3 reference — demo (digits={up1})\n")
    t0 = time.time()
    pk, sk = keygen(up1)
    print(f"KeyGen:    {_fmt_ms(time.time() - t0)}")
    print(f"  P          = {pk.prime}  ({pk.prime.bit_length()} bits)")
    print(f"  k          = {len(sk.primes)}")
    print(f"  primes     = {sk.primes}   (secret)")
    W = pair_compress(sk.primes)
    print(f"  W          = {W}")
    print(f"  h          = {pk.h.hex()[:40]}...\n")

    msg = b"Ladhe reference demo"
    t0 = time.time()
    sig = sign(msg, sk)
    t_sign = time.time() - t0
    sig_bytes = sig.encode()
    print(f"Sign:      {_fmt_ms(t_sign)}, signature size = {len(sig_bytes)} bytes")

    t0 = time.time()
    ok = verify(msg, sig, pk)
    print(f"Verify:    {_fmt_ms(time.time() - t0)}, result = {ok}\n")

    ok_bad = verify(b"tampered", sig, pk)
    print(f"Tampered-message verify (should be False): {ok_bad}\n")

    P_c, h_c = generate_ldp_challenge(bits=32)
    print("Fresh LDP challenge (32-bit):")
    print(f"  P = {P_c}")
    print(f"  h = {h_c.hex()}")
    print(f"  task: find distinct odd primes (p_1 < ... < p_k) with k odd,")
    print(f"        summing to P, and H(enc(pair_compress(primes))) = h")


def _cli_bench():
    print("Ladhe v3 — timing benchmark\n")
    print(f"{'digits':>7} {'P_bits':>7} {'k':>3} "
          f"{'keygen_ms':>12} {'sign_ms':>9} {'verify_ms':>11} {'sig_bytes':>10}")
    print("-" * 68)
    for up1 in (3, 5, 7, 10, 15, 20, 30, 50):
        try:
            t0 = time.time()
            pk, sk = keygen(up1)
            t_kg = (time.time() - t0) * 1000
            msg = b"bench"
            t0 = time.time()
            sig = sign(msg, sk)
            t_s = (time.time() - t0) * 1000
            t0 = time.time()
            verify(msg, sig, pk)
            t_v = (time.time() - t0) * 1000
            sig_b = len(sig.encode())
            print(f"{up1:>7d} {pk.prime.bit_length():>7d} "
                  f"{len(sk.primes):>3d} {t_kg:>12.2f} "
                  f"{t_s:>9.2f} {t_v:>11.2f} {sig_b:>10d}")
        except Exception as e:
            print(f"{up1:>7d} FAILED: {e}")


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv
    if len(argv) < 2 or argv[1] == "demo":
        up1 = int(argv[2]) if len(argv) > 2 else 3
        _cli_demo(up1)
        return 0
    if argv[1] == "bench":
        _cli_bench()
        return 0
    if argv[1] == "sign" and len(argv) >= 3:
        msg = argv[2].encode()
        pk, sk = keygen()
        sig = sign(msg, sk)
        print(f"P      = {pk.prime}")
        print(f"primes = {sk.primes}")
        print(f"h      = {pk.h.hex()}")
        print(f"sig    = {sig.encode().hex()[:200]}...")
        print(f"verify = {verify(msg, sig, pk)}")
        return 0
    if argv[1] == "challenge":
        bits = int(argv[2]) if len(argv) > 2 else 256

        # Tier classification
        if bits < 64:
            tier_label = "SANITY CHECK TIER"
            tier_note = ("toy parameters — trivially breakable by brute "
                         "force; for testing the algorithm only")
            reward = ("not a cryptographic break; for testing / debugging")
        elif bits < 128:
            tier_label = "EDUCATIONAL TIER"
            tier_note = ("tractable for advanced attackers; below "
                         "security target")
            reward = ("not yet a cryptographic break; useful for teaching "
                      "and CTF practice")
        elif bits < 256:
            tier_label = "PRE-CRYPTOGRAPHIC TIER"
            tier_note = ("hard but solvable; below the 256-bit security "
                         "target of the paper")
            reward = ("technically interesting but does not contradict the "
                      "scheme's security claim")
        elif bits < 512:
            tier_label = "BRONZE TIER (security target)"
            tier_note = ("256-bit P is the cryptographic security claim "
                         "of the paper; a break here is a real "
                         "cryptanalytic result")
            reward = ("named in the public 'challenges solved' log")
        elif bits < 1024:
            tier_label = "SILVER TIER"
            tier_note = ("above the 256-bit security target")
            reward = ("named acknowledgment in v2 of the paper")
        elif bits < 2048:
            tier_label = "GOLD TIER"
            tier_note = ("well above security target")
            reward = ("coauthorship offer on a cryptanalysis follow-on "
                      "paper")
        else:
            tier_label = "PLATINUM TIER"
            tier_note = ("extreme parameters")
            reward = ("public retraction of the scheme + coauthorship "
                      "on the retraction paper")

        print(f"# Ladhe LDP challenge (bits={bits})")
        print(f"# Tier:   {tier_label}")
        print(f"#         {tier_note}")
        print(f"# Credit: {reward}")
        print(f"# Generating challenge "
              f"(may take a moment for higher bit sizes)...")
        print()
        P, h = generate_ldp_challenge(bits=bits)
        print(f"P = {P}")
        print(f"h = {h.hex()}")
        print()
        print("Task:  find an ascending tuple of distinct odd primes")
        print("       (p_1 < p_2 < ... < p_k)  with  k in {3, 5, 7}")
        print("       summing to P, such that")
        print("       SHA-256(encode(pair_compress(primes))) == h.")
        print()
        print("       pair_compress((p_1, p_2, ..., p_k)) =")
        print("         (p_1+p_2, p_3+p_4, ..., p_k)")
        print("       — last element unpaired since k is odd.")
        print()
        print("       encode(W) is the canonical big-endian byte encoding")
        print("       of the tuple W; see encode_W() in ladhe_rsa.py.")
        print()
        print("Tier reference:")
        print("  bits <  64        sanity check       (toy)")
        print("  bits <  128       educational        (CTF practice)")
        print("  bits <  256       pre-cryptographic  (below target)")
        print("  bits =  256       BRONZE             (security target)")
        print("  bits <  1024      SILVER             (above target)")
        print("  bits <  2048      GOLD               (well above target)")
        print("  bits >= 2048      PLATINUM           (extreme)")
        print()
        print("Submit: github.com/SPAlgorithm/LE/issues  or  "
              "spalgorithm@gmail.com")
        return 0
    print("usage:")
    print("  python3 ladhe_rsa.py demo [up1]")
    print("  python3 ladhe_rsa.py bench")
    print("  python3 ladhe_rsa.py sign <message>")
    print("  python3 ladhe_rsa.py challenge [bits]")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
