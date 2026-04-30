# Ladhe Cryptanalysis Bounty

> Public challenges for the Ladhe one-time signature scheme.
> Find a witness, submit, get credit.
> **Honest framing:** Ladhe is a candidate scheme; community
> cryptanalysis is the whole point of this directory.

---

## TL;DR

```bash
# 1. Pick a challenge
cat manifest.json | python3 -m json.tool | head -40

# 2. Try to break it
python3 brute_force_baseline.py manifest.json sanity-32

# 3. Verify your witness
python3 verify_solution.py manifest.json sanity-32 <p_1> <p_2> <p_3>

# 4. Submit
#    GitHub:  https://github.com/SPAlgorithm/LE/issues
#    Email:   spalgorithm@gmail.com
```

For the formal threat model and what counts as a break, read
**[../CRYPTANALYSIS.md](../CRYPTANALYSIS.md)** first. It is the canonical
cryptographic specification of the bounty.

---

## What's in this directory

| File | Purpose |
|---|---|
| `manifest.json` | Public challenges. Each is a `(P, h)` pair at a specific tier. **Stable** — once published, IDs and `(P, h)` values do not change. |
| `verify_solution.py` | Stdlib-only verifier. Given a candidate prime tuple, runs all six structural and hash checks. |
| `brute_force_baseline.py` | Reference brute-force solver. Demonstrates the baseline attack work; succeeds at sub-cryptographic tiers, infeasible at BRONZE+. |
| `generate_manifest.py` | Maintainer tool — used to refresh the manifest. Committed publicly so anyone can audit how challenges are generated (no fixed seeds, no hidden choices). |
| `.witnesses/` | Internal witness vault. **Gitignored** — not in the public repo. |

---

## Tier overview

| Tier | Bits | What a break means | Reward |
|---|---|---|---|
| Sanity check | 32 | Brute force baseline; expected | Acknowledgment in changelog |
| Educational | 64–96 | Tractable with serious effort; below security target | Acknowledgment in changelog |
| Pre-cryptographic | 128 | Hard but not yet a contradiction of the security claim | Acknowledgment in changelog |
| **BRONZE (security target)** | **256** | **Real cryptanalytic result** | **Named in 'challenges solved' log + v2 paper acknowledgment** |
| Silver | 512+ | Stronger result | Coauthorship offer (cryptanalysis follow-on) |
| Gold | 1024+ | Stronger still | Coauthorship offer |
| Platinum | 2048+ | Extreme | Public retraction + paper coauthorship |

The current `manifest.json` ships challenges at the first 4 tiers
(sanity, educational, pre-crypto, bronze). Higher-tier challenges
can be generated on request; KeyGen latency at 1024+ bits is
significant.

---

## How to participate

### Step 1 — Read the threat model

Read **[../CRYPTANALYSIS.md](../CRYPTANALYSIS.md)**. Specifically:
- §2 (Security notion)
- §5 (Attack surface)
- §6 (What would constitute a break)
- §8 (Submitting a claim)

Submissions that don't meet the formal break criteria can still
be submitted and acknowledged, but they will not be tier-rewarded.

### Step 2 — Pick a challenge

```bash
cat manifest.json
```

Each challenge has:
- `id` — stable identifier (e.g., `bronze-256`)
- `tier` — SANITY_CHECK / EDUCATIONAL / PRE_CRYPTOGRAPHIC / BRONZE / etc.
- `bits` — target bit size (matches the CLI's `challenge` argument)
- `P` — the public prime
- `h_hex` — the hash commitment (SHA-256 of the encoded compressed witness)
- `purpose` — what this challenge is for
- `reward` — what credit a successful break earns

### Step 3 — Find a witness

A witness is a tuple `(p_1 < p_2 < ... < p_k)` of distinct odd
primes with `k ∈ {3, 5, 7}` such that:

```
sum(primes) == P
SHA-256(encode(pair_compress(primes))) == h
```

You can use the provided `brute_force_baseline.py` to demonstrate
the baseline attack. Or write your own (preferred — that's what
cryptanalysis means).

### Step 4 — Verify locally

Before submitting, run the verifier on your candidate:

```bash
python3 verify_solution.py manifest.json <id> <p_1> <p_2> ... <p_k>
```

If it prints **PASS** in green, you have a valid witness. If it
prints **FAIL** with a reason, fix it before submitting.

### Step 5 — Submit

**GitHub issue (preferred for public claims):**
https://github.com/SPAlgorithm/LE/issues

Include:
- Challenge ID and `(P, h)` you attacked
- The prime tuple you found
- Brief description of your method
- Time and resources used (wall clock, CPU/GPU/quantum, memory)
- How you'd like to be credited (real name, pseudonym, anonymous)

**Email (private/sensitive disclosures):**
spalgorithm@gmail.com — for breaks at BRONZE+ tier where you'd
prefer coordinated disclosure timing.

---

## Reproducibility

These challenges are stable. Once published, the `manifest.json`
contents do not change. If a challenge is solved, we add a
`solved` field to the entry but do not modify `P` or `h_hex`.

If you need a *fresh* challenge of your own (e.g., for testing
your solver across multiple instances), use:

```bash
cd ..
python3 ladhe.py challenge 64
```

This generates a one-off challenge that is *not* tracked in this
directory's manifest.

---

## What does NOT count as a break

To save everyone time, here's the explicit "not a break" list:

- **Brute force at sub-cryptographic parameter sizes.** The
  baseline solver in this directory will eventually solve at
  bits=32 or 64 — that's the expected baseline, documented in
  `CRYPTANALYSIS.md §5.2`.
- **Side-channel attacks on the reference Python implementation.**
  Acknowledged out-of-scope in `CRYPTANALYSIS.md §5.5`. Will be
  addressed in Phase I third-party audit.
- **Bug reports in the reference code** (welcome as GitHub issues
  but not cryptanalysis).
- **Attacks requiring observation of multiple signatures under one
  key.** The scheme is one-time by design. Multi-time security is
  recovered via Merkle aggregation (paper §6, not yet implemented).
- **Attacks on the many-time variant** before it's implemented.
  We make no claims yet about its security.

---

## What DOES count as a break

For the precise success criteria, see `CRYPTANALYSIS.md §6`. In
brief, at the **BRONZE tier (256-bit)**:

A method that recovers a witness for `(P, h)` from the manifest's
`bronze-256` challenge in:
- **`o(2^128)` work classically**, OR
- **`o(2^64)` work quantum**

with the work documented (or the witness itself produced).

A successful BRONZE break implies one of:
- A structural weakness in the encoding or pair-compression
- A weakness in SHA-256's preimage resistance (which would also
  break SPHINCS+ and SLH-DSA)
- A novel cryptanalytic technique we haven't anticipated

Any of these is a publishable result. We commit to public
acknowledgment within 30 days of confirmation.

---

## Credit policy

We do not pay cash bounties. The reward structure matches academic
cryptanalysis norms:

- **Public credit** in the format you prefer (real name, pseudonym,
  or "researcher who wishes to remain anonymous").
- **Named acknowledgment** in v2 of the paper for substantive
  contributions.
- **Coauthorship offer** for breaks that materially shape the next
  version of the scheme (typically Silver tier and above, but at
  our discretion).
- **Public retraction commitment** within 30 days for confirmed
  BRONZE+ breaks.

We are not asking for endorsement. We are asking for scrutiny.

---

## Honest caveats

1. **The bounty is new.** This is v1 of the kit, alongside v1 of
   the scheme. Workflow may evolve based on your feedback.
2. **No SLA on response times.** Non-urgent submissions: we aim
   for 3–7 business days. Urgent BRONZE+ disclosures: same day if
   we are notified by email.
3. **Paper revisions in flight.** The scheme's paper is currently
   under preparation for IACR ePrint. The Zenodo deposit is the
   canonical citation today; an ePrint version will be added when
   accepted. The scheme content does not change between
   formulations.
4. **Verifier authoritative.** If `verify_solution.py` says PASS,
   we treat the submission as a valid witness. If it says FAIL,
   we will not adjudicate further — fix the FAIL reason and
   resubmit.
5. **Reproducibility expected.** We may ask you to walk us
   through your method. Methods that cannot be reproduced or
   described in detail will be acknowledged but not
   tier-rewarded.

---

## Contact

- GitHub: https://github.com/SPAlgorithm/LE/issues
- Email: spalgorithm@gmail.com
- Paper: https://zenodo.org/records/19888480
- Maintainer: LESecure AI, Inc.

---

*Cryptanalysis welcome.*
