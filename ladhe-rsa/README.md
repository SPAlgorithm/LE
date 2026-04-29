# Ladhe

Reference implementation of the signature scheme from the paper:

> **Ladhe Signatures: Compact Hash-Based Signatures from Additive Prime Decompositions**
> Shubham Ladhe, Pankaj Ladhe (2026)
> Zenodo: [10.5281/zenodo.19888480](https://zenodo.org/records/19888480)

---

## ⚠️ Status: Research reference, not production

This repository exists to accompany the paper and **enable community cryptanalysis**. Do not use it to protect real data.

**What Ladhe is** (honestly):

- A **one-time hash-based signature scheme** in the same family as Lamport, SPHINCS+, and SLH-DSA.
- Security **reduces to SHA-256 preimage resistance** — the same standard assumption as SPHINCS+. There is **no new hardness assumption**.
- The novelty is in the *structure* of the hash preimage: the private key is a sorted tuple of distinct odd primes summing to the public prime P. This enables dramatically smaller signatures (~100 bytes vs SPHINCS+'s ~17 KB) at the cost of significantly slower KeyGen.

**Known limitations:**

- **One-time only.** Signing two messages with the same key leaks the private key. The paper (§6) sketches a Merkle-aggregated many-time extension; this is not yet implemented.
- **KeyGen scales, but slowly.** With the sieve-accelerated random-trial search (v3.1), KeyGen is sub-millisecond at 5-digit primes, ~8 ms at 50 digits (165 bits), ~400 ms at 200 digits (664 bits), and ~90 s at 1000 digits (3322 bits). Lower is better, of course — efficient constructive decomposition remains open work (paper §8).
- **No side-channel resistance**, no constant-time operations.
- **Community cryptanalysis has not yet occurred.** The scheme is released to invite it.

**If you find a break, please open an issue or email the authors.** That's the point.

---

## What this repository provides

| Function | Purpose |
|---|---|
| `keygen(up1)` | Sample a (public, private) key pair for a prime of `up1` decimal digits |
| `sign(message, sk)` | Produce a one-time signature (reveals the prime decomposition) |
| `verify(message, sig, pk)` | Verify a signature against the public key |
| `is_prime(n)` | Miller-Rabin primality test |
| `pair_compress(primes)` | Indexed-pair compression of the private decomposition |
| `encode_W(W)` | Canonical byte encoding of a compressed witness |
| `generate_ldp_challenge(bits)` | Produce a fresh (P, h) challenge for cryptanalysts |

The implementation is deliberately self-contained in a single file ([`ladhe_rsa.py`](./ladhe_rsa.py)) so it's easy to audit end-to-end.

---

## Installation

Requires **Python 3.9+**. The core scheme has **no third-party dependencies**. The optional `x509` extra pulls in `asn1crypto` for DER/PEM certificate export.

Everything below uses `pyproject.toml`; `ladhe-rsa` is declared as a package named `ladhe-rsa` with version `0.3.0`.

### Option A — Install from GitHub

```bash
# With virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate           # macOS/Linux
# .venv\Scripts\activate            # Windows

# Core scheme
pip install "git+https://github.com/SPAlgorithm/LE.git#subdirectory=ladhe-rsa"

# Core scheme + X.509 export
pip install "git+https://github.com/SPAlgorithm/LE.git#subdirectory=ladhe-rsa[x509]"
```

### Option B — Clone and install locally (editable, for development)

```bash
git clone https://github.com/SPAlgorithm/LE.git
cd LE/ladhe-rsa

python3 -m venv .venv && source .venv/bin/activate

pip install -e ".[x509]"             # changes to source reflect immediately
```

### Option C — Just run the scripts (no install)

```bash
git clone https://github.com/SPAlgorithm/LE.git
cd LE/ladhe-rsa
python3 ladhe_rsa.py demo            # works with zero pip install
```

(`ladhe_x509.py` still needs `pip install asn1crypto` separately for X.509 export.)

### Verify the install

After any of the above:

```bash
ladhe-rsa demo                       # CLI entry point
ladhe-rsa bench                      # timing benchmark
python3 -c "import ladhe_rsa; print(ladhe_rsa.keygen(up1=5))"
python3 -m unittest                  # run the full test suite
```

### What `pip install` actually gives you

| Thing | Source |
|---|---|
| Importable modules: `ladhe_rsa`, `ladhe_cert`, `ladhe_cert_cli`, `ladhe_x509` | `[tool.setuptools] py-modules` in `pyproject.toml` |
| CLI command: `ladhe-rsa` → runs `ladhe_rsa.main()` | `[project.scripts]` in `pyproject.toml` |
| Optional dep `asn1crypto>=1.5` (only with `[x509]`) | `[project.optional-dependencies]` |
| Python 3.9+ enforcement | `requires-python` |

The scheme does not consult any bundled dataset at run time — every `keygen(up1=...)` call samples a fresh prime and a fresh decomposition.

---

## Quick start

**Want to run everything at once?** See [`DEMO.md`](./DEMO.md) for a command-by-command breakdown, or just run:

```bash
chmod +x demo.sh && ./demo.sh
```

This runs 6 demos end-to-end: full scheme demo, timing benchmark, LDP challenge, unit tests, sanity check, and the software-signing example.

**Want the live Alice & Bob walkthrough?** Bootstraps an Acme Quantum CA, issues certs to Alice and Bob, then runs the 7-step signing/verifying/tampering demo:

```bash
cd demo
./setup.sh    # one-time PKI bootstrap (~1 second)
./run.sh      # the live demo with ENTER-paced steps
```

See [`demo/README.md`](./demo/README.md) for full details.

### Sign a message (one-time)

```python
import ladhe_rsa as LR

# One-time key setup (5-digit prime; quick for demo)
pk, sk = LR.keygen(up1=5)

# Sign ONCE — signing twice with the same key leaks the secret.
message = b"software-release-v1.0.0.sha256:abc123..."
sig = LR.sign(message, sk)

# Verify using only the public key
assert LR.verify(message, sig, pk)
```

### Run the benchmark

```bash
python3 ladhe_rsa.py bench
```

Outputs measured KeyGen / Sign / Verify times and signature sizes at several prime scales.

### Run the full demo

```bash
python3 ladhe_rsa.py demo
```

Output walks through key generation, signing, verification, tampered-message rejection, and a fresh LDP challenge.

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

The paper **does not propose** an encryption scheme. This implementation provides one-time hash-based signatures, which is what the current paper specifies.

Digital signatures answer *"who really wrote this, unmodified?"* — and that's the primitive behind:

- Code signing (app stores, OS updates, firmware)
- TLS certificates
- Cryptocurrency transactions
- Git commit signing
- WebAuthn / passkeys
- Document signing

None of those need encryption. If Ladhe signatures ever mature into a production-grade scheme, these are the deployment targets.

---

## For cryptanalysts

The code exposes a fresh LDP challenge generator:

```python
import ladhe_rsa as LR

P, h = LR.generate_ldp_challenge(bits=32)
# Your task: find distinct odd primes (p_1 < ... < p_k), k odd,
#   such that sum(p_i) = P  AND
#   sha256(encode_W(pair_compress(p_1,...,p_k))) == h
```

The canonical encoding is `LR.encode_W`; the pair compression is `LR.pair_compress`. The paper (§3.2–§3.3) defines both exactly.

If you break any of the following, the authors would like to know:

1. **LDP itself** — given `(P, h)`, recover a valid decomposition in time asymptotically faster than the brute-force bound on the secret space.
2. **A structural shortcut** — given the scheme's arithmetic structure (distinct odd primes, odd `k`, ascending order), a recovery algorithm faster than hash preimage on SHA-256.
3. **The signature** — existentially forge a signature for a message on a fresh key pair without ever seeing a legitimate signature.

Please open an issue with a concrete demonstration.

---

## Known limitations

| Limitation | Severity | Mitigation |
|---|---|---|
| One-time only — signing twice leaks the private key | **High** | Use Merkle-aggregated many-time extension (paper §6) — not yet implemented |
| Slow KeyGen at cryptographic sizes | **High** | Efficient decomposition search is open work (paper §8) |
| Non-constant-time primality checks | Medium | Research reference only; production would need constant-time MR |
| SHA-256 modelled as random oracle in proofs | Standard | Same assumption as every hash-based scheme |
| No structural-attack analysis | Medium | Community cryptanalysis invited (paper §4) |

---

## Repository layout

```
ladhe-rsa/
├── ladhe_rsa.py              # core scheme: KeyGen, Sign, Verify
├── ladhe_cert.py             # experimental certificate format
├── ladhe_cert_cli.py         # CLI wrapper for cert operations
├── ladhe_x509.py             # DER/PEM X.509 export (optional; needs asn1crypto)
├── test_ladhe_rsa.py         # unit tests for the scheme
├── test_ladhe_x509.py        # unit tests for X.509 export
├── example_code_signing.py   # realistic software-signing demo
├── demo_cert.py              # end-to-end PKI demo script
├── demo.sh                   # run the full suite of demos
├── demo_x509.sh              # X.509 export + openssl parsing demo
├── README.md                 # this file
├── DEMO.md                   # quick-reference commands
├── CERTIFICATES.md           # certificate-format details
├── ALGORITHM_SPEC.md         # formal algorithm specification
├── OID_REGISTRY.md           # IANA OID arc and ASN.1 module
├── ROADMAP.md                # near, medium, and long-term goals
├── MANUAL_TESTING.md         # deeper cryptanalysis walkthrough (v1 — archived)
├── pyproject.toml            # packaging (with [x509] extra)
├── LICENSE                   # CC BY 4.0
└── .gitignore
```

---

## Citing this work

If you build on this paper or implementation, please cite:

```bibtex
@misc{ladhe2026signatures,
  author = {Shubham Ladhe and Pankaj Ladhe},
  title  = {{Ladhe Signatures: Compact Hash-Based Signatures
             from Additive Prime Decompositions}},
  year   = {2026},
  doi    = {10.5281/zenodo.19888480},
  url    = {https://zenodo.org/records/19888480},
}
```

---

## License

Code and paper are released under **Creative Commons Attribution 4.0 (CC BY 4.0)**. You may use, modify, and redistribute with attribution. See [LICENSE](./LICENSE) for the full text.

---

## Contributing

Contributions welcome, especially:

- **Cryptanalysis**: structural shortcuts on LDP beyond generic hash preimage
- **Efficient KeyGen**: constructive algorithms for the decomposition search at cryptographic prime sizes (currently the main barrier)
- **Many-time extension**: implementation of the Merkle-aggregated variant sketched in the paper (§6)
- **Constant-time / side-channel hardening** of primality checks
- **Benchmarks** at larger parameter sizes and on different hardware
- **Bindings** (Rust, C, JavaScript) once the Python reference is stable

Please open an issue before starting significant work so we can coordinate.

---

## Algorithm Identifier (OID)

IANA Private Enterprise Number **65644** was registered to LeSecure on
2026-04-23. The resulting OIDs for Ladhe are:

```
1.3.6.1.4.1.65644.1.1    id-ladhe-signature
1.3.6.1.4.1.65644.1.2    id-ladhe-publicKey
1.3.6.1.4.1.65644.2.1    id-ladhe-cert-v1
```

Full arc and ASN.1 module: see [OID_REGISTRY.md](OID_REGISTRY.md) and
the formal specification at [ALGORITHM_SPEC.md](ALGORITHM_SPEC.md).

### X.509 export (optional)

Install the `x509` extra (adds `asn1crypto`) to export certificates as
DER or PEM X.509 files that standard tools like `openssl asn1parse` and
`openssl x509 -text` can parse:

```bash
pip install "ladhe-rsa[x509]"

# Bootstrap a CA and issue a cert (creates demo_pki/ the first time)
python3 ladhe_cert_cli.py init-ca --cn "Example Root CA"
python3 ladhe_cert_cli.py issue   --cn alice@example.com

# Export the cert as X.509 PEM and inspect with OpenSSL
python3 ladhe_cert_cli.py export-x509 \
    --cert demo_pki/alice.cert.pem \
    --out  alice.x509.pem \
    --format pem

openssl x509 -in alice.x509.pem -text -noout
# Signature Algorithm: 1.3.6.1.4.1.65644.1.1
# Issuer: CN=Example Root CA
# Subject: CN=alice@example.com
# Public Key Algorithm: 1.3.6.1.4.1.65644.1.2
```

Run [`demo_x509.sh`](demo_x509.sh) for the full walkthrough.
OpenSSL can introspect every field *except* cryptographically verify
the signature — that requires an OpenSSL provider plugin, which is
the next engineering milestone.

---

## Authors

- **Shubham Ladhe** — [spalgorithm@gmail.com](mailto:spalgorithm@gmail.com)
- **Pankaj Ladhe** — [spalgorithm@gmail.com](mailto:spalgorithm@gmail.com)

SPAlgorithm is the cryptography research program of **LESecure AI, Inc.**

---

## Acknowledgements

The paper benefited from extensive informal review. Any errors are the authors' own.
