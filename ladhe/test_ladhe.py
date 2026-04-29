"""Unit tests for the Ladhe signature scheme (v3)."""

import unittest

import ladhe as LR


class TestPrimality(unittest.TestCase):
    def test_small_primes(self):
        for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 97, 101):
            self.assertTrue(LR.is_prime(p), f"{p} should be prime")

    def test_composites(self):
        for n in (4, 6, 8, 9, 15, 21, 25, 100, 1001):
            self.assertFalse(LR.is_prime(n), f"{n} should be composite")

    def test_large_prime(self):
        # 2^61 - 1 is a Mersenne prime
        self.assertTrue(LR.is_prime((1 << 61) - 1))


class TestPairCompression(unittest.TestCase):
    def test_k3(self):
        self.assertEqual(LR.pair_compress((3, 7, 157)), (10, 157))

    def test_k5(self):
        self.assertEqual(
            LR.pair_compress((3, 5, 11, 41, 107)),
            (8, 52, 107),
        )

    def test_rejects_even_k(self):
        with self.assertRaises(ValueError):
            LR.pair_compress((3, 5))


class TestEncoding(unittest.TestCase):
    def test_encode_deterministic(self):
        self.assertEqual(
            LR.encode_W((10, 157)),
            LR.encode_W((10, 157)),
        )

    def test_encode_distinct(self):
        self.assertNotEqual(
            LR.encode_W((10, 157)),
            LR.encode_W((157, 10)),
        )


class TestKeyGenAndSignVerify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pk, cls.sk = LR.keygen(up1=3)

    def test_keygen_structure(self):
        self.assertIsInstance(self.pk.prime, int)
        self.assertEqual(len(self.pk.h), LR.LAMBDA_BYTES)
        self.assertGreaterEqual(len(self.sk.primes), 3)
        self.assertEqual(len(self.sk.primes) % 2, 1)

    def test_keygen_primes_sum_to_P(self):
        self.assertEqual(sum(self.sk.primes), self.pk.prime)

    def test_keygen_primes_distinct_and_sorted(self):
        self.assertEqual(len(set(self.sk.primes)), len(self.sk.primes))
        self.assertEqual(list(self.sk.primes), sorted(self.sk.primes))

    def test_keygen_all_primes(self):
        for p in self.sk.primes:
            self.assertTrue(LR.is_prime(p))

    def test_h_matches_compressed_hash(self):
        import hashlib
        W = LR.pair_compress(self.sk.primes)
        h = hashlib.sha256(LR.encode_W(W)).digest()
        self.assertEqual(self.pk.h, h)

    def test_sign_verify_roundtrip(self):
        msg = b"hello Ladhe"
        sig = LR.sign(msg, self.sk)
        self.assertTrue(LR.verify(msg, sig, self.pk))

    def test_tampered_message_fails(self):
        msg = b"hello"
        sig = LR.sign(msg, self.sk)
        self.assertFalse(LR.verify(b"HELLO", sig, self.pk))

    def test_tampered_primes_fails(self):
        msg = b"hello"
        sig = LR.sign(msg, self.sk)
        bad_primes = list(sig.primes)
        bad_primes[0] += 2
        bad_sig = LR.Signature(primes=tuple(bad_primes), message=msg)
        self.assertFalse(LR.verify(msg, bad_sig, self.pk))

    def test_signature_encoding_roundtrip(self):
        msg = b"roundtrip"
        sig = LR.sign(msg, self.sk)
        decoded = LR.Signature.decode(sig.encode())
        self.assertEqual(decoded.primes, sig.primes)
        self.assertEqual(decoded.message, sig.message)
        self.assertTrue(LR.verify(msg, decoded, self.pk))


class TestLDPChallenge(unittest.TestCase):
    def test_generate_challenge(self):
        P, h = LR.generate_ldp_challenge(bits=16)
        self.assertTrue(LR.is_prime(P))
        self.assertEqual(len(h), LR.LAMBDA_BYTES)


if __name__ == "__main__":
    unittest.main()
