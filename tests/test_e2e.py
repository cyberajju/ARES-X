"""
End-to-end integration tests for ARES-X secure messaging.

Tests full message flow between two clients using a mock relay,
exercising real cryptographic operations without network.
"""

import unittest
import json
import time
import copy

from crypto.key_exchange import X25519KeyPair
from crypto.double_ratchet import RatchetState
from protocol.messages import (
    KeyBundle,
    HandshakeMessage,
    EncryptedMessage,
    MessageEnvelope,
)
from protocol.handshake import X3DHInitiator, X3DHResponder
from client.key_store import KeyStore
from client.session import Session, SessionManager
from client.messenger import Messenger


class MockRelay:
    """
    Simulates a server relay for testing.

    Holds messages in a dictionary keyed by user_id and allows
    delivery between two clients without network.
    """

    def __init__(self):
        self.messages = {}  # {user_id: [MessageEnvelope, ...]}

    def send(self, envelope: MessageEnvelope):
        """Queue a message for the recipient."""
        recipient = envelope.recipient_id
        if recipient not in self.messages:
            self.messages[recipient] = []
        self.messages[recipient].append(envelope)

    def receive(self, user_id: str):
        """Get all queued messages for a user."""
        messages = self.messages.get(user_id, [])
        self.messages[user_id] = []
        return messages

    def has_messages(self, user_id: str) -> bool:
        """Check if user has pending messages."""
        return len(self.messages.get(user_id, [])) > 0


def create_client_stack(user_id: str):
    """Create a complete client stack (key_store, session_manager, messenger) in memory."""
    key_store = KeyStore(":memory:")
    key_store.generate_identity()
    key_store.generate_signed_prekey()
    key_store.generate_one_time_prekeys(5)
    session_manager = SessionManager(key_store)
    messenger = Messenger(session_manager, user_id)
    return key_store, session_manager, messenger


def perform_handshake(alice_stack, bob_stack):
    """
    Perform X3DH handshake between Alice (initiator) and Bob (responder).

    Manually coordinates both sides to ensure they derive the same shared secret.
    Returns (alice_session, bob_session) tuple.
    """
    alice_ks, alice_sm, _ = alice_stack
    bob_ks, bob_sm, _ = bob_stack

    alice_identity = alice_ks.get_identity_key()
    bob_identity = bob_ks.get_identity_key()
    bob_signed_prekey = bob_ks.get_signed_prekey()

    # Bob exports his bundle (without one-time prekey for simplicity)
    bob_bundle = KeyBundle(
        identity_key=bob_identity.public_key,
        signed_prekey=bob_signed_prekey.public_key,
        signed_prekey_signature=b"\x00" * 64,
        one_time_prekey=None,
    )

    # Alice performs X3DH once to get shared secret and ephemeral key
    initiator = X3DHInitiator()
    shared_secret, ephemeral_pub = initiator.perform_handshake(alice_identity, bob_bundle)

    # Alice initializes her ratchet as initiator
    alice_ratchet = RatchetState.initialize_initiator(
        shared_secret=shared_secret,
        peer_public_key=bob_signed_prekey.public_key,
    )
    alice_session = Session(
        peer_id="bob",
        ratchet_state=alice_ratchet,
        peer_identity_key=bob_identity.public_key,
    )
    alice_sm._sessions["bob"] = alice_session

    # Bob completes X3DH with the same ephemeral key
    responder = X3DHResponder()
    bob_shared_secret = responder.complete_handshake(
        our_identity=bob_identity,
        our_signed_prekey=bob_signed_prekey,
        our_one_time_prekey=None,
        peer_identity_key=alice_identity.public_key,
        peer_ephemeral_key=ephemeral_pub,
    )

    # Bob initializes his ratchet as responder
    bob_ratchet = RatchetState.initialize_responder(
        shared_secret=bob_shared_secret,
        our_keypair=bob_signed_prekey,
    )
    bob_session = Session(
        peer_id="alice",
        ratchet_state=bob_ratchet,
        peer_identity_key=alice_identity.public_key,
    )
    bob_sm._sessions["alice"] = bob_session

    return alice_session, bob_session


class TestE2EHandshake(unittest.TestCase):
    """Test full handshake flow between two clients."""

    def test_handshake_completes(self):
        """Two clients can complete X3DH handshake via mock relay."""
        alice_stack = create_client_stack("alice")
        bob_stack = create_client_stack("bob")

        alice_session, bob_session = perform_handshake(alice_stack, bob_stack)

        self.assertIsNotNone(alice_session)
        self.assertIsNotNone(bob_session)
        self.assertEqual(alice_session.peer_id, "bob")
        self.assertEqual(bob_session.peer_id, "alice")

    def test_handshake_identity_keys_stored(self):
        """Sessions store the peer's identity key correctly."""
        alice_stack = create_client_stack("alice")
        bob_stack = create_client_stack("bob")

        alice_ks, _, _ = alice_stack
        bob_ks, _, _ = bob_stack

        alice_session, bob_session = perform_handshake(alice_stack, bob_stack)

        # Alice should have Bob's identity key
        bob_identity = bob_ks.get_identity_key()
        self.assertEqual(alice_session.peer_identity_key, bob_identity.public_key)


class TestE2EMessageExchange(unittest.TestCase):
    """Test encrypted message exchange between two clients."""

    def setUp(self):
        """Set up two clients with established sessions."""
        self.alice_stack = create_client_stack("alice")
        self.bob_stack = create_client_stack("bob")
        self.relay = MockRelay()

        # Perform handshake
        self.alice_session, self.bob_session = perform_handshake(
            self.alice_stack, self.bob_stack
        )

    def test_alice_sends_message_bob_decrypts(self):
        """Alice sends a message to Bob, Bob decrypts correctly."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice composes a message
        envelope = alice_messenger.compose_message("bob", "Hello Bob!")
        self.relay.send(envelope)

        # Bob receives and decrypts
        messages = self.relay.receive("bob")
        self.assertEqual(len(messages), 1)

        result = bob_messenger.receive_message(messages[0])
        self.assertEqual(result["sender"], "alice")
        self.assertEqual(result["text"], "Hello Bob!")

    def test_multiple_messages_back_and_forth(self):
        """Multiple messages exchanged correctly with DH ratchet progression."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice sends 3 messages
        for i in range(3):
            envelope = alice_messenger.compose_message("bob", f"Message {i}")
            self.relay.send(envelope)

        # Bob receives all 3
        messages = self.relay.receive("bob")
        self.assertEqual(len(messages), 3)

        for i, msg in enumerate(messages):
            result = bob_messenger.receive_message(msg)
            self.assertEqual(result["text"], f"Message {i}")

        # Bob replies
        envelope = bob_messenger.compose_message("alice", "Got them all!")
        self.relay.send(envelope)

        # Alice receives reply
        messages = self.relay.receive("alice")
        self.assertEqual(len(messages), 1)
        result = alice_messenger.receive_message(messages[0])
        self.assertEqual(result["text"], "Got them all!")

        # Alice sends another
        envelope = alice_messenger.compose_message("bob", "Great!")
        self.relay.send(envelope)

        messages = self.relay.receive("bob")
        result = bob_messenger.receive_message(messages[0])
        self.assertEqual(result["text"], "Great!")

    def test_forward_secrecy(self):
        """Old ratchet state cannot decrypt new messages."""
        _, alice_sm, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice sends a message to advance the ratchet
        envelope1 = alice_messenger.compose_message("bob", "Before snapshot")
        self.relay.send(envelope1)

        # Bob decrypts first message
        messages = self.relay.receive("bob")
        bob_messenger.receive_message(messages[0])

        # Snapshot Alice's ratchet state BEFORE advancing
        alice_session = alice_sm.get_session("bob")
        old_state_dict = alice_session.ratchet_state.to_dict()

        # Alice sends another message (ratchet advances)
        envelope2 = alice_messenger.compose_message("bob", "After snapshot")
        self.relay.send(envelope2)

        # Try to decrypt new message with old state
        old_ratchet = RatchetState.from_dict(old_state_dict)
        messages = self.relay.receive("bob")
        encrypted_msg = EncryptedMessage.from_bytes(messages[0].payload)

        # The old state should fail because it generates different keys
        # After advancing, the chain key has changed
        with self.assertRaises(RuntimeError):
            old_ratchet.decrypt(encrypted_msg)

    def test_self_destruct_metadata(self):
        """Self-destruct timer metadata is correctly set."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice sends with self-destruct
        envelope = alice_messenger.compose_message("bob", "Secret!", self_destruct_seconds=30)
        self.relay.send(envelope)

        self.assertEqual(envelope.self_destruct_seconds, 30)

        # Bob receives and checks
        messages = self.relay.receive("bob")
        result = bob_messenger.receive_message(messages[0])
        self.assertEqual(result["self_destruct"], 30)
        self.assertEqual(result["text"], "Secret!")

    def test_tampered_ciphertext_rejected(self):
        """Tampered ciphertext is rejected with authentication error."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice composes a message
        envelope = alice_messenger.compose_message("bob", "Tamper me")
        self.relay.send(envelope)

        # Tamper with the ciphertext
        messages = self.relay.receive("bob")
        tampered_envelope = messages[0]

        # Parse the payload, modify ciphertext, reserialize
        enc_data = json.loads(tampered_envelope.payload.decode("utf-8"))
        import base64
        ct_bytes = base64.b64decode(enc_data["ciphertext"])
        # Flip some bits
        tampered_ct = bytes([b ^ 0xFF for b in ct_bytes[:8]]) + ct_bytes[8:]
        enc_data["ciphertext"] = base64.b64encode(tampered_ct).decode("ascii")
        tampered_envelope.payload = json.dumps(enc_data).encode("utf-8")

        with self.assertRaises(RuntimeError):
            bob_messenger.receive_message(tampered_envelope)

    def test_tampered_tag_rejected(self):
        """Tampered authentication tag is rejected."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Alice composes a message
        envelope = alice_messenger.compose_message("bob", "Tamper tag")
        self.relay.send(envelope)

        # Tamper with the tag
        messages = self.relay.receive("bob")
        tampered_envelope = messages[0]

        enc_data = json.loads(tampered_envelope.payload.decode("utf-8"))
        import base64
        tag_bytes = base64.b64decode(enc_data["tag"])
        tampered_tag = bytes([b ^ 0xFF for b in tag_bytes])
        enc_data["tag"] = base64.b64encode(tampered_tag).decode("ascii")
        tampered_envelope.payload = json.dumps(enc_data).encode("utf-8")

        with self.assertRaises(RuntimeError):
            bob_messenger.receive_message(tampered_envelope)


class TestE2EFileTransfer(unittest.TestCase):
    """Test file encryption/decryption round trip."""

    def setUp(self):
        """Set up two clients with established sessions."""
        self.alice_stack = create_client_stack("alice")
        self.bob_stack = create_client_stack("bob")
        self.relay = MockRelay()

        self.alice_session, self.bob_session = perform_handshake(
            self.alice_stack, self.bob_stack
        )

    def test_file_round_trip(self):
        """File encryption and decryption round trip works correctly."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Create test file data
        file_data = b"This is a test file with some content.\n" * 100
        filename = "test_document.txt"

        # Alice sends file
        envelope = alice_messenger.compose_file_message("bob", filename, file_data)
        self.relay.send(envelope)

        # Bob receives file
        messages = self.relay.receive("bob")
        result = bob_messenger.receive_file_message(messages[0])

        self.assertEqual(result["sender"], "alice")
        self.assertEqual(result["filename"], filename)
        self.assertEqual(result["data"], file_data)

    def test_large_file_chunking(self):
        """Files larger than 32KB are chunked correctly."""
        _, _, alice_messenger = self.alice_stack
        _, _, bob_messenger = self.bob_stack

        # Create file larger than chunk size
        file_data = b"X" * (64 * 1024)  # 64KB
        filename = "large_file.bin"

        envelope = alice_messenger.compose_file_message("bob", filename, file_data)

        # Verify chunking happened
        payload_data = json.loads(envelope.payload.decode("utf-8"))
        self.assertGreater(len(payload_data["chunks"]), 1)

        self.relay.send(envelope)

        # Bob receives and decrypts
        messages = self.relay.receive("bob")
        result = bob_messenger.receive_file_message(messages[0])
        self.assertEqual(result["data"], file_data)


class TestE2ESafetyNumbers(unittest.TestCase):
    """Test safety number computation."""

    def test_safety_numbers_match(self):
        """Safety numbers match for both parties in a session."""
        alice_stack = create_client_stack("alice")
        bob_stack = create_client_stack("bob")

        alice_ks, _, _ = alice_stack
        bob_ks, _, _ = bob_stack

        alice_session, bob_session = perform_handshake(alice_stack, bob_stack)

        alice_identity = alice_ks.get_identity_key()
        bob_identity = bob_ks.get_identity_key()

        alice_safety = alice_session.get_safety_number(alice_identity.public_key)
        bob_safety = bob_session.get_safety_number(bob_identity.public_key)

        self.assertEqual(alice_safety, bob_safety)
        # Verify format: groups of 5 digits separated by spaces
        groups = alice_safety.split(" ")
        self.assertEqual(len(groups), 6)
        for g in groups:
            self.assertEqual(len(g), 5)
            self.assertTrue(g.isdigit())


class TestE2ESessionPersistence(unittest.TestCase):
    """Test session save and restore."""

    def test_session_persistence(self):
        """Session can be saved and restored, and still works for messaging."""
        alice_stack = create_client_stack("alice")
        bob_stack = create_client_stack("bob")

        alice_session, bob_session = perform_handshake(alice_stack, bob_stack)

        # Save Alice's session
        session_data = alice_session.to_dict()

        # Restore session
        restored_session = Session.from_dict(session_data)
        self.assertEqual(restored_session.peer_id, "alice_session_peer_id" if False else alice_session.peer_id)

        # Use restored session to encrypt
        plaintext = b"After restore"
        encrypted = restored_session.encrypt_message(plaintext)

        # Bob can decrypt
        decrypted = bob_session.decrypt_message(encrypted)
        self.assertEqual(decrypted, plaintext)


class TestKeyStoreRandomSalt(unittest.TestCase):
    """Test that key store uses a unique random salt per database."""

    def test_different_databases_produce_different_encryption_keys(self):
        """Two KeyStore instances with the same passphrase but different
        databases should produce different encryption keys because each
        database gets its own random salt."""
        passphrase = "same-passphrase-for-both"

        ks1 = KeyStore(":memory:", passphrase=passphrase)
        ks2 = KeyStore(":memory:", passphrase=passphrase)

        # The encryption keys should differ because the salts are random
        self.assertIsNotNone(ks1._encryption_key)
        self.assertIsNotNone(ks2._encryption_key)
        self.assertNotEqual(ks1._encryption_key, ks2._encryption_key)

        ks1.close()
        ks2.close()

    def test_same_database_produces_same_encryption_key(self):
        """Reopening the same database with the same passphrase should
        produce the same encryption key (salt is persisted)."""
        import tempfile
        import os

        tmp_file = tempfile.mktemp(suffix='.db')
        try:
            passphrase = "my-secure-passphrase"

            # First open - creates the salt
            ks1 = KeyStore(tmp_file, passphrase=passphrase)
            key1 = ks1._encryption_key
            ks1.close()

            # Second open - reads the existing salt
            ks2 = KeyStore(tmp_file, passphrase=passphrase)
            key2 = ks2._encryption_key
            ks2.close()

            self.assertEqual(key1, key2)
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)

    def test_salt_is_32_bytes(self):
        """The persisted salt should be 32 bytes."""
        ks = KeyStore(":memory:", passphrase="test")
        cursor = ks._conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'kdf_salt'")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(len(row[0]), 32)
        ks.close()

    def test_data_encrypted_with_random_salt_decrypts(self):
        """Keys encrypted with the random-salt-derived key can be decrypted
        on reopening the same database."""
        import tempfile
        import os

        tmp_file = tempfile.mktemp(suffix='.db')
        try:
            passphrase = "encryption-test"

            # Create key store and generate identity
            ks1 = KeyStore(tmp_file, passphrase=passphrase)
            identity1 = ks1.generate_identity()
            pub_key = identity1.public_key
            ks1.close()

            # Reopen and verify we can read the identity key back
            ks2 = KeyStore(tmp_file, passphrase=passphrase)
            identity2 = ks2.get_identity_key()
            self.assertIsNotNone(identity2)
            self.assertEqual(identity2.public_key, pub_key)
            ks2.close()
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)


if __name__ == "__main__":
    unittest.main()
