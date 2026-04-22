# Ladhe-RSA Object Identifier (OID) Registry

This file documents the OID arc reserved for SPAlgorithm and the
algorithm identifiers defined within it for the Ladhe-RSA scheme.

## OID Arc

IANA Private Enterprise Number (PEN) application submitted 2026-04-22.
Request ID: **PHII-QH8-T48** — pending assignment.

Once the PEN is assigned, replace `<PEN>` below with the integer value.

```
1.3.6.1.4.1.<PEN>          -- SPAlgorithm root arc
```

## Algorithm Identifiers

```
1.3.6.1.4.1.<PEN>.1        -- SPAlgorithm cryptographic algorithms
1.3.6.1.4.1.<PEN>.1.1      -- id-ladhe-rsa-signature
1.3.6.1.4.1.<PEN>.1.2      -- id-ladhe-rsa-publicKey
1.3.6.1.4.1.<PEN>.2        -- SPAlgorithm certificate profiles
1.3.6.1.4.1.<PEN>.2.1      -- id-ladhe-cert-v1
```

## ASN.1 Definitions (draft)

The following ASN.1 module will be finalised once the PEN is assigned.

```asn1
SPAlgorithm-LadheRSA
  { iso(1) identified-organization(3) dod(6) internet(1)
    private(4) enterprise(1) spalgorithm(<PEN>) }

DEFINITIONS IMPLICIT TAGS ::= BEGIN

-- Root arcs
id-spalgorithm  OBJECT IDENTIFIER ::= { 1 3 6 1 4 1 <PEN> }
id-spalg-algs   OBJECT IDENTIFIER ::= { id-spalgorithm 1 }
id-spalg-certs  OBJECT IDENTIFIER ::= { id-spalgorithm 2 }

-- Signature algorithm
id-ladhe-rsa-signature  OBJECT IDENTIFIER ::= { id-spalg-algs 1 }

-- Public-key algorithm
id-ladhe-rsa-publicKey  OBJECT IDENTIFIER ::= { id-spalg-algs 2 }

-- Certificate profile
id-ladhe-cert-v1  OBJECT IDENTIFIER ::= { id-spalg-certs 1 }

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

- [ ] PEN assigned by IANA (pending — request PHII-QH8-T48)
- [ ] Replace `<PEN>` placeholder throughout this file
- [ ] Update `ladhe_cert.py` `CERT_ALGORITHM` string to include OID
- [ ] Submit algorithm identifier to IETF LAMPS WG for awareness

## References

- IANA PEN registry: https://www.iana.org/assignments/enterprise-numbers/
- RFC 9371: Registration procedures for PENs
- Paper: https://zenodo.org/records/19680322
