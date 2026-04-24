# Demo commands

Quick-reference commands for the Ladhe v3 reference implementation.
For the Alice & Bob enterprise demo, see
[`../Demo/DEMO_WALKTHROUGH.md`](../Demo/DEMO_WALKTHROUGH.md).

---

## Quick start — one-shot smoke test

```bash
cd ladhe-rsa
chmod +x demo.sh    # first time only
./demo.sh
```

Walks through all demos with pauses. Press **Enter** to advance.

---

## The commands, one at a time

### 1. End-to-end demo

```bash
python3 ladhe_rsa.py demo 5
```

(The `5` is the decimal-digit count for the public prime P — small
enough that KeyGen finishes in milliseconds.)

**Expected output (abridged):**

```
Ladhe v3 reference — demo (digits=5)

KeyGen:        1.78 ms
  P          = 27823  (15 bits)
  k          = 5
  primes     = (17, 53, 107, 1033, 26613)   (secret)
  W          = (70, 1140, 26613)
  h          = 3b29c2a08d4f...

Sign:          0.01 ms, signature size = 38 bytes
Verify:        0.22 ms, result = True

Tampered-message verify (should be False): False

Fresh LDP challenge (32-bit):
  P = 2854391051
  h = ...
```

---

### 2. Timing benchmark across prime sizes

```bash
python3 ladhe_rsa.py bench
```

Prints KeyGen / Sign / Verify times and signature sizes for digits ∈
{3, 5, 7, 10, 15, 20, 30, 50}.

---

### 3. Generate a fresh LDP challenge (for cryptanalysts)

```bash
python3 -c "
import ladhe_rsa as LR
P, h = LR.generate_ldp_challenge(bits=32)
print('Your LDP challenge:')
print(f'  P = {P}')
print(f'  h = {h.hex()}')
"
```

**Your task:** find a sorted tuple of distinct odd primes
`(p_1 < ... < p_k)` with `k` odd, such that:

- `sum(p_i) = P`, and
- `sha256(encode_W(pair_compress(primes))) == h`

`encode_W` and `pair_compress` are defined in
[`ladhe_rsa.py`](./ladhe_rsa.py). Solving faster than hash preimage
breaks the scheme.

At `bits=32`, brute force takes seconds on a laptop. At `bits=256`,
2²⁵⁶ — infeasible.

---

### 4. Run the unit test suite

```bash
python3 -m unittest test_ladhe_rsa -v
python3 -m unittest test_ladhe_x509 -v    # X.509 export tests
```

Expect 11 core tests + 4 X.509 tests. All should pass.

---

### 5. One-liner sanity check

```bash
python3 -c "
import ladhe_rsa as LR
pk, sk = LR.keygen(up1=5)
sig = LR.sign(b'hi', sk)
print('genuine message verifies:', LR.verify(b'hi', sig, pk))
print('tampered message rejects:', not LR.verify(b'evil', sig, pk))
"
```

Both lines should print `True`.

---

### 6. Sign your own message from the CLI

```bash
python3 ladhe_rsa.py sign "your message here"
```

Generates a fresh one-time key pair, signs the message, prints the
public key and signature bytes.

> ⚠️ One-time only — this key pair must not be used to sign anything
> else. Use a fresh keygen for each new message.

---

### 7. Certificate + X.509 demo

```bash
bash demo_x509.sh
```

Bootstraps a CA, issues a cert, exports to DER and PEM X.509,
and shows OpenSSL parsing the result end-to-end.

---

## Breaking the scheme

If you find:

1. An algorithm that recovers the prime decomposition from `(P, h)`
   asymptotically faster than SHA-256 preimage, or
2. A way to forge a signature under a fresh key pair without ever
   seeing a legitimate signature,

please open an issue:

- Repo: https://github.com/SPAlgorithm/LE
- Paper: `SP_Paper_v3.pdf` (this folder) + Zenodo
  10.5281/zenodo.19680322

Cryptanalysis is the point.
