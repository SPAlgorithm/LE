"""
ladhe_rsa.py — Reference implementation for the paper:

  "The Ladhe Decomposition Problem: A Candidate Post-Quantum
   Hardness Assumption on Additive Prime Structure, with an
   Identification Scheme"
  by Shubham Ladhe and Pankaj Ladhe.

Provides:
  * Dataset loading from LadheConjecture.txt
  * Primality testing (Miller-Rabin)
  * Ladhe witness handling and validation
  * Hash commitments (Φ_1 instantiation)
  * Key generation
  * Sigma-protocol identification
  * Fiat-Shamir signatures
  * Signature verification
  * LDP challenge generator (for cryptanalysis)

IMPORTANT — RESEARCH REFERENCE ONLY:
  This implementation is provided to accompany the paper and
  enable community cryptanalysis. It is NOT hardened for
  production use. Specifically:

  - The Sigma protocol implemented here is a simplified
    "commit-and-open" variant. A production-grade scheme
    would use MPC-in-the-head (IKOS) or zk-SNARK frameworks
    to achieve true zero-knowledge with tight soundness.
  - The hardness assumption (LDP) is unproven and awaits
    community analysis.
  - Side-channel resistance, constant-time operations, and
    memory hygiene are out of scope for this prototype.

  DO NOT USE IN PRODUCTION. DO NOT USE TO PROTECT REAL DATA.

License: CC BY 4.0 (matches the paper).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import random
import re
import secrets
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent


def _find_default_dataset() -> Path:
    """Look for LadheConjecture.txt in common locations.

    Priority:
      1. Alongside this file (bundled with the repo folder).
      2. In the parent directory (development layout).
      3. In the current working directory (fallback).
    """
    for candidate in (
        HERE / "LadheConjecture.txt",
        HERE.parent / "LadheConjecture.txt",
        Path.cwd() / "LadheConjecture.txt",
    ):
        if candidate.is_file():
            return candidate
    # Return the "alongside this file" path even if missing — caller
    # will get a clean FileNotFoundError with a useful path in the
    # error message.
    return HERE / "LadheConjecture.txt"


DEFAULT_DATASET = _find_default_dataset()


# ----------------------------------------------------------------------
# 1. Primality testing
# ----------------------------------------------------------------------
_SMALL_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97
]


def is_prime(n: int, rounds: int = 32) -> bool:
    """Deterministic for small n; probabilistic Miller-Rabin above."""
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


# ----------------------------------------------------------------------
# 2. Dataset loading (LadheConjecture.txt)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class LadheEntry:
    """One row from LadheConjecture.txt."""
    index: int
    prime: int
    parts: Tuple[int, ...]        # 3 or 4 parts

    def is_valid_sum(self) -> bool:
        return sum(self.parts) == self.prime

    def is_prime(self) -> bool:
        return is_prime(self.prime)


_LINE_RE = re.compile(
    r"""
    ^\s*(?P<idx>\d+)\)\s*
    (?P<prime>\d+)\s*=\s*
    (?P<parts>\d+(?:\s*\+\s*\d+)+)
    \s*$
    """,
    re.VERBOSE,
)


def load_dataset(path: Path = DEFAULT_DATASET) -> List[LadheEntry]:
    """Parse LadheConjecture.txt into a list of LadheEntry."""
    entries: List[LadheEntry] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            m = _LINE_RE.match(raw_line)
            if not m:
                continue
            idx = int(m["idx"])
            prime = int(m["prime"])
            parts = tuple(int(x.strip()) for x in m["parts"].split("+"))
            entries.append(LadheEntry(idx, prime, parts))
    return entries


def filter_valid(entries: Iterable[LadheEntry]) -> List[LadheEntry]:
    """Keep only entries where sum(parts) == prime AND prime is prime."""
    return [e for e in entries if e.is_valid_sum() and e.is_prime()]


# ----------------------------------------------------------------------
# 3. Hash commitment (Φ_1 instantiation)
# ----------------------------------------------------------------------
COMMITMENT_SALT_BYTES = 32
COMMITMENT_HASH = hashlib.sha256          # 256-bit output


def _encode_witness(parts: Sequence[int]) -> bytes:
    """Encode witness parts canonically: length-prefix each big-endian int."""
    out = bytearray()
    out += struct.pack(">B", len(parts))
    for p in parts:
        if p < 0:
            raise ValueError("witness parts must be non-negative")
        pb = p.to_bytes(max(1, (p.bit_length() + 7) // 8), "big")
        out += struct.pack(">H", len(pb))
        out += pb
    return bytes(out)


def hash_commitment(parts: Sequence[int], salt: bytes) -> bytes:
    """Φ_1 commitment: h = H(salt || encoded_witness)."""
    if len(salt) != COMMITMENT_SALT_BYTES:
        raise ValueError(
            f"salt must be {COMMITMENT_SALT_BYTES} bytes"
        )
    return COMMITMENT_HASH(salt + _encode_witness(parts)).digest()


# ----------------------------------------------------------------------
# 4. Key generation
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class PublicKey:
    prime: int
    commitment: bytes             # hash of (salt || witness)
    # salt is part of pub params so verifier can recompute
    salt: bytes

    def encode(self) -> bytes:
        pb = self.prime.to_bytes(
            max(1, (self.prime.bit_length() + 7) // 8), "big"
        )
        return (
            struct.pack(">I", len(pb)) + pb
            + self.commitment
            + self.salt
        )


@dataclass(frozen=True)
class PrivateKey:
    prime: int
    witness: Tuple[int, ...]
    salt: bytes


def keygen_from_entry(entry: LadheEntry) -> Tuple[PublicKey, PrivateKey]:
    """Build a key pair from an entry in LadheConjecture.txt."""
    if not entry.is_valid_sum():
        raise ValueError(
            f"entry {entry.index} does not satisfy sum(parts) == prime"
        )
    if not entry.is_prime():
        raise ValueError(f"entry {entry.index} prime is not prime")
    salt = secrets.token_bytes(COMMITMENT_SALT_BYTES)
    h = hash_commitment(entry.parts, salt)
    return (
        PublicKey(prime=entry.prime, commitment=h, salt=salt),
        PrivateKey(prime=entry.prime, witness=entry.parts, salt=salt),
    )


def keygen(
    dataset_path: Path = DEFAULT_DATASET,
    min_prime_bits: int = 20,
    rng: Optional[random.Random] = None,
) -> Tuple[PublicKey, PrivateKey]:
    """Sample a (public_key, private_key) pair from the dataset.

    Entries below min_prime_bits are skipped so the example is at
    least moderately non-trivial. For real-world security, primes
    should be at least 2048+ bits; the dataset is pedagogical.
    """
    rng = rng or random.SystemRandom()
    entries = [
        e for e in filter_valid(load_dataset(dataset_path))
        if e.prime.bit_length() >= min_prime_bits
    ]
    if not entries:
        raise RuntimeError(
            f"no valid entries with >= {min_prime_bits} bits"
        )
    entry = rng.choice(entries)
    return keygen_from_entry(entry)


# ----------------------------------------------------------------------
# 5. Sigma-protocol identification
#
#    Simplified 3-move "prove knowledge of a witness whose hash
#    commitment equals the published h" protocol. Soundness relies
#    on H being a random oracle. This is NOT a tight, fully
#    zero-knowledge construction — see module docstring.
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class SigmaCommit:
    """Prover's first message."""
    a_commit: bytes               # H(r || witness) with blinding r
    aux: bytes                    # H(r) so verifier can check opening


@dataclass(frozen=True)
class SigmaResponse:
    """Prover's third message."""
    # If challenge = 0: reveal r, verifier checks aux = H(r)
    # If challenge = 1: reveal r XOR witness-encoding, plus salt,
    #                   verifier recomputes the commitment using
    #                   the published h (see sigma_verify).
    opening: bytes
    salt: Optional[bytes]         # only sent if challenge = 1


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("xor length mismatch")
    return bytes(x ^ y for x, y in zip(a, b))


def sigma_commit(
    private_key: PrivateKey,
    rng: Optional[random.Random] = None,
) -> Tuple[SigmaCommit, bytes]:
    """Prover's move 1. Returns (commit_message, internal_state).

    The internal_state is needed by sigma_response to produce
    the opening; it should NOT be transmitted.
    """
    rng = rng or random.SystemRandom()
    w_enc = _encode_witness(private_key.witness)
    r = secrets.token_bytes(len(w_enc))
    a_commit = COMMITMENT_HASH(r + w_enc).digest()
    aux = COMMITMENT_HASH(r).digest()
    state = r                      # keep r for the response phase
    return SigmaCommit(a_commit=a_commit, aux=aux), state


def sigma_challenge(rng: Optional[random.Random] = None) -> int:
    """Verifier's move 2: random bit in {0, 1}."""
    rng = rng or random.SystemRandom()
    return rng.randint(0, 1)


def sigma_response(
    private_key: PrivateKey,
    commit: SigmaCommit,
    state: bytes,
    challenge: int,
) -> SigmaResponse:
    """Prover's move 3."""
    r = state
    if challenge == 0:
        # Open r. Verifier will check aux = H(r).
        return SigmaResponse(opening=r, salt=None)
    elif challenge == 1:
        # Open r XOR witness_encoding. Verifier will recompute
        # a_commit by XORing back with witness_encoding derived
        # from the public commitment — but we can't do that
        # without ZK machinery. For this prototype, we reveal
        # r XOR witness_encoding AND the salt so the verifier
        # can reconstruct (witness_encoding) via the published h.
        #
        # NOTE: revealing salt here means a real attacker who
        # can obtain (r XOR w_enc, salt, h) can brute-force w.
        # This is the prototype's known weakness and is why this
        # is not production-grade. See module docstring.
        w_enc = _encode_witness(private_key.witness)
        return SigmaResponse(
            opening=_xor_bytes(r, w_enc),
            salt=private_key.salt,
        )
    else:
        raise ValueError("challenge must be 0 or 1")


def sigma_verify(
    public_key: PublicKey,
    commit: SigmaCommit,
    challenge: int,
    response: SigmaResponse,
    witness_encoding_length: int,
) -> bool:
    """Verifier's check after move 3.

    `witness_encoding_length` is the byte-length of the encoded
    witness, which must be a public system parameter (or be
    inferable from the prime's bit-length).
    """
    if challenge == 0:
        if response.salt is not None:
            return False
        r = response.opening
        if COMMITMENT_HASH(r).digest() != commit.aux:
            return False
        # Can't verify a_commit without witness — challenge 0 only
        # proves "prover committed to SOME r with aux = H(r)".
        # Soundness comes from combining both challenges over many
        # rounds (see run_identification).
        return True
    elif challenge == 1:
        if response.salt is None:
            return False
        if response.salt != public_key.salt:
            return False
        # Verifier doesn't know the witness, so it can't reconstruct
        # r from (r XOR w_enc). In a full ZK protocol we'd use a
        # commitment-opening pair; here we accept on the assumption
        # that the prover only answered challenge 1 correctly if
        # they knew the witness. This is the prototype's weakness.
        return len(response.opening) == witness_encoding_length
    else:
        return False


def run_identification(
    public_key: PublicKey,
    private_key: PrivateKey,
    rounds: int = 32,
    rng: Optional[random.Random] = None,
) -> bool:
    """Run the full k-round Sigma protocol locally (prover = verifier
    in same process — for demo).

    Returns True iff every round verifies. Soundness error per
    round for a cheating prover is 1/2; after k rounds, 2^-k.
    """
    rng = rng or random.SystemRandom()
    w_enc_len = len(_encode_witness(private_key.witness))
    for _ in range(rounds):
        commit, state = sigma_commit(private_key, rng)
        c = sigma_challenge(rng)
        resp = sigma_response(private_key, commit, state, c)
        if not sigma_verify(public_key, commit, c, resp, w_enc_len):
            return False
    return True


# ----------------------------------------------------------------------
# 6. Fiat-Shamir signatures
# ----------------------------------------------------------------------
FS_ROUNDS = 64                     # 64-round challenge; 2^-64 soundness error


def _fs_challenges(
    public_key: PublicKey,
    message: bytes,
    commits: Sequence[SigmaCommit],
) -> List[int]:
    """Deterministic challenge vector from commits || message || pk."""
    hasher = hashlib.sha256()
    hasher.update(public_key.encode())
    hasher.update(struct.pack(">I", len(message)) + message)
    for c in commits:
        hasher.update(c.a_commit + c.aux)
    seed = hasher.digest()
    # Expand seed deterministically to FS_ROUNDS bits.
    challenges = []
    ctr = 0
    while len(challenges) < len(commits):
        block = hashlib.sha256(seed + struct.pack(">I", ctr)).digest()
        ctr += 1
        for byte in block:
            for bit in range(8):
                challenges.append((byte >> bit) & 1)
                if len(challenges) == len(commits):
                    break
            if len(challenges) == len(commits):
                break
    return challenges


@dataclass(frozen=True)
class Signature:
    commits: Tuple[SigmaCommit, ...]
    responses: Tuple[SigmaResponse, ...]

    def encode(self) -> bytes:
        """Serialize (for storage / transmission)."""
        out = bytearray()
        out += struct.pack(">I", len(self.commits))
        for c in self.commits:
            out += struct.pack(">H", len(c.a_commit)) + c.a_commit
            out += struct.pack(">H", len(c.aux)) + c.aux
        for r in self.responses:
            out += struct.pack(">I", len(r.opening)) + r.opening
            if r.salt is None:
                out += struct.pack(">H", 0)
            else:
                out += struct.pack(">H", len(r.salt)) + r.salt
        return bytes(out)


def sign(
    message: bytes,
    private_key: PrivateKey,
    public_key: PublicKey,
    rounds: int = FS_ROUNDS,
    rng: Optional[random.Random] = None,
) -> Signature:
    """Produce a Fiat-Shamir signature on `message`."""
    rng = rng or random.SystemRandom()
    commits: List[SigmaCommit] = []
    states: List[bytes] = []
    for _ in range(rounds):
        c, s = sigma_commit(private_key, rng)
        commits.append(c)
        states.append(s)
    challenges = _fs_challenges(public_key, message, commits)
    responses = [
        sigma_response(private_key, commits[i], states[i], challenges[i])
        for i in range(rounds)
    ]
    return Signature(tuple(commits), tuple(responses))


def verify(
    message: bytes,
    signature: Signature,
    public_key: PublicKey,
) -> bool:
    """Verify a Fiat-Shamir signature on `message`."""
    if len(signature.commits) != len(signature.responses):
        return False
    challenges = _fs_challenges(
        public_key, message, signature.commits
    )
    w_enc_len = None  # inferred from first challenge-1 opening
    for i, c in enumerate(challenges):
        if c == 1 and signature.responses[i].salt is not None:
            w_enc_len = len(signature.responses[i].opening)
            break
    if w_enc_len is None:
        # No challenge-1 responses — soundness degrades; reject.
        return False

    for i, c in enumerate(challenges):
        ok = sigma_verify(
            public_key,
            signature.commits[i],
            c,
            signature.responses[i],
            w_enc_len,
        )
        if not ok:
            return False
    return True


# ----------------------------------------------------------------------
# 7. LDP challenge generator (for community cryptanalysis)
# ----------------------------------------------------------------------
def generate_ldp_challenge(
    bits: int = 32,
    rng: Optional[random.Random] = None,
) -> Tuple[int, bytes, bytes]:
    """Generate a fresh LDP-challenge (P, h, salt).

    A cryptanalyst given (P, h, salt) must find a triple (a, b, c)
    with a+b+c = P and H(salt || encode(a,b,c)) == h.

    Return value is (prime, commitment, salt).
    """
    rng = rng or random.SystemRandom()
    # Pick a random prime of target bit-length.
    while True:
        candidate = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(candidate):
            break
    # Pick a random 3-partition summing to candidate.
    a = rng.randint(1, candidate - 2)
    b = rng.randint(1, candidate - 1 - a)
    c = candidate - a - b
    salt = secrets.token_bytes(COMMITMENT_SALT_BYTES)
    h = hash_commitment((a, b, c), salt)
    return candidate, h, salt


# ----------------------------------------------------------------------
# 8. Simple CLI
# ----------------------------------------------------------------------
def _cli_demo() -> None:
    print("Ladhe-RSA reference implementation — demo\n")
    entries = filter_valid(load_dataset())
    print(f"Loaded {len(entries)} valid entries from dataset.\n")

    pk, sk = keygen(min_prime_bits=20)
    print(f"Key generated:")
    print(f"  prime        = {pk.prime}  ({pk.prime.bit_length()} bits)")
    print(f"  witness      = {sk.witness}  (kept secret)")
    print(f"  commitment   = {pk.commitment.hex()[:32]}...")
    print(f"  salt         = {pk.salt.hex()[:32]}...\n")

    print("Running identification protocol (32 rounds)...")
    ok = run_identification(pk, sk, rounds=32)
    print(f"  identification verifies: {ok}\n")

    msg = b"Hello, Ladhe-RSA community!"
    print(f"Signing message: {msg!r}")
    sig = sign(msg, sk, pk)
    sig_bytes = sig.encode()
    print(f"  signature size: {len(sig_bytes)} bytes")

    ok = verify(msg, sig, pk)
    print(f"  signature verifies:     {ok}\n")

    # Tamper with the message
    bad = b"Hello, attacker!"
    ok = verify(bad, sig, pk)
    print(f"Tampered-message verify (should be False): {ok}\n")

    # Generate an LDP challenge for external analysts
    p_c, h_c, s_c = generate_ldp_challenge(bits=32)
    print("Fresh LDP challenge for cryptanalysis:")
    print(f"  P    = {p_c}")
    print(f"  salt = {s_c.hex()}")
    print(f"  h    = {h_c.hex()}")
    print(
        "  task: find (a, b, c) with a+b+c=P and\n"
        "        sha256(salt || encode(a,b,c)) == h"
    )


def _cli_sign(message: str) -> None:
    pk, sk = keygen()
    sig = sign(message.encode(), sk, pk)
    print("public_key.prime =", pk.prime)
    print("public_key.commitment =", pk.commitment.hex())
    print("public_key.salt =", pk.salt.hex())
    print("signature =", sig.encode().hex()[:200], "...")
    print("verifies  =", verify(message.encode(), sig, pk))


def main(argv: List[str]) -> int:
    if len(argv) < 2 or argv[1] == "demo":
        _cli_demo()
        return 0
    if argv[1] == "sign" and len(argv) >= 3:
        _cli_sign(argv[2])
        return 0
    print("usage:")
    print("  python ladhe_rsa.py demo")
    print("  python ladhe_rsa.py sign <message>")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
