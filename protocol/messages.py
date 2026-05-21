"""
Protocol message definitions for ARES-X secure messaging.

All messages are defined as dataclasses with serialization/deserialization
support via JSON with base64 encoding for bytes fields.
"""

import json
import base64
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


def _bytes_to_b64(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode("ascii")


def _b64_to_bytes(data: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(data)


@dataclass
class KeyBundle:
    """Public key bundle for X3DH handshake."""
    identity_key: bytes
    signed_prekey: bytes
    signed_prekey_signature: bytes
    one_time_prekey: Optional[bytes] = None

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes with base64-encoded fields."""
        d = {
            "identity_key": _bytes_to_b64(self.identity_key),
            "signed_prekey": _bytes_to_b64(self.signed_prekey),
            "signed_prekey_signature": _bytes_to_b64(self.signed_prekey_signature),
            "one_time_prekey": _bytes_to_b64(self.one_time_prekey) if self.one_time_prekey else None,
        }
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "KeyBundle":
        """Deserialize from JSON bytes."""
        d = json.loads(data.decode("utf-8"))
        return cls(
            identity_key=_b64_to_bytes(d["identity_key"]),
            signed_prekey=_b64_to_bytes(d["signed_prekey"]),
            signed_prekey_signature=_b64_to_bytes(d["signed_prekey_signature"]),
            one_time_prekey=_b64_to_bytes(d["one_time_prekey"]) if d.get("one_time_prekey") else None,
        )


@dataclass
class HandshakeMessage:
    """Initial handshake message sent by the initiator."""
    sender_identity_key: bytes
    ephemeral_key: bytes
    one_time_prekey_used: Optional[int] = None
    initial_ciphertext: bytes = b""

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes with base64-encoded fields."""
        d = {
            "sender_identity_key": _bytes_to_b64(self.sender_identity_key),
            "ephemeral_key": _bytes_to_b64(self.ephemeral_key),
            "one_time_prekey_used": self.one_time_prekey_used,
            "initial_ciphertext": _bytes_to_b64(self.initial_ciphertext),
        }
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "HandshakeMessage":
        """Deserialize from JSON bytes."""
        d = json.loads(data.decode("utf-8"))
        return cls(
            sender_identity_key=_b64_to_bytes(d["sender_identity_key"]),
            ephemeral_key=_b64_to_bytes(d["ephemeral_key"]),
            one_time_prekey_used=d.get("one_time_prekey_used"),
            initial_ciphertext=_b64_to_bytes(d["initial_ciphertext"]),
        )


@dataclass
class RatchetMessageHeader:
    """Header for a double ratchet message."""
    dh_public_key: bytes
    previous_chain_length: int
    message_number: int

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes with base64-encoded fields."""
        d = {
            "dh_public_key": _bytes_to_b64(self.dh_public_key),
            "previous_chain_length": self.previous_chain_length,
            "message_number": self.message_number,
        }
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "RatchetMessageHeader":
        """Deserialize from JSON bytes."""
        d = json.loads(data.decode("utf-8"))
        return cls(
            dh_public_key=_b64_to_bytes(d["dh_public_key"]),
            previous_chain_length=d["previous_chain_length"],
            message_number=d["message_number"],
        )


@dataclass
class EncryptedMessage:
    """A fully encrypted double ratchet message."""
    header: RatchetMessageHeader
    ciphertext: bytes
    nonce: bytes
    tag: bytes

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes with base64-encoded fields."""
        d = {
            "header": {
                "dh_public_key": _bytes_to_b64(self.header.dh_public_key),
                "previous_chain_length": self.header.previous_chain_length,
                "message_number": self.header.message_number,
            },
            "ciphertext": _bytes_to_b64(self.ciphertext),
            "nonce": _bytes_to_b64(self.nonce),
            "tag": _bytes_to_b64(self.tag),
        }
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "EncryptedMessage":
        """Deserialize from JSON bytes."""
        d = json.loads(data.decode("utf-8"))
        header = RatchetMessageHeader(
            dh_public_key=_b64_to_bytes(d["header"]["dh_public_key"]),
            previous_chain_length=d["header"]["previous_chain_length"],
            message_number=d["header"]["message_number"],
        )
        return cls(
            header=header,
            ciphertext=_b64_to_bytes(d["ciphertext"]),
            nonce=_b64_to_bytes(d["nonce"]),
            tag=_b64_to_bytes(d["tag"]),
        )


@dataclass
class MessageEnvelope:
    """Top-level message envelope for transport."""
    sender_id: str
    recipient_id: str
    timestamp: float
    message_type: str  # 'text', 'file', 'handshake', 'key_exchange'
    payload: bytes
    self_destruct_seconds: Optional[int] = None

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes with base64-encoded fields."""
        d = {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "payload": _bytes_to_b64(self.payload),
            "self_destruct_seconds": self.self_destruct_seconds,
        }
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageEnvelope":
        """Deserialize from JSON bytes."""
        d = json.loads(data.decode("utf-8"))
        return cls(
            sender_id=d["sender_id"],
            recipient_id=d["recipient_id"],
            timestamp=d["timestamp"],
            message_type=d["message_type"],
            payload=_b64_to_bytes(d["payload"]),
            self_destruct_seconds=d.get("self_destruct_seconds"),
        )
