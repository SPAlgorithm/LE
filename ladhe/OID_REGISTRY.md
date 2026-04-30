# Ladhe Object Identifier (OID) Registry

This file documents the OID arc reserved for LESecure AI / SPAlgorithm
and the algorithm identifiers defined within it for the Ladhe signature
scheme (v3).

## OID Arc

IANA Private Enterprise Number (PEN) assigned 2026-04-23.

- **PEN:** 65644
- **Registered organisation:** LeSecure
- **Contact:** Pankaj S Ladhe
- **Registry:** https://www.iana.org/assignments/enterprise-numbers/

```
1.3.6.1.4.1.65644          -- LESecure AI / SPAlgorithm root arc
```

## Algorithm Identifiers

```
1.3.6.1.4.1.65644.1        -- Cryptographic algorithms
1.3.6.1.4.1.65644.1.1      -- id-ladhe-signature
1.3.6.1.4.1.65644.1.2      -- id-ladhe-publicKey
1.3.6.1.4.1.65644.2        -- Certificate profiles
1.3.6.1.4.1.65644.2.1      -- id-ladhe-cert-v1
```

## ASN.1 Definitions

```asn1
LESecure-Ladhe
  { iso(1) identified-organization(3) dod(6) internet(1)
    private(4) enterprise(1) lesecure(65644) }

DEFINITIONS IMPLICIT TAGS ::= BEGIN

-- Root arcs
id-lesecure     OBJECT IDENTIFIER ::= { 1 3 6 1 4 1 65644 }
id-lesec-algs   OBJECT IDENTIFIER ::= { id-lesecure 1 }
id-lesec-certs  OBJECT IDENTIFIER ::= { id-lesecure 2 }

-- Signature algorithm
id-ladhe-signature  OBJECT IDENTIFIER ::= { id-lesec-algs 1 }

-- Public-key algorithm
id-ladhe-publicKey  OBJECT IDENTIFIER ::= { id-lesec-algs 2 }

-- Certificate profile
id-ladhe-cert-v1  OBJECT IDENTIFIER ::= { id-lesec-certs 1 }

-- Public key structure (v3, hash-based)
LadhePublicKey ::= SEQUENCE {
    prime  INTEGER,             -- the public prime P
    h      OCTET STRING         -- SHA-256 of enc(pair_compress(primes))
}                               -- 32 bytes for SHA-256

-- Signature structure (v3, one-time, reveals the private decomposition)
LadheSignature ::= SEQUENCE {
    primes   SEQUENCE OF INTEGER,   -- the k distinct odd primes,
                                    -- sorted ascending, with k odd
    message  OCTET STRING           -- the signed message
}

END
```

## Algorithm Parameters

| Parameter        | Value                                      |
|------------------|--------------------------------------------|
| Hash function    | SHA-256 (32-byte output)                   |
| Security param κ | 256 bits                                   |
| k                | 3, 5, or 7 (odd)                           |
| Witness encoding | enc(W) per `ladhe.encode_W`            |
| Classical attack | 2²⁵⁶ preimage brute-force                  |
| Quantum attack   | 2¹²⁸ Grover on hash                        |
| Lifetime per key | **One signature** (signing twice leaks sk) |

## Status

- [x] PEN assigned by IANA (decimal 65644, 2026-04-23)
- [x] OID placeholders resolved throughout this file
- [x] `ladhe_cert.py` and `ladhe_x509.py` use these OIDs end-to-end
- [x] ASN.1 module updated to v3 (hash-based, no Sigma protocol)
- [ ] Submit algorithm identifier to IETF LAMPS WG for awareness

## References

- IANA PEN registry: https://www.iana.org/assignments/enterprise-numbers/
- RFC 9371: Registration procedures for PENs
- Paper (v3): `SP_Paper.pdf` (this repo); Zenodo: https://zenodo.org/records/19888480
