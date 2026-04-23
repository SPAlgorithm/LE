"""Unit tests for ladhe_x509 — X.509 DER/PEM export and round-trip."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import ladhe_rsa as LR
import ladhe_cert as LC
import ladhe_x509 as LX


class TestLadheX509(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ca_cert, cls.ca_sk = LC.create_ca(
            "Test CA", validity_days=3650, min_prime_bits=20
        )
        cls.leaf_pk, cls.leaf_sk = LR.keygen(min_prime_bits=20)
        cls.leaf_cert = LC.issue_certificate(
            cls.ca_cert, cls.ca_sk, "subject@example.com",
            cls.leaf_pk, validity_days=365,
        )

    def test_round_trip_der(self):
        der = LX.cert_to_x509_der(self.leaf_cert)
        recovered = LX.cert_from_x509_der(der)
        self.assertEqual(recovered.subject, self.leaf_cert.subject)
        self.assertEqual(recovered.issuer,  self.leaf_cert.issuer)
        self.assertEqual(recovered.signature["value"],
                         self.leaf_cert.signature["value"])
        self.assertEqual(recovered.signature["algorithm_oid"],
                         LX.OID_LADHE_SIG)
        self.assertEqual(recovered.public_key["algorithm_oid"],
                         LX.OID_LADHE_PK)

    def test_round_trip_pem(self):
        pem = LX.cert_to_x509_pem(self.leaf_cert)
        self.assertTrue(pem.startswith("-----BEGIN CERTIFICATE-----"))
        self.assertTrue(pem.rstrip().endswith("-----END CERTIFICATE-----"))
        recovered = LX.cert_from_x509_pem(pem)
        self.assertEqual(recovered.subject, self.leaf_cert.subject)

    def test_oids_present_in_der(self):
        der = LX.cert_to_x509_der(self.leaf_cert)
        # 1.3.6.1.4.1.65644.1.1 DER-encoded
        sig_oid_der = bytes.fromhex("060a2b0601040184806c0101")
        # 1.3.6.1.4.1.65644.1.2 DER-encoded
        pk_oid_der  = bytes.fromhex("060a2b0601040184806c0102")
        self.assertIn(sig_oid_der, der, "signature OID not present in DER")
        self.assertIn(pk_oid_der,  der, "public-key OID not present in DER")

    def test_openssl_can_parse(self):
        with tempfile.NamedTemporaryFile(suffix=".pem", mode="w",
                                         delete=False) as f:
            f.write(LX.cert_to_x509_pem(self.leaf_cert))
            pem_path = f.name
        try:
            r = subprocess.run(
                ["openssl", "x509", "-in", pem_path, "-noout", "-subject"],
                capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"openssl failed: {r.stderr}")
            self.assertIn("subject@example.com", r.stdout)

            r = subprocess.run(
                ["openssl", "x509", "-in", pem_path, "-noout", "-issuer"],
                capture_output=True, text=True)
            self.assertIn("Test CA", r.stdout)
        finally:
            Path(pem_path).unlink()


if __name__ == "__main__":
    unittest.main()
