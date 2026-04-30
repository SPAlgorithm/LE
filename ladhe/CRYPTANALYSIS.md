# Cryptanalysis Document — Ladhe v1.0

> **Status:** v1 draft, 2026-04-29.
> **Companion to:** `SP_Paper.pdf` (Zenodo DOI 19888480; IACR ePrint
> version in preparation). All claims here should match the paper's
> §4 (Security Analysis); discrepancies should be reported as bugs.
> **Purpose:** explicit threat model, attack-surface enumeration, and
> success criteria for cryptanalysis. We invite the community to find
> issues.
> **Maintainer:** LESecure AI, Inc. — `spalgorithm@gmail.com`.

---

## 1. Why This Document Exists

Ladhe is a candidate compact hash-based one-time signature scheme.
Like every cryptographic scheme, it is only as strong as community
cryptanalysis allows us to claim. This document:

1. States the security notion we make claims about (NQF) and the
   notions we explicitly do **not** claim (EUF-CMA at the one-time
   level).
2. Enumerates known attack vectors, with concrete bounds.
3. Defines what we will accept as evidence of a cryptographic break,
   ahead of time, so the threshold is unambiguous.
4. Identifies open questions where we would value outside analysis.
5. Specifies how to submit a cryptanalytic claim and how credit is
   allocated.

If you find a flaw, we want to hear about it — even if it does not
meet the formal "break" criteria, see §6 and §8.

---

## 2. Security Notion

### 2.1 What We Claim

The Ladhe one-time scheme is **No-Query Forgery (NQF) secure** under
the random oracle model with hash assumption (H1) — preimage
resistance of SHA-256.

**Definition (NQF, paraphrased from paper §4.1):** Given a public key
`(P, h)` produced by the honest KeyGen and access to the random oracle
modelling SHA-256, no PPT adversary can produce a valid signature
`(σ*, m*)` for any `m*` of their choice without making at least
~`q_H` queries to find a preimage of `h`.

**Theorem 1 (paper §4.3):**
```
  Adv^NQF_Ladhe(A) ≤ (q_H + 1) / 2^λ      (classical)
  Adv^NQF_Ladhe(A) ≤ O(q_H² / 2^λ)         (quantum, via Grover)
```
where `λ = 256` for the reference instantiation.

### 2.2 What We Do Not Claim

- **EUF-CMA security at the one-time level.** An adversary that has
  observed even one valid signature obtains the secret primes (the
  signature *is* the witness opening). They can trivially forge any
  further message. This is acknowledged in paper §4.1 and is the
  defining property of the "commitment-and-opening" framing.
- **EUF-CMA security at the many-time level without the Merkle layer.**
  EUF-CMA is recovered only via the Merkle-aggregated construction of
  paper §6, which is currently sketched, not implemented.
- **Side-channel resistance.** The reference implementation does not
  use constant-time arithmetic and does not defend against fault
  injection. See §5.5.
- **Security against breaks of SHA-256.** Ladhe inherits the
  brittleness of SHA-256: if SHA-256 is fundamentally broken (e.g.,
  preimage attacks better than 2^λ), Ladhe falls with it — but so do
  SPHINCS+, SLH-DSA, and every other hash-based scheme. We do not
  claim independence from SHA-256.

### 2.3 Multi-Target Setting

For Q independently generated public keys (paper §4.4):
```
  Adv^{Q-NQF}_Ladhe(A) ≤ Q · (q_H + 1) / 2^λ
```
At λ = 256 and Q = 2^40 (a generous deployment scale), the bound is
2^40 · q_H / 2^256, which remains negligible for realistic q_H.

---

## 3. Foundational Assumptions

| Assumption | Statement | Standard? |
|---|---|---|
| **(H1) Preimage resistance** | Given `h ∈ {0,1}^λ`, finding `x` with `H(x) = h` requires ~`q/2^λ` queries classically and Grover-bounded `q²/2^λ` quantumly | Yes — used in SPHINCS+, SLH-DSA, XMSS |
| **(H2) Collision resistance** | Finding `x ≠ x'` with `H(x) = H(x')` requires ~`2^{λ/2}` queries classically | Yes — used in the many-time Merkle construction |
| **(H3) Random oracle model** | `H` is modelled as a random oracle in proofs | Yes — standard for hash-based signature analysis |

These are exactly the assumptions hash-based schemes have used since
Lamport (1979). Ladhe makes no further assumptions.

---

## 4. Encoding Properties (From Paper §4.2)

The reduction in Theorem 1 relies on two encoding properties:

**Lemma 1 (paper §4.2):** The canonical encoding `enc` is injective
on integer tuples — distinct tuples produce distinct byte strings.
This is required so that the hash commits unambiguously to the
witness W.

**Remark (paper §4.2):** The map `pair_compress` is *not* injective on
the underlying prime tuples. Distinct ascending prime tuples can
yield the same compressed witness W. Example with k=5:
- `(3, 17, 23, 29, 1009)` → `W = (20, 52, 1009)`
- `(7, 13, 23, 29, 1009)` → `W = (20, 52, 1009)`

This is by design and **does not weaken security**: the public key h
commits to a specific W (via Lemma 1's injectivity of `enc` on W),
not to a specific prime tuple. Any prime tuple opening to that W
verifies identically. Cryptanalytically, an attacker still must find
*some* preimage of h — the multi-to-one map of primes onto W is
irrelevant to the search difficulty.

---

## 5. Attack Surface

We enumerate every attack class we have considered. If you find a
class we have not enumerated, please report it (see §8).

### 5.1 Generic Preimage Attacks

The dominant attack at cryptographic parameter sizes.

| Method | Cost | Status at λ=256 |
|---|---|---|
| Direct enumeration of inputs | Θ(2^λ) classical | Infeasible (10^77 hash evaluations) |
| Grover quantum search | Θ(2^{λ/2}) quantum | Infeasible (10^38 quantum operations; far beyond any projected quantum hardware) |

**Bound:** Theorem 1 establishes that NQF security reduces to this
attack class. Any improvement on generic preimage attacks against
SHA-256 immediately weakens Ladhe by the same factor.

### 5.2 Structural Search (Direct Prime-Decomposition Enumeration)

The attacker enumerates valid k-tuples of distinct odd primes summing
to P, hashing each and checking against h.

For a 256-bit P:
- π(P) ≈ 2^{248} (prime number theorem)
- Number of candidate k-tuples: bounded by `binom(π(P), k)`, with the
  sum-constraint imposing roughly `O(1/P)` density factor
- Combined with the hash check, the candidate space exceeds 2^λ

**Bound:** Cost ≥ 2^λ at cryptographic P. No advantage over generic
preimage search.

**Caveat:** Below λ = 96 or so, structural enumeration becomes
tractable. This is *expected* — those parameter sizes are
sub-cryptographic (see §6 "Tier Reference"). A break at sub-256-bit
parameters demonstrates the brute-force baseline; it does not refute
the security claim at λ = 256.

### 5.3 Pair-Compression Collisions

An attacker finds two distinct W tuples that hash to the same h.

This is **second-preimage on SHA-256**, which is also bounded by
2^λ classically (and 2^{λ/2} quantum via Grover). No structural
advantage.

**Bound:** Cost ≥ 2^λ at SHA-256 second-preimage hardness.

### 5.4 Multi-Target Attacks

Given Q independent Ladhe public keys, the adversary attacks all of
them in parallel. By a union bound (§2.3):

```
  Cost = 2^λ / Q
```

At Q = 2^40 deployments and λ = 256, the bound is 2^216 — still
infeasible by many orders of magnitude.

**Caveat:** If Ladhe deployment scales to Q ≈ 2^128 keys (e.g., one
key per IoT device worldwide for centuries), the multi-target bound
becomes 2^128, which is the *threshold* of cryptographic security.
This is far beyond any realistic deployment scenario, but worth
flagging.

### 5.5 Side-Channel Attacks

**Out of scope for v1.0. Explicitly flagged.**

- **Timing attacks.** The reference Python implementation does not
  use constant-time arithmetic. Variable-time prime-checking, big
  integer operations, and conditional branches in `_search_decomposition`
  could leak information about the witness during signing.
- **Fault-injection attacks.** No defenses against bit-flips in
  signing or verification flow.
- **Memory side-channels.** Python's GC + buffer caching may leak
  witness material via memory state.

These are addressed in Phase I production-hardening (NSF SBIR work).
Until then, deploy only in environments without side-channel
adversaries (e.g., offline build servers signing release artifacts).

### 5.6 Key-Reuse Attacks

The Ladhe one-time scheme is **catastrophically vulnerable to key
reuse** by definition. After the legitimate signature is published,
the secret primes are exposed. Anyone observing two valid signatures
under the same key trivially:
1. Confirms the secret from either signature
2. Forges any further message

This is the defining property of "one-time" in the scheme name.
The recommended deployment is: one key per artifact, generated fresh,
discarded after the single signature.

For applications requiring repeated signing under one identity, use
the many-time Merkle-aggregated variant (paper §6, not yet implemented).

### 5.7 Implementation Attacks

The reference implementation is **research-grade, not
production-grade**:
- No constant-time arithmetic
- No memory zeroization after key use
- No protection against malicious input on the verifier path
  (though the verifier does check structural validity)
- No formal review of the random number source for KeyGen

Production deployment requires either:
- Phase I third-party security audit (Trail of Bits / NCC Group),
  budgeted at $120K
- A complete from-scratch reimplementation in C or Rust with
  cryptographic engineering best practices

---

## 6. What Would Constitute a Break

We commit, in advance, to what we will accept as a cryptographic
break. The bar is concrete, tiered by parameter size, and matches the
CLI's tier output.

### 6.1 Tier-Specific Success Criteria

| Tier | Bits | Criterion | Implication |
|---|---|---|---|
| Sanity-check | < 64 | Brute force succeeds (expected) | Confirms baseline; not a break |
| Educational | 64–127 | Brute force succeeds; advanced search succeeds | Tractable at parameters below the security target; not a break |
| Pre-cryptographic | 128–255 | Method that beats generic preimage by ≥ 2^16 | Hard but not yet a break of the 256-bit security claim |
| **BRONZE (security target)** | **256** | **Method that recovers a witness with `o(2^{λ/2}) = o(2^128)` work classically, OR `o(2^{λ/4}) = o(2^64)` work quantumly** | **Real cryptanalytic break** |
| Silver | 257–1023 | Same with proof of scalability | Stronger result |
| Gold | 1024–2047 | Same | Even stronger |
| Platinum | ≥ 2048 | Same | Extreme parameters |

### 6.2 What "method" means

We will accept any of:
- **A complete witness recovery** — given `(P, h)`, output primes
  satisfying the verification predicate, in time below the bound.
- **A signature forgery** — given `(P, h)` for an honestly-generated
  key (with no signatures observed), produce `(σ*, m*)` such that
  `Verify(m*, σ*, (P, h)) = 1`, in time below the bound. This is
  equivalent to witness recovery for the one-time scheme.
- **A reduction** — show that NQF security can be reduced to a
  problem that is asymptotically easier than SHA-256 preimage. This
  would be a structural break even without an explicit attack.

### 6.3 Out of scope (does not count as a break)

- **Side-channel attacks** on the reference implementation
  (acknowledged in §5.5, addressed in Phase I).
- **Brute force at sub-cryptographic parameters** (sanity-check tier
  through pre-cryptographic; expected behavior).
- **Implementation bugs in the reference Python** (welcome as bug
  reports, not cryptanalysis).
- **Attacks requiring key reuse or signature observation** at the
  one-time level (the scheme is explicitly one-time; this is by
  design).
- **Attacks on the many-time Merkle variant** before it is
  implemented (we make no claims yet).

---

## 7. Open Cryptanalytic Questions

Areas where we explicitly invite outside analysis:

1. **Tightness of the encoding-injectivity lemma.** Lemma 1 is proven
   in §4.2, but is the byte-level encoding truly free of structural
   leaks that could aid preimage search? E.g., does the length-prefix
   field correlate with the secret in a way that reduces the
   effective search space?

2. **Bit-size scaling of the random-trial KeyGen.** The keygen does
   random trial. Are there parameter regimes where the random-trial
   success probability deviates significantly from naive expectation?

3. **Many-time variant security.** The Merkle-aggregated construction
   of §6 is sketched. Does the standard XMSS/SPHINCS+ argument apply
   directly, or does Ladhe's witness structure introduce subtle issues?

4. **Side-channel exposure.** What information does a timing
   side-channel actually leak during KeyGen? Is the leakage enough
   to recover the witness, or only to reduce the search space?

5. **Multi-target tightness.** Is the union-bound multi-target
   reduction tight, or is there a tighter target-collision-resistance
   argument?

6. **Quantum bounds.** The quantum bound `O(q² / 2^λ)` in Theorem 1
   is from Grover-optimality of preimage. Are there quantum
   amplitude-amplification tricks that improve this?

7. **Comparison to compact hash-based competitors.** Are there
   schemes (besides SPHINCS+ / SLH-DSA / Lamport) with comparable or
   better parameter-to-security tradeoffs?

---

## 8. Submitting a Cryptanalytic Claim

We accept submissions in any form, but the following format helps us
adjudicate quickly.

### 8.1 Required information

```
1. Target bit size (the bits parameter passed to challenge generator)
2. The (P, h) you attacked (as printed by the challenge command)
3. Your attack output:
   - For witness recovery: the prime tuple (p_1, p_2, ..., p_k)
   - For forgery: the signature (σ*) and message (m*)
4. Method description — at least 1 paragraph. Cite any tools used.
5. Time and resources used to attack (wall clock, CPU/GPU/quantum, memory)
6. Verifiability — anything we need to reproduce the attack
```

### 8.2 Submission channels

- **GitHub issues** (preferred for public): https://github.com/SPAlgorithm/LE/issues
- **Email** (for private/sensitive disclosures): spalgorithm@gmail.com

### 8.3 Verification

We verify submissions by:
1. Independently running our implementation's verifier on the
   submitted witness/forgery
2. Re-deriving the attack at our end (if reproducible from the
   description)
3. Cross-checking with the cryptographic-advisor consultant
   (engaged Phase I)

### 8.4 Credit and reward

Per CLI tier output:

| Tier | Reward |
|---|---|
| Sanity-check / Educational / Pre-cryptographic | Acknowledgment in changelog |
| BRONZE (security target) | Named in public "challenges solved" log |
| SILVER | Named acknowledgment in v2 of the paper |
| GOLD | Coauthorship offer on cryptanalysis follow-on paper |
| PLATINUM | Public retraction of the scheme + paper coauthorship |

We commit to public acknowledgment of any accepted analysis with the
attribution the submitter prefers (real name, pseudonym, anonymous
"researcher who wishes to remain anonymous").

We commit to public retraction within 30 days of confirming a BRONZE
or higher tier break.

---

## 9. Process and Communication

- **Active monitoring:** GitHub issues are monitored daily.
- **Response time:** non-urgent submissions, ~3–7 business days.
- **Sensitive-disclosure path:** for breaks at BRONZE+ tier, please
  email first; we will coordinate disclosure timing with you.
- **No bounty payment in cash.** Credit and coauthorship are the
  reward structure (matches academic norms).

---

## 10. References

- Paper: SP_Paper.pdf — Zenodo DOI 19888480
  (https://zenodo.org/records/19888480). IACR ePrint version in
  preparation.
- Open-source implementation: https://github.com/SPAlgorithm/LE
- Challenge generator CLI: `python3 ladhe.py challenge [bits]`
- IANA registry: PEN 65644 (registered April 2026)

### Related work touched on above

- Lamport, L. (1979). "Constructing Digital Signatures from a One-Way
  Function."
- Bernstein et al. (2019). "SPHINCS+ — Submission to the NIST
  Post-Quantum Cryptography Project."
- NIST FIPS 204 (ML-DSA) and FIPS 205 (SLH-DSA), 2024.
- Vinogradov, I.M. (1937). "Some theorems on the theory of prime
  numbers."

---

*Cryptanalysis welcome. We are not asking for endorsement. We are
asking for scrutiny.*
