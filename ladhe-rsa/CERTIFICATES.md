# Ladhe-RSA Certificates (experimental format)

An experimental certificate format backed by Ladhe-RSA signatures, for **local testing and demonstrations only.**

---

## ⚠️ These are NOT yet X.509 certificates

**Update (April 2026):** Ladhe-RSA now has an IANA-registered algorithm
identifier — `1.3.6.1.4.1.65644.1.1` (`id-ladhe-rsa-signature`) — under
Private Enterprise Number **65644**. The OID is already embedded in every
certificate this tool produces. See [OID_REGISTRY.md](OID_REGISTRY.md) and
[ALGORITHM_SPEC.md](ALGORITHM_SPEC.md) for the full arc and ASN.1 module.

Full X.509 interoperability still requires two additional pieces of work:
ASN.1 DER encoding of the certificate body (instead of our JSON), and an
OpenSSL provider plugin so standard tooling can parse and verify the
certificates. Both are tractable — roughly one to two years — but are
ahead of us, not behind.

This format uses its own JSON-based structure wrapped in PEM markers (`-----BEGIN LADHE CERTIFICATE-----`). It is:

| ✅ Good for | ❌ NOT good for |
|---|---|
| Local testing | Browsers (Safari, Chrome, Firefox) |
| Demonstrating PKI flows | Real TLS / HTTPS |
| Educational exercises | Apple Keychain or macOS code-signing (`codesign`) |
| Prototype interop between Ladhe-aware tools | OpenSSL, GnuTLS, or any standards-compliant tool |
| Showing what a Ladhe-RSA PKI would look like | Any production system |

Do not attempt to load these files into any system that expects X.509. They will be rejected, and rightly so.

---

## Quick start

```bash
python3 demo_cert.py
```

This runs a full end-to-end simulation:

1. Bootstraps a self-signed **root CA**
2. **Alice** generates a key pair
3. The CA **issues a certificate** for Alice
4. A third party **verifies Alice's cert** against the CA
5. A rogue CA **fails** to vouch for Alice (negative test)
6. Alice **signs a document** under her cert
7. **Bob verifies** the document + cert chain
8. **Tampered document fails** verification

All files land in `./demo_pki/` so you can open and inspect them.

---

## File format

Each `.cert.pem` file is a PEM-wrapped base64-encoded JSON object with this shape:

```json
{
  "version": 1,
  "serial": "c379b4ff70634c276a2e563d33bccfa7",
  "issuer":  {"CN": "Ladhe Test Root CA"},
  "subject": {"CN": "alice@example.com"},
  "not_before": "2026-04-22T11:36:52+00:00",
  "not_after":  "2027-04-22T11:36:52+00:00",
  "public_key": {
    "algorithm":  "ladhe-sig-v1",
    "prime":      "123364601",
    "commitment": "6e35f93a...",
    "salt":       "a1b2c3..."
  },
  "extensions": {
    "basicConstraints": {"CA": false},
    "keyUsage":         ["digitalSignature"]
  },
  "signature": {
    "algorithm": "ladhe-sig-v1",
    "value":     "<hex bytes of Fiat-Shamir signature>"
  }
}
```

Compared to X.509, the significant simplifications are:

- **JSON instead of DER/ASN.1** — easier to read, less efficient
- **CN-only names** — no full distinguished-name hierarchy
- **No OCSP / CRL** — revocation not modeled
- **No SAN / URI / email extensions** — just `CN`
- **Minimal extensions** — only `basicConstraints` and `keyUsage`

These are all deliberate: the goal is demonstration, not standards compliance.

---

## Programmatic use

```python
import ladhe_rsa as LR
import ladhe_cert as LC

# Create a CA
ca_cert, ca_sk = LC.create_ca("Example Root CA", validity_days=3650)

# Subject generates their own key pair
subject_pk, subject_sk = LR.keygen(min_prime_bits=24)

# CA issues
subject_cert = LC.issue_certificate(
    ca_cert, ca_sk,
    subject_cn="alice@example.com",
    subject_pk=subject_pk,
    validity_days=365,
)

# Third party verifies
ok, reason = LC.verify_certificate(subject_cert, ca_cert)
assert ok, reason

# Save / load
LC.write_cert("alice.cert.pem", subject_cert)
reloaded = LC.read_cert("alice.cert.pem")

# Alice signs a document
sig = LC.sign_document(b"contract text", subject_cert, subject_sk)

# Bob verifies
assert LC.verify_document(b"contract text", sig, subject_cert)
```

---

## Chain verification

For multi-level PKI (root → intermediate → end-entity):

```python
ok, reason = LC.verify_chain(
    end_cert=alice_cert,
    intermediates=[intermediate_ca_cert],
    trust_anchor=root_ca_cert,
)
```

The trust anchor must be self-signed. Each link in the chain is verified against its parent.

---

## What's NOT modelled

| Missing | Why |
|---|---|
| **Revocation (CRL / OCSP)** | Adds complexity without changing the core demonstration |
| **Path length constraints** | Only a single-level hierarchy tested |
| **Name constraints** | Beyond scope of a signature demo |
| **Critical extensions / extended key usage** | Simplified for clarity |
| **Encrypted private keys** | The key PEM is plaintext JSON — **demo only** |

Any of these could be added incrementally. This file format is versioned (`"version": 1`) so future revisions can add fields without breaking older code.

---

## Path to real-world interoperability

If Ladhe-RSA's hardness assumption survives cryptanalysis and the paper is peer-reviewed:

1. **✅ Obtain an OID** — done. IANA PEN 65644 (April 2026); `id-ladhe-rsa-signature` is `1.3.6.1.4.1.65644.1.1`.
2. **Publish an Internet-Draft / RFC** specifying the ASN.1 encoding of the public key and signature
3. **Implement in OpenSSL** (or a provider plugin) so standard tools can generate and verify X.509 Ladhe-RSA certificates
4. **Get it on CAB Forum's list** of approved signature algorithms for web PKI

Steps 2–3 take one to two years typically. Step 4 takes longer. Before any of that, the cryptanalysis must withstand community scrutiny — which is why the paper and this implementation lead with a challenge, not a claim.

---

## Security note (again)

The Sigma protocol used for the underlying signatures is a **simplified prototype** — see the top-level `README.md` for the list of known limitations. Do not use these certificates to protect real data, real identity, or real documents. When cryptography is at stake, "demo only" means demo only.

---

## Feedback

If you find a bug in the cert format, file an issue:

- Repo: https://github.com/SPAlgorithm/LE
- Paper: https://zenodo.org/records/19680322

If you find a cryptographic break, see the main `README.md` for how to report.
