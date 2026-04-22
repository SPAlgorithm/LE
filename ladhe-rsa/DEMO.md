# Demo commands from the video

Every command shown in the "Ladhe-RSA Signatures" explainer video, in order. Copy-paste any of them — they all work after a `git clone` of this folder.

---

## Quick start — run everything at once

```bash
cd ladhe-rsa
chmod +x demo.sh    # first time only
./demo.sh
```

Walks through all five demos with pauses between. Press **Enter** to advance.

---

## The commands, one at a time

### 1. See it in action (video: ~6:22)

```bash
python3 ladhe_rsa.py demo
```

**Expected output** (abridged):

```
Ladhe-RSA reference implementation — demo

Loaded 1618 valid entries from dataset.

Key generated:
  prime        = 65336989  (26 bits)
  witness      = (50936514, 14366710, 15740, 18025)  (kept secret)
  commitment   = 6edf8d944d52e86858db7804a94189f9...
  salt         = bade3a0ac7b18943c331fca15214461e...

Running identification protocol (32 rounds)...
  identification verifies: True

Signing message: b'Hello, Ladhe-RSA community!'
  signature size: 7140 bytes
  signature verifies:     True

Tampered-message verify (should be False): False
```

---

### 2. Try to break it — generate a fresh LDP challenge (video: ~9:00)

```bash
python3 -c "
import ladhe_rsa as LR
P, h, s = LR.generate_ldp_challenge(bits=32)
print('Your LDP challenge:')
print('  P    =', P)
print('  salt =', s.hex())
print('  h    =', h.hex())
"
```

**Your task:** find positive integers `a, b, c` with:
- `a + b + c = P`
- `sha256(salt || canonical_encode(a, b, c)) == h`

Solving this faster than brute force breaks the scheme.

`canonical_encode` is defined in `ladhe_rsa._encode_witness`. At `bits=32`, brute force takes ~2³² hash evaluations (~seconds to minutes on a laptop); at `bits=256`, it's 2²⁵⁶ — infeasible.

---

### 3. Run the unit test suite

```bash
python3 -m unittest test_ladhe_rsa -v
```

Expect ~15 tests, all OK. Tests cover primality, dataset loading, hash commitments, keygen, Sigma protocol, signatures, and the LDP challenge generator.

---

### 4. Practical code-signing example

```bash
python3 example_code_signing.py
```

Simulates the realistic flow:
- **Bob** signs a software release
- **Attacker** swaps in malicious software → verification **fails**
- **Alice** downloads the genuine release → verification **succeeds**

No encryption anywhere. Signatures alone provide integrity and authenticity — which is the use case for every app store, every TLS certificate, every cryptocurrency transaction.

---

### 5. One-liner sanity check

```bash
python3 -c "
import ladhe_rsa as LR
pk, sk = LR.keygen()
sig = LR.sign(b'hi', sk, pk)
print('genuine message verifies:', LR.verify(b'hi', sig, pk))
print('tampered message rejects:', not LR.verify(b'evil', sig, pk))
"
```

**Expected output:**

```
genuine message verifies: True
tampered message rejects: True
```

If both lines print `True`, the library is working correctly.

---

### 6. Sign your own message from the CLI

```bash
python3 ladhe_rsa.py sign "your message here"
```

Generates a fresh key pair, signs the message, prints the public key and signature bytes.

---

## For deeper testing

See [`MANUAL_TESTING.md`](./MANUAL_TESTING.md) — eight sections covering:

- Primality, dataset, and commitment primitives in isolation
- Step-by-step Sigma protocol (one round at a time, printing intermediate values)
- Negative tests (cheating provers, wrong salts, invalid witnesses)
- Simple benchmarks
- Suggested cryptanalysis exercises

## Breaking the scheme

If you find a way to solve an LDP challenge faster than brute force, or forge a signature without the witness, please open an issue:

- Repo: https://github.com/SPAlgorithm/LE
- Paper: https://zenodo.org/records/19680322
- DOI: 10.5281/zenodo.19680322

Cryptanalysis is the point. Every attack strengthens the field.
