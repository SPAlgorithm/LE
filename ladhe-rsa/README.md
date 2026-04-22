# Ladhe-RSA

Reference implementation of the identification and signature scheme from the paper:

> **The Ladhe Decomposition Problem: A Candidate Post-Quantum Hardness Assumption on Additive Prime Structure, with an Identification Scheme**
> Shubham Ladhe, Pankaj Ladhe (2026)
> Zenodo: [10.5281/zenodo.19680322](https://zenodo.org/records/19680322)
> Dataset: [10.5281/zenodo.19354450](https://zenodo.org/records/19354450)

---

## ⚠️ Status: Research reference, not production

This repository exists to accompany the paper and **enable community cryptanalysis**. Do not use it to protect real data.

Specifically:

- The hardness assumption (LDP) is **unproven**. It is proposed as a candidate and awaits community analysis.
- The Sigma protocol is a **simplified commit-and-open variant**, not a tight zero-knowledge construction. A production scheme would use MPC-in-the-head (IKOS 2007) or a zk-SNARK framework.
- **No side-channel resistance**, no constant-time operations, no memory hygiene.
- At toy parameter sizes (which the accompanying dataset supports — 8–30 bit primes), the challenge-1 branch of the Sigma protocol leaks enough information for an offline brute-force attack on the witness. At real cryptographic sizes this is infeasible, but the code is still not hardened.

**If you find a break, please open an issue or email the authors.** That's the point.

---

## What this repository provides

| Function | Purpose |
|---|---|
| `load_dataset()` | Parse `LadheConjecture.txt` into structured entries |
| `is_prime(n)` | Miller-Rabin primality test |
| `hash_commitment(witness, salt)` | SHA-256-based Φ₁ commitment |
| `keygen()` | Sample a (public, private) key pair |
| `run_identification(pk, sk)` | Interactive Sigma protocol |
| `sign(message, sk, pk)` | Non-interactive Fiat-Shamir signature |
| `verify(message, signature, pk)` | Verify a signature |
| `generate_ldp_challenge(bits)` | Produce a fresh LDP instance for cryptanalysts |

The implementation is deliberately self-contained in a single file ([`ladhe_rsa.py`](./ladhe_rsa.py)) so it's easy to audit end-to-end.

---

## Installation

Requires Python 3.9+. No third-party dependencies.

**Install directly via pip:**

```bash
pip install git+https://github.com/SPAlgorithm/LE.git#subdirectory=ladhe-rsa
```

**Or clone and run:**

```bash
git clone https://github.com/SPAlgorithm/LE.git
cd LE/ladhe-rsa
python3 ladhe_rsa.py demo
```

The dataset file `LadheConjecture.txt` is bundled in this folder, so the demo runs out of the box after a clone. If you want to use your own dataset, pass its path to `load_dataset()`. The canonical version of the dataset is archived at [Zenodo 10.5281/zenodo.19354450](https://zenodo.org/records/19354450).

---

## Quick start

**Want to reproduce everything from the companion video?**
See [`DEMO.md`](./DEMO.md), or just run:

```bash
chmod +x demo.sh && ./demo.sh
```

For deeper step-by-step testing — negative cases, benchmarks, cryptanalysis exercises — see [`MANUAL_TESTING.md`](./MANUAL_TESTING.md).

### Sign a message

```python
import ladhe_rsa as LR

# One-time key setup
pk, sk = LR.keygen()

# Sign
message = b"software-release-v1.0.0.sha256:abc123..."
sig = LR.sign(message, sk, pk)

# Verify (using only the public key)
assert LR.verify(message, sig, pk)
```

### Identification (interactive)

```python
pk, sk = LR.keygen()
ok = LR.run_identification(pk, sk, rounds=32)
# Soundness error: 2^-32 after 32 rounds
```

### Run the full demo

```bash
python3 ladhe_rsa.py demo
```

Output walks through key generation, identification, signing, verification, tampered-message rejection, and an LDP challenge.

### Run the tests

```bash
python3 -m unittest test_ladhe_rsa -v
```

### Example: software code signing

See [`example_code_signing.py`](./example_code_signing.py) for a realistic end-to-end flow: Bob signs a release, an attacker tries to tamper, Alice verifies.

```bash
python3 example_code_signing.py
```

---

## Why signatures and not encryption?

The paper **does not propose** an encryption scheme. An earlier draft of the work did — we withdrew it as unsound. This implementation only provides signatures and identification, which are what the current paper specifies.

Digital signatures answer *"who really wrote this, unmodified?"* — and that's the primitive behind:

- Code signing (app stores, OS updates, firmware)
- TLS certificates
- Cryptocurrency transactions
- Git commit signing
- WebAuthn / passkeys
- Document signing

None of those need encryption. If Ladhe-RSA signatures ever mature into a production-grade scheme, these are the deployment targets.

---

## For cryptanalysts

The code exposes a fresh LDP challenge generator:

```python
import ladhe_rsa as LR

P, h, salt = LR.generate_ldp_challenge(bits=32)
# Your task: find (a, b, c) with
#   a + b + c = P
#   sha256(salt || canonical_encode(a, b, c)) == h
```

The encoding is defined in `ladhe_rsa._encode_witness`. If you break any of the following, the authors would like to know:

1. **LDP itself** — given `(P, h, salt)`, recover a valid witness in time polynomial in `log P` (classically or quantumly).
2. **The simplified Sigma protocol** — given a public key and polynomially-many valid transcripts, forge a new one without knowing the witness.
3. **The Fiat-Shamir signature** — existentially forge a signature for a message you did not legitimately sign.

Please open an issue with a concrete demonstration.

---

## Known limitations

| Limitation | Severity | Mitigation |
|---|---|---|
| Simplified Sigma protocol leaks information at toy sizes | Medium | At real κ ≥ 256 sizes, brute force is infeasible; still, production requires MPC-in-the-head |
| No formal ZK proof | Medium | Future work; see paper §4 and §7 |
| LDP hardness unproven | **High** | Core assumption; awaits community analysis |
| Dataset entries may be constructively generated | Medium | See paper §2, Open Problem #4 |
| Non-constant-time | Low (for research use) | Not a production implementation |
| SHA-256 as random oracle in proofs | Standard | Same assumption as most Fiat-Shamir schemes |

---

## Repository layout

```
ladhe-rsa/
├── ladhe_rsa.py              # main implementation
├── test_ladhe_rsa.py         # unit tests
├── example_code_signing.py   # realistic software-signing demo
├── LadheConjecture.txt       # empirical dataset (1,620+ entries)
├── DEMO.md                   # commands from the companion video
├── demo.sh                   # run all the video demos at once
├── MANUAL_TESTING.md         # deeper testing + cryptanalysis guide
├── README.md                 # this file
├── LICENSE                   # CC BY 4.0
└── .gitignore
```

---

## Citing this work

If you build on this paper or implementation, please cite:

```bibtex
@misc{ladhe2026ldp,
  author       = {Shubham Ladhe and Pankaj Ladhe},
  title        = {{The Ladhe Decomposition Problem: A Candidate Post-Quantum
                  Hardness Assumption on Additive Prime Structure, with an
                  Identification Scheme}},
  year         = {2026},
  doi          = {10.5281/zenodo.19680322},
  url          = {https://zenodo.org/records/19680322},
  note         = {IACR ePrint: \url{https://eprint.iacr.org/2026/NNNN}},
}
```

(Replace `NNNN` with the real ePrint ID once the paper is approved.)

---

## License

Code and paper are released under **Creative Commons Attribution 4.0 (CC BY 4.0)**. You may use, modify, and redistribute with attribution. See [LICENSE](./LICENSE) for the full text.

---

## Contributing

Contributions welcome, especially:

- **Cryptanalysis**: attacks, breaks, reductions to known hard problems
- **Formal security proofs** or disproofs
- **MPC-in-the-head or zk-SNARK implementations** of a tight ZK Sigma protocol
- **Better dataset generation** tooling or a formal characterisation of Φ
- **Benchmarks** at real cryptographic parameter sizes
- **Bindings** (Rust, C, JavaScript) once the Python reference is stable

Please open an issue before starting significant work so we can coordinate.

---

## Authors

- **Shubham Ladhe** — [spalgorithm@gmail.com](mailto:spalgorithm@gmail.com)
- **Pankaj Ladhe** — [spalgorithm@gmail.com](mailto:spalgorithm@gmail.com)

---

## Acknowledgements

The paper benefited from extensive informal review. Any errors are the authors' own.
