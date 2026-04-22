# Manual testing guide

Hands-on walkthrough for every primitive in `ladhe_rsa.py`. Open a terminal in this folder and follow along.

---

## 1. Run the three scripts as-is

### 1.1 The demo (end-to-end smoke test)

```bash
python3 ladhe_rsa.py demo
```

Expected: loads 1618 dataset entries, generates a key, runs identification (32 rounds → verifies True), signs a message (verifies True), tries tampered message (False), prints an LDP challenge.

### 1.2 The unit tests

```bash
python3 -m unittest test_ladhe_rsa -v
```

Expected: `~15 tests, all OK`. Any `FAIL` or `ERROR` is a real bug.

Run individual tests:

```bash
python3 -m unittest test_ladhe_rsa.TestSignatures -v
python3 -m unittest test_ladhe_rsa.TestSignatures.test_sign_verify_roundtrip -v
```

### 1.3 The code-signing example

```bash
python3 example_code_signing.py
```

Expected: Bob signs, attacker tamper fails, Alice verifies.

### 1.4 Sign an arbitrary message from the CLI

```bash
python3 ladhe_rsa.py sign "hello world"
```

### 1.5 Quick one-liner: keygen + sign + verify + tamper check

The fastest sanity-check after a clone. Copy-paste into your shell:

```bash
python3 -c "
import ladhe_rsa as LR
pk, sk = LR.keygen()
sig = LR.sign(b'hi', sk, pk)
print('verify not ok:', LR.verify(b'hi', sig, pk))
print('tampered:', LR.verify(b'evil', sig, pk))
"
```

Expected output:

```
verify not ok: True
tampered: False
```

Reading the output:

| Line | Value | Meaning |
|---|---|---|
| `verify not ok: True` | `True` | The genuine signature on `b'hi'` verifies — protocol works end-to-end |
| `tampered: False` | `False` | Changing the message to `b'evil'` breaks verification — tamper detection works |

If you see `verify not ok: False` or `tampered: True`, something is broken. File a repo issue with your Python version and the full output.

---

## 2. Interactive testing (REPL)

Start a Python REPL in the folder:

```bash
python3
```

Then paste the sessions below.

---

### 2.1 Primality testing

```python
import ladhe_rsa as LR

LR.is_prime(2)           # True
LR.is_prime(97)          # True
LR.is_prime(100)         # False
LR.is_prime(3467)        # True  (entry 40 in the dataset)
LR.is_prime((1<<127)-1)  # True  (Mersenne prime 2^127 - 1)
LR.is_prime((1<<127))    # False
```

### 2.2 Dataset loading

```python
import ladhe_rsa as LR

entries = LR.load_dataset()
len(entries)                          # 1620 (raw)

valid = LR.filter_valid(entries)
len(valid)                            # 1618 (rows where sum == prime and prime is prime)

# Inspect a specific entry
e = next(e for e in valid if e.prime == 3467)
print(e.index, e.prime, e.parts)      # 40 3467 (360, 501, 2606)
print("sum check:", sum(e.parts) == e.prime)
print("prime check:", LR.is_prime(e.prime))
```

### 2.3 Hash commitment (the Φ₁ primitive)

```python
import ladhe_rsa as LR

salt = b"\x00" * 32                        # fixed salt for demo
h1 = LR.hash_commitment((2, 3, 6), salt)
h2 = LR.hash_commitment((2, 3, 6), salt)
print("deterministic:", h1 == h2)          # True

h3 = LR.hash_commitment((2, 3, 6), b"\x01" * 32)
print("salt-sensitive:", h1 != h3)         # True

# Different witness → different commitment
h4 = LR.hash_commitment((1, 4, 6), salt)
print("witness-sensitive:", h1 != h4)      # True

print("commit hex:", h1.hex())
print("commit bits:", len(h1) * 8)         # 256
```

### 2.4 Key generation

```python
import ladhe_rsa as LR

# Sample a random key from the dataset
pk, sk = LR.keygen(min_prime_bits=20)

print("PRIME        :", pk.prime)
print("PRIME BITS   :", pk.prime.bit_length())
print("WITNESS      :", sk.witness, "  (sum =", sum(sk.witness), ")")
print("COMMITMENT   :", pk.commitment.hex()[:32], "...")
print("SALT         :", pk.salt.hex()[:32], "...")

# Consistency check — the commitment must reproduce from (salt, witness)
recomputed = LR.hash_commitment(sk.witness, sk.salt)
print("commit matches:", recomputed == pk.commitment)   # True

# Use a specific entry
entries = LR.filter_valid(LR.load_dataset())
chosen = next(e for e in entries if e.prime == 3467)
pk2, sk2 = LR.keygen_from_entry(chosen)
print("deterministic prime:", pk2.prime)                # 3467
```

### 2.5 Sigma protocol — one round, step by step

```python
import ladhe_rsa as LR

pk, sk = LR.keygen()

# --- Prover's move 1: commit ---
commit, state = LR.sigma_commit(sk)
print("a_commit:", commit.a_commit.hex()[:32], "...")
print("aux     :", commit.aux.hex()[:32], "...")

# --- Verifier's move 2: challenge bit ---
challenge = 0              # try both 0 and 1
print("challenge:", challenge)

# --- Prover's move 3: response ---
response = LR.sigma_response(sk, commit, state, challenge)
if challenge == 0:
    print("opening (r):", response.opening.hex()[:32], "...")
    print("salt sent:  ", response.salt)       # None for challenge 0
else:
    print("opening (r⊕w):", response.opening.hex()[:32], "...")
    print("salt sent  :", response.salt.hex()[:32], "...")

# --- Verifier's check ---
w_enc_len = len(LR._encode_witness(sk.witness))
ok = LR.sigma_verify(pk, commit, challenge, response, w_enc_len)
print("round verifies:", ok)
```

### 2.6 Full identification protocol (32 rounds)

```python
import ladhe_rsa as LR

pk, sk = LR.keygen()
print("Running 32 rounds...")
ok = LR.run_identification(pk, sk, rounds=32)
print("identification:", ok)
# Soundness error: 2^-32 after 32 rounds — a cheating prover
# without the witness passes with probability < 1 in 4 billion.
```

### 2.7 Fiat-Shamir signatures

```python
import ladhe_rsa as LR

pk, sk = LR.keygen()

# Sign
msg = b"This is a signed message."
sig = LR.sign(msg, sk, pk)

print("Number of commits (=rounds):", len(sig.commits))      # 64
print("Signature encoded size      :", len(sig.encode()), "bytes")

# Verify
print("Valid signature verifies    :", LR.verify(msg, sig, pk))   # True

# Tamper: change the message
print("Tampered message verifies   :", LR.verify(b"evil", sig, pk))  # False

# Tamper: replace signature with random bytes wouldn't even parse,
# but we can corrupt a single commit and see detection:
import copy
bad_commit = LR.SigmaCommit(
    a_commit=b"\x00" * 32,     # wrong
    aux=sig.commits[0].aux,
)
corrupted = LR.Signature(
    commits=(bad_commit,) + sig.commits[1:],
    responses=sig.responses,
)
print("Corrupted sig verifies      :", LR.verify(msg, corrupted, pk))  # False
```

### 2.8 Serialise and deserialise a signature

```python
import ladhe_rsa as LR

pk, sk = LR.keygen()
sig = LR.sign(b"hello", sk, pk)

wire = sig.encode()                     # bytes you'd send over a network
print("on-wire bytes:", len(wire))
print("first 64 hex  :", wire[:32].hex())

# NOTE: this prototype doesn't ship a decoder; for round-trip use
# you'd add a Signature.decode(bytes) -> Signature method.
# As written, keep the Signature object around after signing.
```

### 2.9 Generate an LDP challenge (for cryptanalysis)

```python
import ladhe_rsa as LR

# Generate a fresh challenge at toy size
P, h, salt = LR.generate_ldp_challenge(bits=24)

print("P    (prime):", P)
print("salt        :", salt.hex())
print("h (target)  :", h.hex())
print()
print("Cryptanalyst's task:")
print(f"  Find integers a, b, c > 0 with:")
print(f"    a + b + c = {P}")
print(f"    sha256(salt || canonical_encode(a,b,c)) == {h.hex()[:16]}...")

# Verify your solution with:
def check(a, b, c):
    return a + b + c == P and LR.hash_commitment((a, b, c), salt) == h

# (There IS a solution — the generator chose one — but finding it
# classically requires ~2^24 hash evaluations at bits=24; ~2^256 at
# bits=256.)
```

---

## 3. Break things on purpose (negative tests)

A good way to build intuition is to feed invalid inputs and see what happens.

### 3.1 Invalid witness (doesn't sum to P)

```python
import ladhe_rsa as LR

bogus = LR.LadheEntry(index=999, prime=11, parts=(2, 3, 5))  # sums to 10, not 11
print("valid sum:", bogus.is_valid_sum())   # False

try:
    LR.keygen_from_entry(bogus)
except ValueError as e:
    print("caught:", e)
```

### 3.2 Wrong salt during verification

```python
import ladhe_rsa as LR

pk, sk = LR.keygen()
commit, state = LR.sigma_commit(sk)
resp = LR.sigma_response(sk, commit, state, 1)

# Swap in a wrong salt
bad_resp = LR.SigmaResponse(opening=resp.opening, salt=b"\xff" * 32)
w_enc_len = len(LR._encode_witness(sk.witness))
ok = LR.sigma_verify(pk, commit, 1, bad_resp, w_enc_len)
print("wrong salt verifies:", ok)           # False
```

### 3.3 A cheating prover without the witness

```python
import ladhe_rsa as LR

# Bob's real key
pk, sk = LR.keygen()

# Eve doesn't know the witness. She fabricates one and tries to
# pass identification.
fake_sk = LR.PrivateKey(prime=pk.prime, witness=(1, 2, 3), salt=pk.salt)

print("cheating prover (1 round):")
for trial in range(5):
    ok = LR.run_identification(pk, fake_sk, rounds=1)
    print(f"  trial {trial}: {ok}")

# Over 32 rounds, probability of passing is 2^-32 ≈ 0
print("cheating over 32 rounds:",
      LR.run_identification(pk, fake_sk, rounds=32))
```

Why does challenge-0 sometimes pass for the cheater? Because challenge-0 only checks `H(r) = aux`, which the cheater CAN satisfy — they pick `r`, compute `aux = H(r)`, and succeed. Challenge-1 requires actually using the witness, which they can't. A random bit means they pass each round with probability 1/2, and 32 rounds puts them below 2⁻³².

### 3.4 Encoding edge cases

```python
import ladhe_rsa as LR

# Negative witness part — rejected
try:
    LR._encode_witness((2, -1, 6))
except ValueError as e:
    print("caught:", e)

# Zero is allowed (additive identity)
print("encoded zero:", LR._encode_witness((0, 5, 6)).hex())

# Very large values encode to longer byte strings
big = 10**40
encoded = LR._encode_witness((big, 1, 1))
print("big value encoding size:", len(encoded), "bytes")
```

---

## 4. Benchmarking (rough)

```python
import time
import ladhe_rsa as LR

pk, sk = LR.keygen()
msg = b"benchmark message" * 100

# Signing
t0 = time.perf_counter()
for _ in range(10):
    sig = LR.sign(msg, sk, pk)
t1 = time.perf_counter()
print(f"sign: {(t1-t0)/10*1000:.1f} ms/sig (64 rounds)")

# Verifying
t0 = time.perf_counter()
for _ in range(10):
    LR.verify(msg, sig, pk)
t1 = time.perf_counter()
print(f"verify: {(t1-t0)/10*1000:.1f} ms/sig")

print(f"sig size: {len(sig.encode())} bytes")
```

On a typical laptop: sign and verify each take a few milliseconds; signatures are ~7 KB at the default 64-round setting. That signature size is the main honest-about-it weakness of the prototype — a production scheme would compress it via MPC-in-the-head.

---

## 5. What to try when cryptanalysing

If you want to attack your own scheme (a good practice), try these:

1. **Break challenge-1 at toy size.** Given a valid `(commit, response)` pair with `challenge=1`, the response contains `salt` and `r ⊕ witness_encoding`. Brute-force every 8-bit witness, compute `witness_encoding`, XOR with `response.opening` to recover `r`, and check against `commit.a_commit`. At 8-bit parameters this takes microseconds.

2. **Write an LDP solver at bits=16 or 24.** Enumerate triples `(a, b, c)` with `a + b + c = P`, compute `hash_commitment((a,b,c), salt)`, compare to `h`. Measure how long it takes. Scale the time to bits=256.

3. **Two signatures on the same message.** Do they leak anything? (They shouldn't — the Fiat-Shamir challenges are deterministic — but verify.)

4. **Forge a signature from transcripts.** Given many valid signatures from the same key, can you produce a signature on a new message without the witness? (You shouldn't be able to. If you can, it's a major finding — file an issue.)

---

## 6. Cleanup

```bash
# Remove Python bytecode caches
rm -rf __pycache__
find . -name "*.pyc" -delete
```

---

## Summary table

| File | Command | What to look for |
|---|---|---|
| `ladhe_rsa.py` | `python3 ladhe_rsa.py demo` | All 6 steps print non-error output |
| `test_ladhe_rsa.py` | `python3 -m unittest test_ladhe_rsa -v` | All tests pass, no failures |
| `example_code_signing.py` | `python3 example_code_signing.py` | Tamper fails, genuine verify succeeds |
| REPL experiments | see sections above | Intermediate values shape your intuition |

If any of these produce unexpected output, treat it as a bug report for the repo.
