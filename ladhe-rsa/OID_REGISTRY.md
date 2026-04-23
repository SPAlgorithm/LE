# Ladhe-RSA Object Identifier (OID) Registry

This file documents the OID arc reserved for LESecure AI / SPAlgorithm
and the algorithm identifiers defined within it for the Ladhe-RSA scheme.

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
1.3.6.1.4.1.65644.1.1      -- id-ladhe-rsa-signature
1.3.6.1.4.1.65644.1.2      -- id-ladhe-rsa-publicKey
1.3.6.1.4.1.65644.2        -- Certificate profiles
1.3.6.1.4.1.65644.2.1      -- id-ladhe-cert-v1
```

## ASN.1 Definitions

```asn1
LESecure-LadheRSA
  { iso(1) identified-organization(3) dod(6) internet(1)
    private(4) enterprise(1) lesecure(65644) }

DEFINITIONS IMPLICIT TAGS ::= BEGIN

-- Root arcs
id-lesecure     OBJECT IDENTIFIER ::= { 1 3 6 1 4 1 65644 }
id-lesec-algs   OBJECT IDENTIFIER ::= { id-lesecure 1 }
id-lesec-certs  OBJECT IDENTIFIER ::= { id-lesecure 2 }

-- Signature algorithm
id-ladhe-rsa-signature  OBJECT IDENTIFIER ::= { id-lesec-algs 1 }

-- Public-key algorithm
id-ladhe-rsa-publicKey  OBJECT IDENTIFIER ::= { id-lesec-algs 2 }

-- Certificate profile
id-ladhe-cert-v1  OBJECT IDENTIFIER ::= { id-lesec-certs 1 }

-- Public key structure
LadheRSAPublicKey ::= SEQUENCE {
    prime       INTEGER,        -- the Ladhe prime P
    commitment  OCTET STRING,   -- SHA-256( salt || encode(witness) )
    salt        OCTET STRING    -- 32-byte random salt
}

-- Signature structure (Fiat-Shamir, 64 rounds)
LadheRSASignature ::= SEQUENCE {
    rounds      INTEGER,        -- number of Sigma rounds (default 64)
    commits     SEQUENCE OF SigmaCommit,
    responses   SEQUENCE OF SigmaResponse
}

SigmaCommit ::= SEQUENCE {
    aCommit  OCTET STRING,   -- H(r || witness_encoding)
    aux      OCTET STRING    -- H(r)
}

SigmaResponse ::= SEQUENCE {
    opening  OCTET STRING,
    salt     OCTET STRING OPTIONAL   -- present iff challenge = 1
}

END
```

## Algorithm Parameters

| Parameter          | Value                          |
|--------------------|--------------------------------|
| Hash function      | SHA-256                        |
| Commitment salt    | 32 bytes (256 bits), random    |
| Fiat-Shamir rounds | 64 (soundness error 2⁻⁶⁴)     |
| Sigma challenge    | 1 bit ∈ {0, 1}                 |
| Witness encoding   | Length-prefixed big-endian     |

## Status

- [x] PEN assigned by IANA (decimal 65644, 2026-04-23)
- [x] OID placeholders resolved throughout this file
- [x] `ladhe_cert.py` `CERT_ALGORITHM` includes the OID
- [ ] Submit algorithm identifier to IETF LAMPS WG for awareness

## References

- IANA PEN registry: https://www.iana.org/assignments/enterprise-numbers/
- RFC 9371: Registration procedures for PENs
- Paper: https://zenodo.org/records/19680322
