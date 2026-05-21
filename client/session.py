"""
End-to-end session management for ARES-X client.

Manages encrypted sessions between peers using the Double Ratchet algorithm.
Handles session creation via X3DH, message encryption/decryption,
safety number computation, and session persistence.
"""

import hashlib
import json
import sqlite3
import time
from typing import Optional, Dict

from crypto.key_exchange import X25519KeyPair
from crypto.double_ratchet import RatchetState
from protocol.messages import (
    KeyBundle,
    HandshakeMessage,
    EncryptedMessage,
)
from protocol.handshake import X3DHInitiator, X3DHResponder


class Session:
    """
    Represents an encrypted session with a single peer.

    Wraps a RatchetState and provides encrypt/decrypt methods
    along with safety number computation for identity verification.
    """

    def __init__(self, peer_id: str, ratchet_state: RatchetState, peer_identity_key: bytes):
        """
        Initialize a session.

        Args:
            peer_id: Identifier of the remote peer
            ratchet_state: Initialized Double Ratchet state
            peer_identity_key: Peer's long-term identity public key
        """
        self.peer_id = peer_id
        self.ratchet_state = ratchet_state
        self.peer_identity_key = peer_identity_key
        self.created_at = time.time()
        self.message_count = 0

    def encrypt_message(self, plaintext: bytes) -> EncryptedMessage:
        """
        Encrypt a message for the peer.

        Args:
            plaintext: Message bytes to encrypt

        Returns:
            EncryptedMessage ready for transport
        """
        self.message_count += 1
        return self.ratchet_state.encrypt(plaintext)

    def decrypt_message(self, message: EncryptedMessage) -> bytes:
        """
        Decrypt a message from the peer.

        Args:
            message: Encrypted message received from peer

        Returns:
            Decrypted plaintext bytes

        Raises:
            RuntimeError: If decryption fails (tampered or wrong session)
        """
        return self.ratchet_state.decrypt(message)

    def get_safety_number(self, our_identity_key: bytes) -> str:
        """
        Compute safety number for identity verification.

        Both parties compute the same safety number from their identity keys.
        Displayed as groups of 5 digits for easy comparison.

        Args:
            our_identity_key: Our identity public key

        Returns:
            String of digit groups (e.g., "12345 67890 12345 ...")
        """
        # Sort keys to ensure both parties get the same result
        keys = sorted([our_identity_key, self.peer_identity_key])
        combined = keys[0] + keys[1]
        digest = hashlib.sha256(combined).digest()

        # Convert to decimal digits (take first 30 digits)
        number = int.from_bytes(digest[:16], "big")
        digits = str(number).zfill(40)[:30]

        # Format as groups of 5
        groups = [digits[i:i+5] for i in range(0, 30, 5)]
        return " ".join(groups)

    def to_dict(self) -> dict:
        """Serialize session to dictionary for persistence."""
        import base64
        return {
            "peer_id": self.peer_id,
            "ratchet_state": self.ratchet_state.to_dict(),
            "peer_identity_key": base64.b64encode(self.peer_identity_key).decode("ascii"),
            "created_at": self.created_at,
            "message_count": self.message_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Deserialize session from dictionary."""
        import base64
        ratchet_state = RatchetState.from_dict(data["ratchet_state"])
        peer_identity_key = base64.b64decode(data["peer_identity_key"])
        session = cls(
            peer_id=data["peer_id"],
            ratchet_state=ratchet_state,
            peer_identity_key=peer_identity_key,
        )
        session.created_at = data.get("created_at", time.time())
        session.message_count = data.get("message_count", 0)
        return session


class SessionManager:
    """
    Manages multiple encrypted sessions with different peers.

    Handles session creation (both initiator and responder sides),
    persistence, and lookup.
    """

    def __init__(self, key_store):
        """
        Initialize session manager.

        Args:
            key_store: KeyStore instance for accessing our keys
        """
        self.key_store = key_store
        self._sessions: Dict[str, Session] = {}

    def create_session_initiator(self, peer_id: str, peer_bundle: KeyBundle) -> Session:
        """
        Create a new session as the handshake initiator.

        Performs X3DH key agreement and initializes the Double Ratchet.

        Args:
            peer_id: Identifier for the remote peer
            peer_bundle: Peer's published key bundle

        Returns:
            Initialized Session ready to encrypt messages
        """
        our_identity = self.key_store.get_identity_key()
        if our_identity is None:
            raise RuntimeError("No identity key. Generate identity first.")

        # Perform X3DH handshake
        initiator = X3DHInitiator()
        shared_secret, ephemeral_pub = initiator.perform_handshake(our_identity, peer_bundle)

        # Initialize Double Ratchet as initiator
        # Use peer's signed prekey as initial ratchet key
        ratchet_state = RatchetState.initialize_initiator(
            shared_secret=shared_secret,
            peer_public_key=peer_bundle.signed_prekey,
        )

        session = Session(
            peer_id=peer_id,
            ratchet_state=ratchet_state,
            peer_identity_key=peer_bundle.identity_key,
        )

        self._sessions[peer_id] = session
        return session

    def create_session_responder(self, peer_id: str, handshake_msg: HandshakeMessage) -> Session:
        """
        Create a new session as the handshake responder.

        Completes X3DH key agreement and initializes the Double Ratchet.

        Args:
            peer_id: Identifier for the remote peer
            handshake_msg: Handshake message from the initiator

        Returns:
            Initialized Session ready to decrypt messages
        """
        our_identity = self.key_store.get_identity_key()
        if our_identity is None:
            raise RuntimeError("No identity key. Generate identity first.")

        our_signed_prekey = self.key_store.get_signed_prekey()
        if our_signed_prekey is None:
            raise RuntimeError("No signed prekey found.")

        # Check if one-time prekey was used
        our_otp = None
        # For simplicity, we pass None for OTP in the responder
        # In production, the handshake message would indicate which OTP was used

        # Complete X3DH
        responder = X3DHResponder()
        shared_secret = responder.complete_handshake(
            our_identity=our_identity,
            our_signed_prekey=our_signed_prekey,
            our_one_time_prekey=our_otp,
            peer_identity_key=handshake_msg.sender_identity_key,
            peer_ephemeral_key=handshake_msg.ephemeral_key,
        )

        # Initialize Double Ratchet as responder
        ratchet_state = RatchetState.initialize_responder(
            shared_secret=shared_secret,
            our_keypair=our_signed_prekey,
        )

        session = Session(
            peer_id=peer_id,
            ratchet_state=ratchet_state,
            peer_identity_key=handshake_msg.sender_identity_key,
        )

        self._sessions[peer_id] = session
        return session

    def get_session(self, peer_id: str) -> Optional[Session]:
        """
        Get an existing session for a peer.

        Args:
            peer_id: Peer identifier

        Returns:
            Session or None if no session exists
        """
        return self._sessions.get(peer_id)

    def save_session(self, session: Session):
        """
        Save a session to the in-memory store.

        Args:
            session: Session to save
        """
        self._sessions[session.peer_id] = session

    def load_sessions(self) -> Dict[str, Session]:
        """
        Get all active sessions.

        Returns:
            Dictionary mapping peer_id to Session
        """
        return dict(self._sessions)

    def save_sessions_to_db(self, db_path: str):
        """
        Persist all sessions to SQLite.

        Args:
            db_path: Path to SQLite database
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                peer_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL
            )
        """)
        for peer_id, session in self._sessions.items():
            data = json.dumps(session.to_dict())
            cursor.execute(
                "INSERT OR REPLACE INTO sessions (peer_id, session_data) VALUES (?, ?)",
                (peer_id, data),
            )
        conn.commit()
        conn.close()

    def load_sessions_from_db(self, db_path: str):
        """
        Load sessions from SQLite.

        Args:
            db_path: Path to SQLite database
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                peer_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL
            )
        """)
        cursor.execute("SELECT peer_id, session_data FROM sessions")
        for row in cursor.fetchall():
            peer_id, session_data = row
            data = json.loads(session_data)
            session = Session.from_dict(data)
            self._sessions[peer_id] = session
        conn.close()
