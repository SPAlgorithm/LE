# Algorithm Identifier Specification: Ladhe-RSA Signature Scheme

**Draft** — SPAlgorithm, April 2026  
**Authors**: Shubham Ladhe, Pankaj Ladhe  
**Contact**: spalgorithm@gmail.com  
**Paper**: https://zenodo.org/records/19680322  
**Implementation**: https://github.com/SPAlgorithm/LE

---

## Abstract

This document specifies the algorithm identifiers, key formats, and
signature formats for the Ladhe-RSA signature scheme, a candidate
post-quantum signature scheme based on the Ladhe Decomposition Problem
(LDP). It follows the style of IETF algorithm identifier specifications
(cf. RFC 8410, RFC 8420) to facilitate future standardisation efforts.

This is a **research draft**. The hardness of LDP is unproven and
awaits community cryptanalysis. This specification is published to
enable interoperability among experimental implementations and to
invite formal review.

---

## 1. Background

The Ladhe Decomposition Problem (LDP) asks: given a prime P and a
hash commitment h = H(salt || encode(a, b, c)), find a triple
(a, b, c) of positive integers such that a + b + c = P and the
commitment matches. The Ladhe-RSA signature scheme is a Fiat-Shamir
transform of a Sigma protocol whose soundness relies on LDP hardness.

Full mathematical treatment: see the companion paper (§2–§4).

---

## 2. OID Assignments

IANA Private Enterprise Number **65644** assigned 2026-04-23 to
LESecure AI / SPAlgorithm.

```
id-ladhe-rsa-signature  ::=  1.3.6.1.4.1.65644.1.1
id-ladhe-rsa-publicKey  ::=  1.3.6.1.4.1.65644.1.2
id-ladhe-cert-v1        ::=  1.3.6.1.4.1.65644.2.1
```

Full OID arc and ASN.1 module: see [OID_REGISTRY.md](OID_REGISTRY.md).

---

## 3. Public Key Format

A Ladhe-RSA public key consists of three values:

| Field        | Type        | Description                                    |
|--------------|-------------|------------------------------------------------|
| `prime`      | INTEGER     | The Ladhe prime P                              |
| `commitment` | OCTET STRING| SHA-256(salt \|\| encode(witness)), 32 bytes   |
| `salt`       | OCTET STRING| 32-byte random salt used in the commitment     |

### 3.1 Witness Encoding

The witness (a, b, c) is encoded as follows before hashing:

```
encoded := byte(len(parts))       -- 1 byte: number of parts (3 or 4)
        || for each part p:
             uint16be(byte_len(p)) -- 2 bytes: length of p in bytes
          || bytes_be(p)           -- p in big-endian, minimal length
```

### 3.2 ASN.1

```asn1
LadheRSAPublicKey ::= SEQUENCE {
    prime       INTEGER,
    commitment  OCTET STRING (SIZE(32)),
    salt        OCTET STRING (SIZE(32))
}
```

### 3.3 SubjectPublicKeyInfo (for X.509 use, once OID is finalised)

```asn1
SubjectPublicKeyInfo  ::=  SEQUENCE {
    algorithm   AlgorithmIdentifier {
                    algorithm  id-ladhe-rsa-publicKey,
                    parameters absent
                },
    subjectPublicKey  BIT STRING  -- DER of LadheRSAPublicKey
}
```

---

## 4. Signature Format

A Ladhe-RSA signature is the result of a 64-round Fiat-Shamir
transform of the Sigma protocol.

### 4.1 Sigma Round

Each round consists of:

- **Commitment**: (a_commit, aux) where  
  `a_commit = SHA-256(r || encode(witness))`  
  `aux      = SHA-256(r)`  
  and r is a 32-byte random blinding value.

- **Challenge**: a single bit c ∈ {0, 1}, derived deterministically
  from `SHA-256(pk || message || a_commit_0 || aux_0 || ... )`.

- **Response**:
  - If c = 0: reveal r. Verifier checks `SHA-256(r) = aux`.
  - If c = 1: reveal `r XOR encode(witness)` and the commitment salt.
    Verifier checks the opening length against the public key.

### 4.2 Fiat-Shamir Challenge Derivation

Challenge bits are derived from a SHA-256 hash expanded via a
counter-based PRF:

```
seed  = SHA-256( pk_bytes || uint32be(len(msg)) || msg
               || a_commit_0 || aux_0 || ... || a_commit_63 || aux_63 )

block_i = SHA-256(seed || uint32be(i))

challenges = bits(block_0) || bits(block_1) || ...   (first 64 bits)
```

### 4.3 Binary Wire Format

```
signature_bytes :=
    uint32be(rounds)                   -- 4 bytes, default 64
    for i in 0..rounds-1:
        uint16be(len(a_commit_i))      -- 2 bytes
        a_commit_i                     -- 32 bytes
        uint16be(len(aux_i))           -- 2 bytes
        aux_i                          -- 32 bytes
    for i in 0..rounds-1:
        uint32be(len(opening_i))       -- 4 bytes
        opening_i
        uint16be(len(salt_i))          -- 2 bytes (0 if challenge=0)
        salt_i                         -- 32 bytes, or absent
```

### 4.4 ASN.1

```asn1
LadheRSASignature ::= SEQUENCE {
    rounds     INTEGER DEFAULT 64,
    commits    SEQUENCE OF SigmaCommit,
    responses  SEQUENCE OF SigmaResponse
}

SigmaCommit ::= SEQUENCE {
    aCommit  OCTET STRING,
    aux      OCTET STRING
}

SigmaResponse ::= SEQUENCE {
    opening  OCTET STRING,
    salt     OCTET STRING OPTIONAL
}
```

---

## 5. Security Parameters

| Parameter           | Research value | Target production value |
|---------------------|---------------|------------------------|
| Prime bit-length    | 8–30 bits     | ≥ 2048 bits            |
| Fiat-Shamir rounds  | 64            | 128+ (≥ 128-bit sound) |
| Hash function       | SHA-256       | SHA-256 or SHA-3-256   |
| Salt length         | 256 bits      | 256 bits               |
| Soundness error     | 2⁻⁶⁴          | 2⁻¹²⁸                  |

---

## 6. Known Limitations and Open Problems

1. **LDP hardness** — no reduction from a classically or quantumly
   hard problem is known. Community cryptanalysis is invited.

2. **Simplified Sigma protocol** — the challenge-1 branch reveals the
   commitment salt, which at toy parameter sizes enables offline
   brute-force of the witness. A production scheme must use
   MPC-in-the-head (IKOS 2007) or an equivalent ZK compiler.

3. **No formal ZK proof** — the scheme is not proven zero-knowledge.
   The paper (§7) identifies this as future work.

4. **Parameter sizes** — the empirical dataset (LadheConjecture.txt)
   uses 8–30 bit primes. Real security requires at least 2048-bit
   primes; generation tooling for large primes is future work.

---

## 7. IANA Considerations

IANA Private Enterprise Number **65644** was assigned on 2026-04-23
under RFC 9371 procedures. All OID values in §2 are now concrete.
This document will be submitted to the IETF LAMPS Working Group
for awareness once community cryptanalysis has begun.

---

## 8. References

- **[LDP26]** Shubham Ladhe, Pankaj Ladhe. "The Ladhe Decomposition
  Problem: A Candidate Post-Quantum Hardness Assumption on Additive
  Prime Structure, with an Identification Scheme." 2026.
  https://zenodo.org/records/19680322

- **[RFC8410]** S. Josefsson, J. Schaad. "Algorithm Identifiers for
  Ed25519, Ed448, X25519, and X448." RFC 8410, 2018.

- **[RFC9371]** M. Cotton. "Registration Procedures for Private
  Enterprise Numbers (PENs)." RFC 9371, 2023.

- **[IKOS07]** Y. Ishai, E. Kushilevitz, R. Ostrovsky, A. Sahai.
  "Zero-knowledge from secure multiparty computation." STOC 2007.

- **[FS87]** A. Fiat, A. Shamir. "How to Prove Yourself: Practical
  Solutions to Identification and Signature Problems." CRYPTO 1986.
