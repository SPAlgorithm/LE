# Ladhe Roadmap

This document tracks completed milestones and the path toward
production-grade deployment. Dates on future items are target
dates, not commitments — they are gated on community cryptanalysis
holding up, security audits completing, and (in some cases)
funding or pilot engagements materialising.

---

## Completed

| Date        | Milestone |
|-------------|-----------|
| 2026-04-22  | Paper published on Zenodo ([10.5281/zenodo.19888480](https://zenodo.org/records/19888480)) |
| 2026-04-22  | Reference implementation released (github.com/SPAlgorithm/LE) |
| 2026-04-22  | Empirical dataset released (1,620+ entries) |
| 2026-04-23  | IANA Private Enterprise Number **65644** registered to LeSecure |
| 2026-04-23  | OIDs formally assigned: `id-ladhe-signature`, `id-ladhe-publicKey`, `id-ladhe-cert-v1` |
| 2026-04-23  | X.509 DER/PEM certificate export shipped; `openssl x509 -text` parses Ladhe certs |

---

## Near-term (next 3–6 months)

Target window: **May 2026 – October 2026**

- [ ] **Submit IACR ePrint** — once approved, update citation in README
- [ ] **Post to IETF LAMPS working group** — awareness, not action request ([ALGORITHM_SPEC.md](ALGORITHM_SPEC.md) is the draft)
- [ ] **Academic outreach** — email cryptanalysis targets at MIT CSAIL, CMU CyLab, Georgia Tech, other PQC-active labs
- [ ] **First external cryptanalysis attempts** — enabled by the challenge generator in `ladhe_rsa.generate_ldp_challenge`
- [ ] **Conference submissions** — PQCrypto 2027, CT-RSA 2027, ACNS 2027 (deadlines mid-2026)
- [ ] **NSF SBIR Phase I** — outline ready; $300K / 6 months to fund formal security analysis and production hardening
- [ ] **First friendly pilot** — unpaid proof-of-concept with a warm enterprise or IoT contact

---

## Medium-term (6–18 months)

Target window: **October 2026 – October 2027**

Gated on:
- External cryptanalysis having surveyed LDP for 6+ months with no break
- NSF SBIR or equivalent grant awarded
- At least one completed friendly pilot with public case study

Steps:

- [ ] **OpenSSL provider plugin** — implement Ladhe as an OpenSSL 3.0+ provider so standard tools (`openssl verify`, Python `cryptography`, Go `crypto/x509`, curl, nginx) can cryptographically verify signatures, not just parse the structure. Fastest path: fork `oqsprovider` (Open Quantum Safe) and add Ladhe alongside NIST PQC algorithms. Estimated: 2–4 months of C development.
- [ ] **Many-time extension** — ship the Merkle-aggregated many-time variant sketched in `SP_Paper_v3.pdf` §6. Each leaf is a one-time Ladhe key pair; signatures include the one-time signature plus a Merkle authentication path.
- [ ] **Efficient KeyGen algorithm** — replace random-trial decomposition search (`O((ln P)^k · k · (log P)^3)`) with a directly-constructive algorithm. This is the main barrier to cryptographic parameter sizes.
- [ ] **Constant-time / side-channel hardening** — replace non-constant-time primitives; add memory hygiene and timing-attack resistance.
- [ ] **Third-party security audit** — engage Trail of Bits, NCC Group, or Cure53 for formal review of the hardened implementation.
- [ ] **First paid pilot** — 8–12 week enterprise PKI or IoT deployment; joint case study.
- [ ] **NSF SBIR Phase II** — $2M / 24 months, gated on successful Phase I.

---

## Long-term (18 months – 3+ years)

Target window: **2027 – 2029+**

Gated on:
- Medium-term items above completing successfully
- A formal security proof (or stronger reduction) from the research community
- Sustained enterprise adoption

Steps:

- [ ] **IETF Internet-Draft → RFC** — formalise the algorithm identifier specification. Calendar time dominates: 12–18 months of list review, working-group adoption, multiple revisions, IESG review. Only makes sense once cryptanalysis has held up and the scheme has real deployments.
- [ ] **Formal security proof** — reduce LDP to a known-hard problem, or establish concrete security bounds relative to established assumptions.
- [ ] **Standards publication** — algorithm identifier IETF RFC published.

### Optional (only for browser-trusted public SSL)

- [ ] **CA/Browser Forum adoption** — submit for inclusion in web PKI. Only relevant if targeting browser-trusted certificates (Safari, Chrome, Firefox). Not needed for enterprise private PKI or IoT closed ecosystems, which is our primary deployment target. Timeline: 2+ years beyond RFC publication.

---

## Check-in dates

- **2026-06-23** (2 months): progress review — ePrint approved? LAMPS engagement? Any cryptanalysis attempts?
- **2026-10-23** (6 months): cryptanalysis window midpoint — any breaks found? First pilots started?
- **2027-04-23** (12 months): medium-term kick-off — ready to start OpenSSL provider work? Funding secured?

---

## Explicit gates

Each tier of work depends on the previous tier succeeding. Specifically:

```
Step 1: X.509 DER encoding                    ✅ DONE
   │
   ├── gated on: nothing — purely engineering
   ▼
Step 2: OpenSSL provider plugin
   │
   ├── gated on: cryptanalysis surviving + funding secured
   ▼
Step 3: IETF Internet-Draft → RFC
   │
   ├── gated on: real deployments + formal proof (or strong reduction)
   ▼
Step 4: CA/Browser Forum (OPTIONAL, only for public SSL)
   │
   └── gated on: RFC published + browser vendor interest
```

We explicitly reserve the right to not pursue Step 4 if the
enterprise-PKI and IoT markets prove sufficient — which is the
honest default assumption given how rarely new signature algorithms
achieve browser trust (last was Ed25519, which took roughly a decade
post-publication).

---

## How to contribute

If any of the items above overlap with your research or engineering
interests, please open an issue or email us. The shortest path from
"interesting idea" to "landed milestone" almost always runs through
a specific person volunteering to drive one step.

- Paper & cryptanalysis: [github.com/SPAlgorithm/LE/issues](https://github.com/SPAlgorithm/LE/issues)
- Engineering (OpenSSL provider, ZK upgrade, etc.): pull requests welcome
- Pilots & commercial engagement: spalgorithm@gmail.com
