"""
Message pipeline for ARES-X client.

Handles composing, encrypting, decrypting, and processing messages
including text, file transfers, and self-destruct functionality.
"""

import json
import time
from typing import Optional, Dict, List

from protocol.messages import (
    EncryptedMessage,
    MessageEnvelope,
    HandshakeMessage,
)
from client.session import SessionManager


# Maximum chunk size for file transfers
FILE_CHUNK_SIZE = 32 * 1024  # 32KB


class Messenger:
    """
    Full message pipeline for composing and receiving encrypted messages.

    Handles text messages, file transfers, handshake messages,
    and self-destruct timer tracking.
    """

    def __init__(self, session_manager: SessionManager, user_id: str):
        """
        Initialize messenger.

        Args:
            session_manager: SessionManager for encryption/decryption
            user_id: Our user identifier
        """
        self.session_manager = session_manager
        self.user_id = user_id
        self._self_destruct_tracker: List[Dict] = []

    def compose_message(
        self, peer_id: str, text: str, self_destruct_seconds: Optional[int] = None
    ) -> MessageEnvelope:
        """
        Compose and encrypt a text message.

        Args:
            peer_id: Recipient peer identifier
            text: Message text to send
            self_destruct_seconds: Optional self-destruct timer in seconds

        Returns:
            MessageEnvelope ready for transport

        Raises:
            RuntimeError: If no session exists with the peer
        """
        session = self.session_manager.get_session(peer_id)
        if session is None:
            raise RuntimeError(f"No session with peer: {peer_id}")

        # Build message payload
        payload_data = {
            "text": text,
            "timestamp": time.time(),
        }
        if self_destruct_seconds is not None:
            payload_data["self_destruct_seconds"] = self_destruct_seconds

        plaintext = json.dumps(payload_data).encode("utf-8")
        encrypted = session.encrypt_message(plaintext)

        envelope = MessageEnvelope(
            sender_id=self.user_id,
            recipient_id=peer_id,
            timestamp=time.time(),
            message_type="text",
            payload=encrypted.to_bytes(),
            self_destruct_seconds=self_destruct_seconds,
        )

        return envelope

    def receive_message(self, envelope: MessageEnvelope) -> Dict:
        """
        Decrypt and process a received text message.

        Args:
            envelope: Received message envelope

        Returns:
            Dictionary with {sender, text, timestamp, self_destruct}

        Raises:
            RuntimeError: If no session exists or decryption fails
        """
        session = self.session_manager.get_session(envelope.sender_id)
        if session is None:
            raise RuntimeError(f"No session with sender: {envelope.sender_id}")

        encrypted_msg = EncryptedMessage.from_bytes(envelope.payload)
        plaintext = session.decrypt_message(encrypted_msg)
        payload_data = json.loads(plaintext.decode("utf-8"))

        result = {
            "sender": envelope.sender_id,
            "text": payload_data.get("text", ""),
            "timestamp": payload_data.get("timestamp", envelope.timestamp),
            "self_destruct": envelope.self_destruct_seconds,
        }

        # Track self-destruct if set
        if envelope.self_destruct_seconds is not None:
            self._self_destruct_tracker.append({
                "delivered_at": time.time(),
                "expires_at": time.time() + envelope.self_destruct_seconds,
                "sender": envelope.sender_id,
            })

        return result

    def compose_file_message(
        self, peer_id: str, filename: str, data: bytes
    ) -> MessageEnvelope:
        """
        Compose and encrypt a file message.

        For files larger than FILE_CHUNK_SIZE, the data is chunked
        and each chunk is encrypted separately.

        Args:
            peer_id: Recipient peer identifier
            filename: Name of the file
            data: Raw file data bytes

        Returns:
            MessageEnvelope containing the encrypted file

        Raises:
            RuntimeError: If no session exists with the peer
        """
        session = self.session_manager.get_session(peer_id)
        if session is None:
            raise RuntimeError(f"No session with peer: {peer_id}")

        # Build file payload with metadata
        import base64
        payload_data = {
            "filename": filename,
            "size": len(data),
            "chunks": [],
        }

        # Chunk the file if needed
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + FILE_CHUNK_SIZE]
            encrypted_chunk = session.encrypt_message(chunk)
            payload_data["chunks"].append(
                base64.b64encode(encrypted_chunk.to_bytes()).decode("ascii")
            )
            offset += FILE_CHUNK_SIZE

        # Wrap in envelope (the chunks are already encrypted individually)
        envelope_payload = json.dumps(payload_data).encode("utf-8")

        envelope = MessageEnvelope(
            sender_id=self.user_id,
            recipient_id=peer_id,
            timestamp=time.time(),
            message_type="file",
            payload=envelope_payload,
        )

        return envelope

    def receive_file_message(self, envelope: MessageEnvelope) -> Dict:
        """
        Decrypt and process a received file message.

        Args:
            envelope: Received file message envelope

        Returns:
            Dictionary with {sender, filename, data}

        Raises:
            RuntimeError: If no session exists or decryption fails
        """
        import base64

        session = self.session_manager.get_session(envelope.sender_id)
        if session is None:
            raise RuntimeError(f"No session with sender: {envelope.sender_id}")

        payload_data = json.loads(envelope.payload.decode("utf-8"))
        filename = payload_data["filename"]

        # Decrypt each chunk
        decrypted_data = b""
        for chunk_b64 in payload_data["chunks"]:
            chunk_bytes = base64.b64decode(chunk_b64)
            encrypted_msg = EncryptedMessage.from_bytes(chunk_bytes)
            decrypted_chunk = session.decrypt_message(encrypted_msg)
            decrypted_data += decrypted_chunk

        return {
            "sender": envelope.sender_id,
            "filename": filename,
            "data": decrypted_data,
        }

    def handle_handshake(self, envelope: MessageEnvelope):
        """
        Process an incoming handshake message.

        Creates a responder session with the sender.

        Args:
            envelope: Envelope containing handshake payload
        """
        handshake_msg = HandshakeMessage.from_bytes(envelope.payload)
        self.session_manager.create_session_responder(
            peer_id=envelope.sender_id,
            handshake_msg=handshake_msg,
        )

    def get_expired_messages(self) -> List[Dict]:
        """
        Get list of messages that have exceeded their self-destruct timer.

        Returns:
            List of expired message tracking records
        """
        now = time.time()
        expired = [m for m in self._self_destruct_tracker if now >= m["expires_at"]]
        self._self_destruct_tracker = [
            m for m in self._self_destruct_tracker if now < m["expires_at"]
        ]
        return expired
