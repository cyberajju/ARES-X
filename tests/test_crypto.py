"""
Comprehensive tests for the ARES-X cryptographic primitives module.
"""

import unittest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto import aes_gcm, key_exchange, hkdf, hmac_auth, utils


class TestAESGCM(unittest.TestCase):
    """Test AES-256-GCM encryption and decryption."""

    def test_encrypt_decrypt_round_trip(self):
        """Encrypt then decrypt should return original plaintext."""
        key = utils.generate_random_bytes(32)
        plaintext = b"Hello, ARES-X secure messaging!"

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext)

        self.assertEqual(len(nonce), 12)
        self.assertEqual(len(tag), 16)
        self.assertNotEqual(ciphertext, plaintext)

        decrypted = aes_gcm.decrypt(key, nonce, ciphertext, tag)
        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_empty_plaintext(self):
        """Should handle empty plaintext."""
        key = utils.generate_random_bytes(32)
        plaintext = b""

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext)
        decrypted = aes_gcm.decrypt(key, nonce, ciphertext, tag)
        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_large_plaintext(self):
        """Should handle large payloads."""
        key = utils.generate_random_bytes(32)
        plaintext = utils.generate_random_bytes(64 * 1024)

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext)
        decrypted = aes_gcm.decrypt(key, nonce, ciphertext, tag)
        self.assertEqual(decrypted, plaintext)

    def test_wrong_key_fails(self):
        """Decryption with wrong key should fail."""
        key = utils.generate_random_bytes(32)
        wrong_key = utils.generate_random_bytes(32)
        plaintext = b"Secret data"

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext)

        with self.assertRaises(RuntimeError):
            aes_gcm.decrypt(wrong_key, nonce, ciphertext, tag)

    def test_wrong_tag_fails(self):
        """Decryption with tampered tag should fail."""
        key = utils.generate_random_bytes(32)
        plaintext = b"Secret data"

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext)
        tampered_tag = bytes([b ^ 0xFF for b in tag])

        with self.assertRaises(RuntimeError):
            aes_gcm.decrypt(key, nonce, ciphertext, tampered_tag)

    def test_aad_mismatch_fails(self):
        """Decryption with wrong AAD should fail."""
        key = utils.generate_random_bytes(32)
        plaintext = b"Secret data"
        aad = b"authenticated header"

        nonce, ciphertext, tag = aes_gcm.encrypt(key, plaintext, aad=aad)

        # Correct AAD works
        decrypted = aes_gcm.decrypt(key, nonce, ciphertext, tag, aad=aad)
        self.assertEqual(decrypted, plaintext)

        # Wrong AAD fails
        with self.assertRaises(RuntimeError):
            aes_gcm.decrypt(key, nonce, ciphertext, tag, aad=b"wrong header")

        # No AAD fails
        with self.assertRaises(RuntimeError):
            aes_gcm.decrypt(key, nonce, ciphertext, tag, aad=b"")

    def test_different_nonces_produce_different_ciphertext(self):
        """Same plaintext with different nonces should produce different ciphertext."""
        key = utils.generate_random_bytes(32)
        plaintext = b"Same message encrypted twice"

        nonce1, ct1, tag1 = aes_gcm.encrypt(key, plaintext)
        nonce2, ct2, tag2 = aes_gcm.encrypt(key, plaintext)

        # Nonces should be different (random)
        self.assertNotEqual(nonce1, nonce2)
        # Ciphertexts should be different
        self.assertNotEqual(ct1, ct2)

    def test_invalid_key_size(self):
        """Should reject keys that are not 32 bytes."""
        with self.assertRaises(ValueError):
            aes_gcm.encrypt(b"short", b"data")

        with self.assertRaises(ValueError):
            aes_gcm.decrypt(b"short", b"x" * 12, b"data", b"x" * 16)


class TestX25519(unittest.TestCase):
    """Test X25519 key exchange."""

    def test_key_generation_produces_32_byte_keys(self):
        """Generated keys should be 32 bytes each."""
        kp = key_exchange.X25519KeyPair.generate()
        self.assertEqual(len(kp.public_key), 32)
        self.assertEqual(len(kp.private_key), 32)

    def test_different_key_pairs_are_different(self):
        """Two generated key pairs should be different."""
        kp1 = key_exchange.X25519KeyPair.generate()
        kp2 = key_exchange.X25519KeyPair.generate()
        self.assertNotEqual(kp1.public_key, kp2.public_key)
        self.assertNotEqual(kp1.private_key, kp2.private_key)

    def test_shared_secret_agreement(self):
        """Both parties should derive the same shared secret."""
        alice = key_exchange.X25519KeyPair.generate()
        bob = key_exchange.X25519KeyPair.generate()

        # Alice computes shared secret with Bob's public key
        secret_alice = key_exchange.compute_shared_secret(alice, bob.public_key)
        # Bob computes shared secret with Alice's public key
        secret_bob = key_exchange.compute_shared_secret(bob, alice.public_key)

        self.assertEqual(len(secret_alice), 32)
        self.assertEqual(secret_alice, secret_bob)

    def test_different_key_pairs_produce_different_secrets(self):
        """Different key pairs should produce different shared secrets."""
        alice = key_exchange.X25519KeyPair.generate()
        bob = key_exchange.X25519KeyPair.generate()
        charlie = key_exchange.X25519KeyPair.generate()

        secret_ab = key_exchange.compute_shared_secret(alice, bob.public_key)
        secret_ac = key_exchange.compute_shared_secret(alice, charlie.public_key)

        self.assertNotEqual(secret_ab, secret_ac)

    def test_from_private_key(self):
        """Should recreate consistent key pair from private key."""
        kp1 = key_exchange.X25519KeyPair.generate()
        kp2 = key_exchange.X25519KeyPair.from_private_key(kp1.private_key)

        self.assertEqual(kp1.public_key, kp2.public_key)

    def test_invalid_key_size(self):
        """Should reject keys of incorrect size."""
        with self.assertRaises(ValueError):
            key_exchange.X25519KeyPair.from_private_key(b"short")

        kp = key_exchange.X25519KeyPair.generate()
        with self.assertRaises(ValueError):
            key_exchange.compute_shared_secret(kp, b"short_pub_key")


class TestHKDF(unittest.TestCase):
    """Test HKDF key derivation."""

    def test_deterministic_output(self):
        """Same inputs should produce same output."""
        ikm = b"input keying material"
        salt = b"salt value"
        info = b"context info"

        key1 = hkdf.derive_key(ikm, salt, info, 32)
        key2 = hkdf.derive_key(ikm, salt, info, 32)

        self.assertEqual(key1, key2)

    def test_correct_output_length(self):
        """Output should match requested length."""
        ikm = b"input keying material"
        salt = b"salt"
        info = b"info"

        for length in [16, 32, 48, 64, 128]:
            key = hkdf.derive_key(ikm, salt, info, length)
            self.assertEqual(len(key), length)

    def test_different_info_produces_different_keys(self):
        """Different info values should produce different keys."""
        ikm = b"input keying material"
        salt = b"salt"

        key1 = hkdf.derive_key(ikm, salt, b"purpose-1", 32)
        key2 = hkdf.derive_key(ikm, salt, b"purpose-2", 32)

        self.assertNotEqual(key1, key2)

    def test_different_salt_produces_different_keys(self):
        """Different salts should produce different keys."""
        ikm = b"input keying material"
        info = b"info"

        key1 = hkdf.derive_key(ikm, b"salt-1", info, 32)
        key2 = hkdf.derive_key(ikm, b"salt-2", info, 32)

        self.assertNotEqual(key1, key2)

    def test_extract_produces_hash_length_output(self):
        """Extract should produce output of hash digest length."""
        prk = hkdf.hkdf_extract(b"salt", b"ikm", "sha256")
        self.assertEqual(len(prk), 32)  # SHA-256 output

        prk = hkdf.hkdf_extract(b"salt", b"ikm", "sha512")
        self.assertEqual(len(prk), 64)  # SHA-512 output

    def test_expand_max_length(self):
        """Expand should reject requests exceeding max length."""
        prk = hkdf.hkdf_extract(b"salt", b"ikm")
        with self.assertRaises(ValueError):
            hkdf.hkdf_expand(prk, b"info", 255 * 32 + 1)

    def test_empty_salt(self):
        """Should handle empty salt (uses zero-filled salt)."""
        ikm = b"input keying material"
        key = hkdf.derive_key(ikm, b"", b"info", 32)
        self.assertEqual(len(key), 32)


class TestHMACAuth(unittest.TestCase):
    """Test HMAC-SHA512 message authentication."""

    def test_sign_verify_works(self):
        """Sign then verify should succeed."""
        key = utils.generate_random_bytes(32)
        message = b"Authenticated message"

        signature = hmac_auth.sign(key, message)
        self.assertEqual(len(signature), 64)  # SHA-512 output

        self.assertTrue(hmac_auth.verify(key, message, signature))

    def test_tampered_message_fails(self):
        """Verification should fail if message is tampered."""
        key = utils.generate_random_bytes(32)
        message = b"Original message"

        signature = hmac_auth.sign(key, message)

        self.assertFalse(hmac_auth.verify(key, b"Tampered message", signature))

    def test_tampered_signature_fails(self):
        """Verification should fail if signature is tampered."""
        key = utils.generate_random_bytes(32)
        message = b"Authenticated message"

        signature = hmac_auth.sign(key, message)
        tampered_sig = bytes([b ^ 0x01 for b in signature])

        self.assertFalse(hmac_auth.verify(key, message, tampered_sig))

    def test_wrong_key_fails(self):
        """Verification should fail with wrong key."""
        key1 = utils.generate_random_bytes(32)
        key2 = utils.generate_random_bytes(32)
        message = b"Secret message"

        signature = hmac_auth.sign(key1, message)

        self.assertFalse(hmac_auth.verify(key2, message, signature))

    def test_deterministic_signature(self):
        """Same key and message should produce same signature."""
        key = b"fixed-key-for-testing-purposes!!"
        message = b"Consistent message"

        sig1 = hmac_auth.sign(key, message)
        sig2 = hmac_auth.sign(key, message)

        self.assertEqual(sig1, sig2)


class TestUtils(unittest.TestCase):
    """Test crypto utility functions."""

    def test_random_bytes_length(self):
        """Should generate correct number of random bytes."""
        for n in [0, 1, 16, 32, 64, 256]:
            self.assertEqual(len(utils.generate_random_bytes(n)), n)

    def test_random_bytes_different(self):
        """Two random generations should be different."""
        a = utils.generate_random_bytes(32)
        b = utils.generate_random_bytes(32)
        self.assertNotEqual(a, b)

    def test_constant_time_compare(self):
        """Constant-time compare should work correctly."""
        self.assertTrue(utils.constant_time_compare(b"abc", b"abc"))
        self.assertFalse(utils.constant_time_compare(b"abc", b"abd"))
        self.assertFalse(utils.constant_time_compare(b"abc", b"abcd"))

    def test_base64_round_trip(self):
        """Base64 encode then decode should return original."""
        data = utils.generate_random_bytes(32)
        encoded = utils.bytes_to_base64(data)
        decoded = utils.base64_to_bytes(encoded)
        self.assertEqual(data, decoded)

    def test_xor_bytes(self):
        """XOR should work correctly."""
        a = b"\x01\x02\x03\x04"
        b_val = b"\x05\x06\x07\x08"
        result = utils.xor_bytes(a, b_val)
        self.assertEqual(result, b"\x04\x04\x04\x0c")

    def test_xor_bytes_length_mismatch(self):
        """XOR should raise on length mismatch."""
        with self.assertRaises(ValueError):
            utils.xor_bytes(b"\x01\x02", b"\x01")


if __name__ == "__main__":
    unittest.main()
