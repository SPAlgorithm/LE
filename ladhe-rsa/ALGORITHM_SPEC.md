# Algorithm Identifier Specification: Ladhe Signature Scheme (v3)

**Draft** — SPAlgorithm, April 2026
**Authors**: Shubham Ladhe, Pankaj Ladhe
**Contact**: spalgorithm@gmail.com
**Paper**: `SP_Paper_v3.pdf` (this folder); Zenodo: https://zenodo.org/records/19888480
**Implementation**: https://github.com/SPAlgorithm/LE

---

## Abstract

This document specifies the algorithm identifiers, key formats, and
signature formats for the **Ladhe signature scheme**, a one-time
hash-based signature within the post-quantum hash-based family
(alongside SPHINCS+ and Lamport). Security reduces to preimage
resistance of SHA-256. The specification follows the style of IETF
algorithm identifier drafts (cf. RFC 8410, RFC 8420) to facilitate
future standardisation efforts.

This is a **research draft**. Community cryptanalysis has not yet
occurred. The specification is published to enable interoperability
among experimental implementations and to invite formal review.

---

## 1. Background

The Ladhe scheme is defined in the companion paper
(`SP_Paper_v3.pdf`). Informally:

- A **public key** is `(P, h)` where `P` is a prime and
  `h = SHA-256(enc(W))` for a compressed witness `W`.
- A **private key** is a sorted tuple
  `(p_1 < p_2 < ... < p_k)` of distinct odd primes with `k` odd
  and `sum(p_i) = P`.
- The compressed witness `W` is formed by **indexed-pair compression**
  of the private primes.
- A **signature** reveals the private decomposition once; the scheme
  is one-time (Merkle aggregation for many-time is sketched in
  paper §6).

The **Ladhe Decomposition Problem (LDP)** — given `(P, h)`, recover a
valid prime decomposition — reduces to SHA-256 preimage resistance
(paper §4, Proposition 1).

---

## 2. OID Assignments

IANA Private Enterprise Number **65644** assigned 2026-04-23 to
LeSecure.

```
id-ladhe-signature  ::=  1.3.6.1.4.1.65644.1.1
id-ladhe-publicKey  ::=  1.3.6.1.4.1.65644.1.2
id-ladhe-cert-v1    ::=  1.3.6.1.4.1.65644.2.1
```

Full OID arc: see [OID_REGISTRY.md](OID_REGISTRY.md).

---

## 3. Public Key Format

```asn1
LadhePublicKey ::= SEQUENCE {
    prime  INTEGER,            -- the public prime P
    h      OCTET STRING        -- SHA-256 of the compressed witness
                               -- (32 bytes for SHA-256)
}
```

For X.509 use:

```asn1
SubjectPublicKeyInfo  ::=  SEQUENCE {
    algorithm   AlgorithmIdentifier {
                    algorithm  id-ladhe-publicKey,
                    parameters NULL
                },
    subjectPublicKey  BIT STRING    -- DER of LadhePublicKey
}
```

---

## 4. Indexed-Pair Compression and Encoding

### 4.1 Indexed-pair compression

Given a sorted tuple `(p_1, p_2, ..., p_k)` with `k` odd:

```
W = ( p_1 + p_2, p_3 + p_4, ..., p_{k-2} + p_{k-1}, p_k )
```

`W` has `m = (k+1)/2` components. The first `m-1` are even (sums of
two odd primes); the last is odd (the unpaired prime `p_k`).

### 4.2 Canonical encoding

```
enc(W) :=  0x01                        -- version byte
        || uint8(m)                    -- 1 byte: tuple length
        || for each w_i in W:
               uint16be(byte_len(w_i)) -- 2 bytes
            || w_i                     -- minimal big-endian of w_i
```

### 4.3 Hash commitment

```
h = SHA-256( enc(W) )
```

Output `h` is 32 bytes.

---

## 5. Signature Format

A Ladhe one-time signature reveals the private decomposition.

```asn1
LadheSignature ::= SEQUENCE {
    primes   SEQUENCE OF INTEGER,    -- the k private odd primes,
                                     -- sorted ascending
    message  OCTET STRING            -- the signed message
}
```

### 5.1 Binary wire format (reference implementation)

```
signature_bytes :=
    uint8(k)                      -- 1 byte: number of primes (odd)
    for i in 0..k-1:
        uint16be(byte_len(p_i))   -- 2 bytes
        p_i_big_endian
    uint32be(message_length)      -- 4 bytes
    message_bytes
```

---

## 6. Verification

```
Verify(pk = (P, h), m, sigma):
    1. parse sigma into (p_1, ..., p_k, m')
    2. reject if m != m'
    3. reject if k < 3 or k is even
    4. reject if any p_i is not prime (Miller-Rabin)
    5. reject if the p_i are not all distinct and ascending
    6. reject if sum(p_i) != P
    7. compute W by indexed-pair compression of (p_1, ..., p_k)
    8. reject if SHA-256(enc(W)) != h
    9. otherwise, accept
```

---

## 7. Security Parameters

| Parameter        | Reference value | Target production       |
|------------------|-----------------|-------------------------|
| Security param κ | 256 bits        | 256                     |
| Hash function    | SHA-256         | SHA-256 or SHA3-256     |
| Prime P bit-len  | small (toy)     | ≥ 2048 (open problem)   |
| k (odd)          | 3, 5, or 7      | unchanged               |
| Preimage attack  | 2²⁵⁶ classical / 2¹²⁸ Grover | same |

---

## 8. Known Limitations (Summary)

1. **One-time only.** A fresh key pair must be used for each message.
   Merkle-aggregation for many-time is planned (paper §6).
2. **Slow KeyGen at cryptographic parameter sizes.** Random-trial
   decomposition search; efficient alternatives are open.
3. **Community cryptanalysis has not yet occurred.**
4. **Not side-channel or constant-time hardened.** Research
   reference only.

---

## 9. IANA Considerations

IANA Private Enterprise Number **65644** was assigned on 2026-04-23
under RFC 9371 procedures. All OID values in §2 are concrete.
This specification may be submitted to the IETF LAMPS Working Group
for awareness once community cryptanalysis begins.

---

## 10. References

- **[LadheV3]** Shubham Ladhe, Pankaj Ladhe. "Ladhe Signatures:
  Compact Hash-Based Signatures from Additive Prime Decompositions."
  2026 — this folder's `SP_Paper_v3.pdf`.
- **[RFC8410]** S. Josefsson, J. Schaad. "Algorithm Identifiers for
  Ed25519, Ed448, X25519, and X448." RFC 8410, 2018.
- **[RFC9371]** M. Cotton. "Registration Procedures for Private
  Enterprise Numbers (PENs)." RFC 9371, 2023.
- **[SPHINCS+]** D. J. Bernstein et al. "The SPHINCS+ Signature
  Framework." ACM CCS 2019.
- **[Vinogradov]** I. M. Vinogradov, "Representation of an Odd
  Number as a Sum of Three Primes," 1937. Helfgott (2013) removed
  the sufficiency condition.
