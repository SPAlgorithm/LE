"""
test_ladhe_rsa.py — Tests for the Ladhe-RSA reference
implementation.

Run with:
    python -m unittest test_ladhe_rsa
    # or:
    python test_ladhe_rsa.py
"""

from __future__ import annotations

import random
import unittest
from pathlib import Path

import ladhe_rsa as LR


class TestPrimality(unittest.TestCase):
    def test_small_primes(self):
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 97]:
            self.assertTrue(LR.is_prime(p))

    def test_composites(self):
        for n in [0, 1, 4, 6, 8, 9, 10, 15, 100, 221]:
            self.assertFalse(LR.is_prime(n))

    def test_large_prime(self):
        # 2^127 - 1 is a Mersenne prime
        self.assertTrue(LR.is_prime((1 << 127) - 1))


class TestDatasetLoading(unittest.TestCase):
    def test_load_entries(self):
        entries = LR.load_dataset()
        self.assertGreater(len(entries), 1000)

    def test_entries_valid(self):
        entries = LR.load_dataset()
        valid = LR.filter_valid(entries)
        self.assertGreater(len(valid), 0)
        for e in valid[:20]:
            self.assertEqual(sum(e.parts), e.prime)
            self.assertTrue(LR.is_prime(e.prime))


class TestHashCommitment(unittest.TestCase):
    def test_determinism(self):
        salt = b"\x00" * 32
        w = (2, 3, 6)
        h1 = LR.hash_commitment(w, salt)
        h2 = LR.hash_commitment(w, salt)
        self.assertEqual(h1, h2)

    def test_different_salts_different_commits(self):
        w = (2, 3, 6)
        h1 = LR.hash_commitment(w, b"\x00" * 32)
        h2 = LR.hash_commitment(w, b"\x01" * 32)
        self.assertNotEqual(h1, h2)

    def test_rejects_wrong_salt_length(self):
        with self.assertRaises(ValueError):
            LR.hash_commitment((2, 3, 6), b"\x00" * 16)


class TestKeyGeneration(unittest.TestCase):
    def test_keygen_from_entry(self):
        # Known entry 40: 3467 = 360 + 501 + 2606
        entries = LR.filter_valid(LR.load_dataset())
        # Find entry with prime 3467 if available
        matching = [e for e in entries if e.prime == 3467]
        self.assertTrue(matching, "entry 40 (3467) not found in dataset")
        pk, sk = LR.keygen_from_entry(matching[0])
        self.assertEqual(pk.prime, sk.prime)
        self.assertEqual(pk.salt, sk.salt)
        # Commitment must reopen to the witness
        self.assertEqual(
            LR.hash_commitment(sk.witness, sk.salt),
            pk.commitment,
        )

    def test_keygen_random(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        self.assertEqual(pk.prime, sk.prime)
        self.assertEqual(sum(sk.witness), pk.prime)
        self.assertTrue(LR.is_prime(pk.prime))


class TestSigmaProtocol(unittest.TestCase):
    def test_honest_prover_accepts(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        ok = LR.run_identification(pk, sk, rounds=16)
        self.assertTrue(ok)

    def test_challenge_0_aux_check(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        commit, state = LR.sigma_commit(sk)
        resp = LR.sigma_response(sk, commit, state, 0)
        w_enc_len = len(LR._encode_witness(sk.witness))
        self.assertTrue(
            LR.sigma_verify(pk, commit, 0, resp, w_enc_len)
        )

    def test_wrong_salt_fails(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        commit, state = LR.sigma_commit(sk)
        resp = LR.sigma_response(sk, commit, state, 1)
        # Corrupt the salt
        bad = LR.SigmaResponse(opening=resp.opening, salt=b"\xff" * 32)
        w_enc_len = len(LR._encode_witness(sk.witness))
        self.assertFalse(
            LR.sigma_verify(pk, commit, 1, bad, w_enc_len)
        )


class TestSignatures(unittest.TestCase):
    def test_sign_verify_roundtrip(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        msg = b"test message"
        sig = LR.sign(msg, sk, pk)
        self.assertTrue(LR.verify(msg, sig, pk))

    def test_tampered_message_fails(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        sig = LR.sign(b"original", sk, pk)
        self.assertFalse(LR.verify(b"tampered", sig, pk))

    def test_tampered_signature_fails(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        sig = LR.sign(b"original", sk, pk)
        # Flip a byte in the first commit
        bad_commit = LR.SigmaCommit(
            a_commit=b"\x00" + sig.commits[0].a_commit[1:],
            aux=sig.commits[0].aux,
        )
        bad_sig = LR.Signature(
            commits=(bad_commit,) + sig.commits[1:],
            responses=sig.responses,
        )
        self.assertFalse(LR.verify(b"original", bad_sig, pk))

    def test_signature_encoding_roundtrip(self):
        pk, sk = LR.keygen(min_prime_bits=20)
        sig = LR.sign(b"hello", sk, pk)
        encoded = sig.encode()
        self.assertIsInstance(encoded, bytes)
        self.assertGreater(len(encoded), 0)


class TestLDPChallenge(unittest.TestCase):
    def test_challenge_structure(self):
        P, h, s = LR.generate_ldp_challenge(bits=24)
        self.assertTrue(LR.is_prime(P))
        self.assertEqual(len(s), LR.COMMITMENT_SALT_BYTES)
        self.assertEqual(len(h), 32)   # SHA-256 output


class TestPublicKeyEncoding(unittest.TestCase):
    def test_encode_stable(self):
        pk, _ = LR.keygen(min_prime_bits=20)
        e1 = pk.encode()
        e2 = pk.encode()
        self.assertEqual(e1, e2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
