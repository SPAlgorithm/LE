# Alice & Bob: Live Ladhe PKI Demo

A scripted walkthrough showing how a small enterprise PKI built on the
Ladhe one-time hash-based signature scheme works end-to-end. Acme Corp
runs an internal Certificate Authority; Alice (Procurement) signs a
$1.25M purchase order; Bob (Finance) verifies the cert chain and the
signature; a tamper attempt is caught.

---

## Two-step quickstart

```bash
cd ladhe-rsa/demo

# Bootstrap the CA, Alice, and Bob (one-time, ~1 second)
./setup.sh

# Run the live demo (presses ENTER between steps)
./run.sh
```

That's it. To re-run from a clean slate, repeat both. To re-run the demo
without regenerating certs, just `./run.sh` again.

---

## What the scripts do

| Script | Purpose |
|---|---|
| `setup.sh` | Bootstraps Acme CA + Alice + Bob certs in `ca/`, `alice/`, `bob/`. Idempotent. |
| `run.sh`   | The 7-step Alice → Bob signing demo, with pauses for narration. |

Override the prime size for setup:

```bash
DIGITS=7 ./setup.sh    # 23-bit primes; still finishes in ~milliseconds
```

---

## Folder layout after `./setup.sh`

```
ladhe-rsa/demo/
├── setup.sh                   # bootstrap the demo PKI
├── run.sh                     # the 7-step live demo
├── README.md                  # this file
├── purchase_order.txt         # the demo document Alice will sign
├── ca/
│   ├── ca.cert.pem            # Acme CA's cert (public)
│   └── ca.key.pem             # Acme CA's private key (kept secret)
├── alice/
│   ├── alice.cert.pem         # Alice's cert (public)
│   ├── alice.key.pem          # Alice's private key (kept secret)
│   └── purchase_order.txt     # local copy of the document
└── bob/
    ├── bob.cert.pem
    └── bob.key.pem
```

The `ca/`, `alice/`, `bob/` folders are listed in `.gitignore` —
generated certs and private keys never get committed.

---

## What the demo proves

The 7 steps in `run.sh`:

| # | Step | Demonstrates |
|---|---|---|
| 1 | Show Alice's certificate | What a Ladhe cert looks like (algorithm OID, issuer, subject) |
| 2 | Show the purchase order | The document being signed |
| 3 | Alice signs the document | One-time signature using her prime decomposition |
| 4 | Alice sends three files to Bob | Document + signature + Alice's cert |
| 5 | Bob verifies Alice's cert against the CA | Cert-chain trust |
| 6 | Bob verifies the document signature | Authenticity & integrity |
| 7 | The tamper test | An attacker changes `$1,250,000` → `$12,500,000`; verify fails immediately |

---

## Manual commands (if you want to run without the script)

Run from `ladhe-rsa/` (one level up from this folder), so Python sees
the `ladhe_*.py` modules.

```bash
cd ladhe-rsa

# Sign a document
python3 ladhe_cert_cli.py sign \
    --subject alice \
    --dir demo/alice \
    --doc demo/alice/purchase_order.txt

# Verify a cert against the CA
python3 ladhe_cert_cli.py verify \
    --cert demo/alice/alice.cert.pem \
    --ca   demo/ca/ca.cert.pem

# Verify a signed document
python3 ladhe_cert_cli.py verify-doc \
    --subject alice \
    --dir demo/alice \
    --doc demo/alice/purchase_order.txt \
    --sig demo/alice/purchase_order.txt.sig
```

---

## Notes on the scheme

- **One-time keys.** Each Ladhe key pair signs exactly one document
  safely. Alice would generate a fresh keypair before signing the next
  document. The Merkle-aggregated many-time variant sketched in the
  paper (§6) is not yet implemented in this reference.
- **Security foundation.** Ladhe signatures reduce to SHA-256 preimage
  resistance — the same foundation as SPHINCS+ and SLH-DSA.
- **Algorithm OID.** `1.3.6.1.4.1.65644.1.1` (IANA-registered to
  LeSecure, 2026-04-23). Visible in the cert's `signature.algorithm_oid`
  field and in `openssl x509 -text` output of the X.509 export.

---

## Reset between runs

`run.sh` cleans up Bob's folder at the start and end of each run, so
re-running the demo is safe. To reset *everything* (regenerate fresh
certs):

```bash
./setup.sh    # uses --force to overwrite
```
