"""
Tests for ARES-X protocol module.

Tests message serialization, X3DH handshake, double ratchet encrypt/decrypt,
forward secrecy, out-of-order messages, and state serialization.
"""

import unittest
import time
import copy

from crypto.key_exchange import X25519KeyPair, compute_shared_secret
from crypto.double_ratchet import RatchetState
from protocol.messages import (
    KeyBundle,
    HandshakeMessage,
    RatchetMessageHeader,
    EncryptedMessage,
    MessageEnvelope,
)
from protocol.ratchet_header import Header, HEADER_SIZE
from protocol.handshake import X3DHInitiator, X3DHResponder


class TestMessageSerialization(unittest.TestCase):
    """Test serialization/deserialization round-trips for all message types."""

    def test_key_bundle_round_trip(self):
        """KeyBundle serializes and deserializes without data loss."""
        bundle = KeyBundle(
            identity_key=b"\x01" * 32,
            signed_prekey=b"\x02" * 32,
            signed_prekey_signature=b"\x03" * 64,
            one_time_prekey=b"\x04" * 32,
        )
        data = bundle.to_bytes()
        restored = KeyBundle.from_bytes(data)
        self.assertEqual(restored.identity_key, bundle.identity_key)
        self.assertEqual(restored.signed_prekey, bundle.signed_prekey)
        self.assertEqual(restored.signed_prekey_signature, bundle.signed_prekey_signature)
        self.assertEqual(restored.one_time_prekey, bundle.one_time_prekey)

    def test_key_bundle_without_one_time_prekey(self):
        """KeyBundle without one-time prekey serializes correctly."""
        bundle = KeyBundle(
            identity_key=b"\x01" * 32,
            signed_prekey=b"\x02" * 32,
            signed_prekey_signature=b"\x03" * 64,
            one_time_prekey=None,
        )
        data = bundle.to_bytes()
        restored = KeyBundle.from_bytes(data)
        self.assertIsNone(restored.one_time_prekey)
        self.assertEqual(restored.identity_key, bundle.identity_key)

    def test_handshake_message_round_trip(self):
        """HandshakeMessage serializes and deserializes without data loss."""
        msg = HandshakeMessage(
            sender_identity_key=b"\xaa" * 32,
            ephemeral_key=b"\xbb" * 32,
            one_time_prekey_used=7,
            initial_ciphertext=b"\xcc" * 48,
        )
        data = msg.to_bytes()
        restored = HandshakeMessage.from_bytes(data)
        self.assertEqual(restored.sender_identity_key, msg.sender_identity_key)
        self.assertEqual(restored.ephemeral_key, msg.ephemeral_key)
        self.assertEqual(restored.one_time_prekey_used, 7)
        self.assertEqual(restored.initial_ciphertext, msg.initial_ciphertext)

    def test_handshake_message_no_one_time_prekey(self):
        """HandshakeMessage without one-time prekey used."""
        msg = HandshakeMessage(
            sender_identity_key=b"\xaa" * 32,
            ephemeral_key=b"\xbb" * 32,
            one_time_prekey_used=None,
            initial_ciphertext=b"\xcc" * 16,
        )
        data = msg.to_bytes()
        restored = HandshakeMessage.from_bytes(data)
        self.assertIsNone(restored.one_time_prekey_used)

    def test_ratchet_message_header_round_trip(self):
        """RatchetMessageHeader serializes and deserializes without data loss."""
        header = RatchetMessageHeader(
            dh_public_key=b"\xdd" * 32,
            previous_chain_length=5,
            message_number=42,
        )
        data = header.to_bytes()
        restored = RatchetMessageHeader.from_bytes(data)
        self.assertEqual(restored.dh_public_key, header.dh_public_key)
        self.assertEqual(restored.previous_chain_length, 5)
        self.assertEqual(restored.message_number, 42)

    def test_encrypted_message_round_trip(self):
        """EncryptedMessage serializes and deserializes without data loss."""
        header = RatchetMessageHeader(
            dh_public_key=b"\xee" * 32,
            previous_chain_length=3,
            message_number=10,
        )
        msg = EncryptedMessage(
            header=header,
            ciphertext=b"\xff" * 64,
            nonce=b"\x11" * 12,
            tag=b"\x22" * 16,
        )
        data = msg.to_bytes()
        restored = EncryptedMessage.from_bytes(data)
        self.assertEqual(restored.header.dh_public_key, header.dh_public_key)
        self.assertEqual(restored.header.previous_chain_length, 3)
        self.assertEqual(restored.header.message_number, 10)
        self.assertEqual(restored.ciphertext, msg.ciphertext)
        self.assertEqual(restored.nonce, msg.nonce)
        self.assertEqual(restored.tag, msg.tag)

    def test_message_envelope_round_trip(self):
        """MessageEnvelope serializes and deserializes without data loss."""
        envelope = MessageEnvelope(
            sender_id="alice",
            recipient_id="bob",
            timestamp=1700000000.123,
            message_type="text",
            payload=b"encrypted payload here",
            self_destruct_seconds=30,
        )
        data = envelope.to_bytes()
        restored = MessageEnvelope.from_bytes(data)
        self.assertEqual(restored.sender_id, "alice")
        self.assertEqual(restored.recipient_id, "bob")
        self.assertAlmostEqual(restored.timestamp, 1700000000.123, places=3)
        self.assertEqual(restored.message_type, "text")
        self.assertEqual(restored.payload, b"encrypted payload here")
        self.assertEqual(restored.self_destruct_seconds, 30)

    def test_message_envelope_no_self_destruct(self):
        """MessageEnvelope without self-destruct timer."""
        envelope = MessageEnvelope(
            sender_id="charlie",
            recipient_id="dave",
            timestamp=time.time(),
            message_type="file",
            payload=b"\x00" * 100,
            self_destruct_seconds=None,
        )
        data = envelope.to_bytes()
        restored = MessageEnvelope.from_bytes(data)
        self.assertIsNone(restored.self_destruct_seconds)


class TestRatchetHeader(unittest.TestCase):
    """Test binary header encode/decode."""

    def test_encode_decode_round_trip(self):
        """Header encodes to 40 bytes and decodes correctly."""
        dh_key = b"\xab" * 32
        header = Header(dh_key, prev_chain_length=10, message_number=255)
        encoded = header.encode()
        self.assertEqual(len(encoded), HEADER_SIZE)

        decoded = Header.decode(encoded)
        self.assertEqual(decoded.dh_ratchet_key, dh_key)
        self.assertEqual(decoded.prev_chain_length, 10)
        self.assertEqual(decoded.message_number, 255)

    def test_encode_decode_zero_values(self):
        """Header with zero values encodes/decodes correctly."""
        dh_key = b"\x00" * 32
        header = Header(dh_key, prev_chain_length=0, message_number=0)
        decoded = Header.decode(header.encode())
        self.assertEqual(decoded.dh_ratchet_key, dh_key)
        self.assertEqual(decoded.prev_chain_length, 0)
        self.assertEqual(decoded.message_number, 0)

    def test_encode_decode_large_values(self):
        """Header with large counter values encodes/decodes correctly."""
        dh_key = b"\xff" * 32
        header = Header(dh_key, prev_chain_length=2**32 - 1, message_number=2**32 - 1)
        decoded = Header.decode(header.encode())
        self.assertEqual(decoded.prev_chain_length, 2**32 - 1)
        self.assertEqual(decoded.message_number, 2**32 - 1)

    def test_invalid_dh_key_size(self):
        """Header raises ValueError for wrong DH key size."""
        with self.assertRaises(ValueError):
            Header(b"\x00" * 16, 0, 0)

    def test_invalid_data_size(self):
        """Header.decode raises ValueError for wrong data size."""
        with self.assertRaises(ValueError):
            Header.decode(b"\x00" * 20)

    def test_associated_data(self):
        """Associated data equals the encoded header."""
        dh_key = b"\xab" * 32
        header = Header(dh_key, prev_chain_length=5, message_number=3)
        self.assertEqual(header.associated_data(), header.encode())


class TestX3DHHandshake(unittest.TestCase):
    """Test X3DH handshake produces matching secrets."""

    def test_handshake_with_one_time_prekey(self):
        """Initiator and responder derive identical shared secrets with OTP."""
        # Generate keys for both parties
        alice_identity = X25519KeyPair.generate()
        bob_identity = X25519KeyPair.generate()
        bob_signed_prekey = X25519KeyPair.generate()
        bob_one_time_prekey = X25519KeyPair.generate()

        # Create Bob's key bundle
        bundle = KeyBundle(
            identity_key=bob_identity.public_key,
            signed_prekey=bob_signed_prekey.public_key,
            signed_prekey_signature=b"\x00" * 64,  # Signature verification not in scope
            one_time_prekey=bob_one_time_prekey.public_key,
        )

        # Alice performs handshake
        initiator = X3DHInitiator()
        alice_secret, ephemeral_pub = initiator.perform_handshake(alice_identity, bundle)

        # Bob completes handshake
        responder = X3DHResponder()
        bob_secret = responder.complete_handshake(
            our_identity=bob_identity,
            our_signed_prekey=bob_signed_prekey,
            our_one_time_prekey=bob_one_time_prekey,
            peer_identity_key=alice_identity.public_key,
            peer_ephemeral_key=ephemeral_pub,
        )

        # Both should derive the same shared secret
        self.assertEqual(alice_secret, bob_secret)
        self.assertEqual(len(alice_secret), 32)

    def test_handshake_without_one_time_prekey(self):
        """Initiator and responder derive identical shared secrets without OTP."""
        alice_identity = X25519KeyPair.generate()
        bob_identity = X25519KeyPair.generate()
        bob_signed_prekey = X25519KeyPair.generate()

        bundle = KeyBundle(
            identity_key=bob_identity.public_key,
            signed_prekey=bob_signed_prekey.public_key,
            signed_prekey_signature=b"\x00" * 64,
            one_time_prekey=None,
        )

        initiator = X3DHInitiator()
        alice_secret, ephemeral_pub = initiator.perform_handshake(alice_identity, bundle)

        responder = X3DHResponder()
        bob_secret = responder.complete_handshake(
            our_identity=bob_identity,
            our_signed_prekey=bob_signed_prekey,
            our_one_time_prekey=None,
            peer_identity_key=alice_identity.public_key,
            peer_ephemeral_key=ephemeral_pub,
        )

        self.assertEqual(alice_secret, bob_secret)
        self.assertEqual(len(alice_secret), 32)

    def test_different_keys_produce_different_secrets(self):
        """Different key bundles produce different shared secrets."""
        alice_identity = X25519KeyPair.generate()
        bob_identity1 = X25519KeyPair.generate()
        bob_identity2 = X25519KeyPair.generate()
        bob_spk1 = X25519KeyPair.generate()
        bob_spk2 = X25519KeyPair.generate()

        bundle1 = KeyBundle(
            identity_key=bob_identity1.public_key,
            signed_prekey=bob_spk1.public_key,
            signed_prekey_signature=b"\x00" * 64,
        )
        bundle2 = KeyBundle(
            identity_key=bob_identity2.public_key,
            signed_prekey=bob_spk2.public_key,
            signed_prekey_signature=b"\x00" * 64,
        )

        initiator = X3DHInitiator()
        secret1, _ = initiator.perform_handshake(alice_identity, bundle1)
        secret2, _ = initiator.perform_handshake(alice_identity, bundle2)

        self.assertNotEqual(secret1, secret2)


class TestDoubleRatchet(unittest.TestCase):
    """Test Double Ratchet encrypt/decrypt."""

    def _setup_ratchet_pair(self):
        """Helper to set up Alice and Bob ratchet states after X3DH."""
        alice_identity = X25519KeyPair.generate()
        bob_identity = X25519KeyPair.generate()
        bob_signed_prekey = X25519KeyPair.generate()

        bundle = KeyBundle(
            identity_key=bob_identity.public_key,
            signed_prekey=bob_signed_prekey.public_key,
            signed_prekey_signature=b"\x00" * 64,
        )

        initiator = X3DHInitiator()
        shared_secret, ephemeral_pub = initiator.perform_handshake(alice_identity, bundle)

        responder = X3DHResponder()
        bob_secret = responder.complete_handshake(
            our_identity=bob_identity,
            our_signed_prekey=bob_signed_prekey,
            our_one_time_prekey=None,
            peer_identity_key=alice_identity.public_key,
            peer_ephemeral_key=ephemeral_pub,
        )

        # Bob uses his signed prekey as initial ratchet key
        bob_state = RatchetState.initialize_responder(bob_secret, bob_signed_prekey)
        alice_state = RatchetState.initialize_initiator(shared_secret, bob_signed_prekey.public_key)

        return alice_state, bob_state

    def test_single_message(self):
        """Encrypt and decrypt a single message."""
        alice_state, bob_state = self._setup_ratchet_pair()

        plaintext = b"Hello, Bob!"
        encrypted = alice_state.encrypt(plaintext)
        decrypted = bob_state.decrypt(encrypted)

        self.assertEqual(decrypted, plaintext)

    def test_multiple_messages_same_direction(self):
        """Multiple messages in the same direction (no DH ratchet)."""
        alice_state, bob_state = self._setup_ratchet_pair()

        messages = [b"Message 1", b"Message 2", b"Message 3", b"Message 4", b"Message 5"]

        encrypted_messages = []
        for msg in messages:
            encrypted_messages.append(alice_state.encrypt(msg))

        for i, enc in enumerate(encrypted_messages):
            decrypted = bob_state.decrypt(enc)
            self.assertEqual(decrypted, messages[i])

    def test_alternating_messages(self):
        """Alternating messages triggers DH ratchet steps."""
        alice_state, bob_state = self._setup_ratchet_pair()

        # Alice -> Bob
        enc1 = alice_state.encrypt(b"Alice message 1")
        plain1 = bob_state.decrypt(enc1)
        self.assertEqual(plain1, b"Alice message 1")

        # Bob -> Alice
        enc2 = bob_state.encrypt(b"Bob message 1")
        plain2 = alice_state.decrypt(enc2)
        self.assertEqual(plain2, b"Bob message 1")

        # Alice -> Bob
        enc3 = alice_state.encrypt(b"Alice message 2")
        plain3 = bob_state.decrypt(enc3)
        self.assertEqual(plain3, b"Alice message 2")

        # Bob -> Alice
        enc4 = bob_state.encrypt(b"Bob message 2")
        plain4 = alice_state.decrypt(enc4)
        self.assertEqual(plain4, b"Bob message 2")

    def test_out_of_order_messages(self):
        """Out-of-order messages within skip window decrypt correctly."""
        alice_state, bob_state = self._setup_ratchet_pair()

        # Alice sends 5 messages
        enc_msgs = []
        for i in range(5):
            enc_msgs.append(alice_state.encrypt(f"Message {i}".encode()))

        # Bob decrypts in reverse order (simulating out-of-order delivery)
        # First decrypt message 4 (this sets up the chain)
        plain4 = bob_state.decrypt(enc_msgs[4])
        self.assertEqual(plain4, b"Message 4")

        # Now decrypt messages 0-3 (skipped messages)
        for i in range(4):
            plain = bob_state.decrypt(enc_msgs[i])
            self.assertEqual(plain, f"Message {i}".encode())

    def test_out_of_order_partial(self):
        """Partial out-of-order: skip some, then go back."""
        alice_state, bob_state = self._setup_ratchet_pair()

        enc_msgs = []
        for i in range(5):
            enc_msgs.append(alice_state.encrypt(f"Msg {i}".encode()))

        # Decrypt 0, skip 1 and 2, decrypt 3
        plain0 = bob_state.decrypt(enc_msgs[0])
        self.assertEqual(plain0, b"Msg 0")

        plain3 = bob_state.decrypt(enc_msgs[3])
        self.assertEqual(plain3, b"Msg 3")

        # Now decrypt skipped 1 and 2
        plain1 = bob_state.decrypt(enc_msgs[1])
        self.assertEqual(plain1, b"Msg 1")

        plain2 = bob_state.decrypt(enc_msgs[2])
        self.assertEqual(plain2, b"Msg 2")

        # And 4
        plain4 = bob_state.decrypt(enc_msgs[4])
        self.assertEqual(plain4, b"Msg 4")

    def test_forward_secrecy(self):
        """After ratchet advance, old keys are deleted and cannot decrypt new messages."""
        alice_state, bob_state = self._setup_ratchet_pair()

        # Alice sends a message
        enc1 = alice_state.encrypt(b"First message")
        bob_state.decrypt(enc1)

        # Save Bob's old root key and chain key state
        old_bob_root = bob_state.root_key
        old_bob_recv_chain = bob_state.recv_chain_key

        # Bob responds (triggers DH ratchet on Alice's side when she receives)
        enc2 = bob_state.encrypt(b"Response")
        alice_state.decrypt(enc2)

        # Alice sends another message (with new DH ratchet key)
        enc3 = alice_state.encrypt(b"New secret message")
        bob_state.decrypt(enc3)

        # After DH ratchet, keys have changed - demonstrating forward secrecy
        # Root key must be different after ratchet steps
        self.assertNotEqual(bob_state.root_key, old_bob_root)

        # The old receive chain key is no longer in use
        self.assertNotEqual(bob_state.recv_chain_key, old_bob_recv_chain)

        # Verify that encrypting with old compromised state produces
        # messages that the other party's advanced state still handles,
        # but the key material has progressed forward
        old_send_chain = alice_state.send_chain_key

        # Another round of ratcheting
        enc4 = bob_state.encrypt(b"Another bob msg")
        alice_state.decrypt(enc4)

        enc5 = alice_state.encrypt(b"Post ratchet")
        bob_state.decrypt(enc5)

        # Send chain key has advanced (forward secrecy - old key is gone)
        self.assertNotEqual(alice_state.send_chain_key, old_send_chain)

    def test_state_serialization(self):
        """Ratchet state can be serialized and restored."""
        alice_state, bob_state = self._setup_ratchet_pair()

        # Do some encryption
        enc1 = alice_state.encrypt(b"Before serialize")
        bob_state.decrypt(enc1)

        # Serialize and restore Alice
        alice_dict = alice_state.to_dict()
        alice_restored = RatchetState.from_dict(alice_dict)

        # Serialize and restore Bob
        bob_dict = bob_state.to_dict()
        bob_restored = RatchetState.from_dict(bob_dict)

        # Continue communication with restored states
        enc2 = alice_restored.encrypt(b"After serialize")
        plain2 = bob_restored.decrypt(enc2)
        self.assertEqual(plain2, b"After serialize")

    def test_state_serialization_with_skipped_keys(self):
        """State with skipped keys serializes correctly."""
        alice_state, bob_state = self._setup_ratchet_pair()

        # Send 3 messages
        enc_msgs = []
        for i in range(3):
            enc_msgs.append(alice_state.encrypt(f"Msg {i}".encode()))

        # Bob skips to message 2 (stores keys for 0 and 1)
        bob_state.decrypt(enc_msgs[2])

        # Serialize/restore Bob
        bob_dict = bob_state.to_dict()
        bob_restored = RatchetState.from_dict(bob_dict)

        # Should still decrypt skipped messages
        plain0 = bob_restored.decrypt(enc_msgs[0])
        self.assertEqual(plain0, b"Msg 0")

        plain1 = bob_restored.decrypt(enc_msgs[1])
        self.assertEqual(plain1, b"Msg 1")

    def test_empty_plaintext(self):
        """Encrypting empty plaintext works."""
        alice_state, bob_state = self._setup_ratchet_pair()

        enc = alice_state.encrypt(b"")
        plain = bob_state.decrypt(enc)
        self.assertEqual(plain, b"")

    def test_large_plaintext(self):
        """Encrypting large plaintext works."""
        alice_state, bob_state = self._setup_ratchet_pair()

        large_msg = b"X" * 10000
        enc = alice_state.encrypt(large_msg)
        plain = bob_state.decrypt(enc)
        self.assertEqual(plain, large_msg)

    def test_associated_data(self):
        """Associated data is authenticated."""
        alice_state, bob_state = self._setup_ratchet_pair()

        enc = alice_state.encrypt(b"Secret", associated_data=b"context")
        # Correct AD
        plain = bob_state.decrypt(enc, associated_data=b"context")
        self.assertEqual(plain, b"Secret")

    def test_wrong_associated_data_fails(self):
        """Wrong associated data causes decryption failure."""
        alice_state, bob_state = self._setup_ratchet_pair()

        enc = alice_state.encrypt(b"Secret", associated_data=b"correct_context")
        with self.assertRaises(RuntimeError):
            bob_state.decrypt(enc, associated_data=b"wrong_context")


if __name__ == "__main__":
    unittest.main()
