"""
test_security.py
================
Unit tests for the security primitives.

Run with:
    python -m pytest simulator/tests/   (or: python -m unittest)
"""
import unittest

from simulator.security import (
    RootOfTrust, SecureBootError,
    SecureKeyStore, TamperLog,
)


class TestSecureBoot(unittest.TestCase):
    def test_signed_firmware_boots(self):
        rot = RootOfTrust()
        img = rot.sign_firmware(b"hello world", "v1")
        self.assertTrue(rot.verify_firmware(img))
        rot.boot(img)  # should not raise

    def test_tampered_payload_refused(self):
        rot = RootOfTrust()
        img = rot.sign_firmware(b"hello", "v1")
        img.payload = b"goodbye"
        with self.assertRaises(SecureBootError):
            rot.boot(img)

    def test_wrong_rot_refused(self):
        rot_a = RootOfTrust()
        rot_b = RootOfTrust()
        img = rot_a.sign_firmware(b"x", "v1")
        with self.assertRaises(SecureBootError):
            rot_b.boot(img)


class TestKeyStore(unittest.TestCase):
    def test_initial_keys_present(self):
        ks = SecureKeyStore()
        self.assertEqual(len(ks.aes_key), 32)
        self.assertFalse(ks.erased)

    def test_wipe_zeros_keys(self):
        ks = SecureKeyStore()
        ks.crypto_erase()
        self.assertTrue(ks.erased)
        self.assertEqual(ks.aes_key, b"\x00" * 32)
        self.assertEqual(ks.ecdsa_priv, b"\x00" * 32)

    def test_wipe_under_500ms(self):
        ks = SecureKeyStore()
        ks.crypto_erase()
        # In software this is microseconds; we just assert the budget.
        self.assertLess(ks.erase_duration_ms, 500.0)


class TestTamperLog(unittest.TestCase):
    def test_chain_verifies(self):
        log = TamperLog()
        log.append("A", "alpha")
        log.append("B", "beta")
        log.append("C", "gamma")
        self.assertTrue(log.verify())

    def test_edited_entry_breaks_chain(self):
        log = TamperLog()
        log.append("A", "alpha")
        log.append("B", "beta")
        log._entries[0].detail = "FORGED"
        self.assertFalse(log.verify())

    def test_reordered_entry_breaks_chain(self):
        log = TamperLog()
        log.append("A", "alpha")
        log.append("B", "beta")
        log._entries[0], log._entries[1] = log._entries[1], log._entries[0]
        self.assertFalse(log.verify())


if __name__ == "__main__":
    unittest.main()
