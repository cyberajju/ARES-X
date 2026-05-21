"""
Double Ratchet Algorithm for ARES-X secure messaging.

Implements the full Double Ratchet providing forward secrecy and
break-in recovery through continuous key ratcheting.
"""

import hmac as hmac_module
import hashlib
import base64
from typing import Dict, Optional, Tuple

from crypto.key_exchange import X25519KeyPair, compute_shared_secret
from crypto.hkdf import derive_key
from crypto.aes_gcm import encrypt as aes_encrypt, decrypt as aes_decrypt
from protocol.messages import RatchetMessageHeader, EncryptedMessage


# Maximum number of skipped message keys to store (prevents DoS)
MAX_SKIP = 100

# Protocol constants
RATCHET_INFO = b"ARES-X_RATCHET"
CHAIN_KEY_MSG = b"\x01"  # Input for deriving message key from chain key
CHAIN_KEY_NEXT = b"\x02"  # Input for deriving next chain key


def _kdf_rk(root_key: bytes, dh_output: bytes) -> Tuple[bytes, bytes]:
    """
    KDF for root key ratchet step.

    Derives new root key and chain key from current root key and DH output.

    Args:
        root_key: Current root key (32 bytes)
        dh_output: DH shared secret output (32 bytes)

    Returns:
        Tuple of (new_root_key, new_chain_key) each 32 bytes
    """
    output = derive_key(
        ikm=dh_output,
        salt=root_key,
        info=RATCHET_INFO,
        length=64,
    )
    return output[:32], output[32:]


def _kdf_ck(chain_key: bytes) -> Tuple[bytes, bytes]:
    """
    KDF for symmetric chain ratchet step.

    Derives message key and next chain key from current chain key.

    Args:
        chain_key: Current chain key (32 bytes)

    Returns:
        Tuple of (new_chain_key, message_key)
    """
    # Next chain key: HMAC-SHA256(chain_key, 0x02)
    new_chain_key = hmac_module.new(chain_key, CHAIN_KEY_NEXT, hashlib.sha256).digest()
    # Message key: HMAC-SHA256(chain_key, 0x01)
    message_key = hmac_module.new(chain_key, CHAIN_KEY_MSG, hashlib.sha256).digest()
    return new_chain_key, message_key


class RatchetState:
    """
    Full Double Ratchet state machine.

    Manages DH ratchet keys, symmetric sending/receiving chains,
    and skipped message keys for out-of-order delivery.
    """

    def __init__(self):
        """Initialize empty ratchet state. Use class methods to create."""
        self.dh_keypair: Optional[X25519KeyPair] = None
        self.dh_remote_public: Optional[bytes] = None
        self.root_key: bytes = b""
        self.send_chain_key: Optional[bytes] = None
        self.recv_chain_key: Optional[bytes] = None
        self.send_message_number: int = 0
        self.recv_message_number: int = 0
        self.prev_chain_length: int = 0
        # Skipped keys: maps (base64(ratchet_pub), msg_num) -> message_key
        self.skipped_keys: Dict[Tuple[str, int], bytes] = {}

    @classmethod
    def initialize_initiator(cls, shared_secret: bytes, peer_public_key: bytes) -> "RatchetState":
        """
        Initialize ratchet state for the handshake initiator.

        The initiator performs the first DH ratchet step immediately.

        Args:
            shared_secret: Shared secret from X3DH handshake (32 bytes)
            peer_public_key: Responder's DH ratchet public key (32 bytes)

        Returns:
            Initialized RatchetState ready to encrypt
        """
        state = cls()
        state.dh_keypair = X25519KeyPair.generate()
        state.dh_remote_public = peer_public_key
        state.root_key = shared_secret

        # Perform initial DH ratchet step
        dh_output = compute_shared_secret(state.dh_keypair, peer_public_key)
        state.root_key, state.send_chain_key = _kdf_rk(state.root_key, dh_output)

        state.recv_chain_key = None
        state.send_message_number = 0
        state.recv_message_number = 0
        state.prev_chain_length = 0

        return state

    @classmethod
    def initialize_responder(cls, shared_secret: bytes, our_keypair: X25519KeyPair) -> "RatchetState":
        """
        Initialize ratchet state for the handshake responder.

        The responder sets up state and waits for the first message
        to trigger the DH ratchet.

        Args:
            shared_secret: Shared secret from X3DH handshake (32 bytes)
            our_keypair: Our initial DH ratchet key pair

        Returns:
            Initialized RatchetState ready to receive
        """
        state = cls()
        state.dh_keypair = our_keypair
        state.dh_remote_public = None
        state.root_key = shared_secret
        state.send_chain_key = None
        state.recv_chain_key = None
        state.send_message_number = 0
        state.recv_message_number = 0
        state.prev_chain_length = 0

        return state

    def encrypt(self, plaintext: bytes, associated_data: bytes = b"") -> EncryptedMessage:
        """
        Encrypt a message using the sending chain.

        Advances the symmetric sending chain and encrypts with AES-256-GCM.

        Args:
            plaintext: Message to encrypt
            associated_data: Additional data to authenticate (optional)

        Returns:
            EncryptedMessage containing header, ciphertext, nonce, and tag

        Raises:
            RuntimeError: If sending chain is not initialized
        """
        if self.send_chain_key is None:
            raise RuntimeError("Send chain not initialized")

        # Advance sending chain
        self.send_chain_key, message_key = _kdf_ck(self.send_chain_key)

        # Create header
        header = RatchetMessageHeader(
            dh_public_key=self.dh_keypair.public_key,
            previous_chain_length=self.prev_chain_length,
            message_number=self.send_message_number,
        )

        # Combine associated data with header
        ad = associated_data + header.dh_public_key

        # Encrypt with AES-256-GCM
        nonce, ciphertext, tag = aes_encrypt(message_key, plaintext, ad)

        self.send_message_number += 1

        return EncryptedMessage(
            header=header,
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
        )

    def decrypt(self, message: EncryptedMessage, associated_data: bytes = b"") -> bytes:
        """
        Decrypt a received message.

        Handles DH ratchet steps for new remote public keys and
        skipped messages for out-of-order delivery.

        Args:
            message: The encrypted message to decrypt
            associated_data: Additional authenticated data (must match encryption)

        Returns:
            Decrypted plaintext bytes

        Raises:
            RuntimeError: If decryption fails or message cannot be processed
        """
        header = message.header
        pub_key_b64 = base64.b64encode(header.dh_public_key).decode("ascii")

        # Check if this is a skipped message
        skipped_key_id = (pub_key_b64, header.message_number)
        if skipped_key_id in self.skipped_keys:
            message_key = self.skipped_keys.pop(skipped_key_id)
            ad = associated_data + header.dh_public_key
            return aes_decrypt(message_key, message.nonce, message.ciphertext, message.tag, ad)

        # Check if we need a DH ratchet step
        if self.dh_remote_public is None or header.dh_public_key != self.dh_remote_public:
            self._skip_messages(header.previous_chain_length)
            self._dh_ratchet(header.dh_public_key)

        # Skip any messages before this one in the current chain
        self._skip_messages(header.message_number)

        # Advance receiving chain
        self.recv_chain_key, message_key = _kdf_ck(self.recv_chain_key)
        self.recv_message_number += 1

        # Decrypt
        ad = associated_data + header.dh_public_key
        return aes_decrypt(message_key, message.nonce, message.ciphertext, message.tag, ad)

    def _skip_messages(self, until: int):
        """
        Store skipped message keys for out-of-order delivery.

        Args:
            until: Skip messages up to (but not including) this number

        Raises:
            RuntimeError: If too many messages would be skipped
        """
        if self.recv_chain_key is None:
            return

        if until - self.recv_message_number > MAX_SKIP:
            raise RuntimeError(
                f"Cannot skip more than {MAX_SKIP} messages "
                f"(requested skip from {self.recv_message_number} to {until})"
            )

        while self.recv_message_number < until:
            self.recv_chain_key, message_key = _kdf_ck(self.recv_chain_key)
            pub_key_b64 = base64.b64encode(self.dh_remote_public).decode("ascii")
            self.skipped_keys[(pub_key_b64, self.recv_message_number)] = message_key
            self.recv_message_number += 1

            # Enforce max skip limit on total stored keys
            if len(self.skipped_keys) > MAX_SKIP:
                # Remove oldest entry
                oldest_key = next(iter(self.skipped_keys))
                del self.skipped_keys[oldest_key]

    def _dh_ratchet(self, new_peer_public_key: bytes):
        """
        Perform a DH ratchet step with a new peer public key.

        Generates a new DH key pair, computes new shared secrets,
        and derives new root key and chain keys.

        Args:
            new_peer_public_key: Peer's new DH ratchet public key
        """
        self.prev_chain_length = self.send_message_number
        self.send_message_number = 0
        self.recv_message_number = 0
        self.dh_remote_public = new_peer_public_key

        # Derive new receiving chain from current DH
        dh_output = compute_shared_secret(self.dh_keypair, self.dh_remote_public)
        self.root_key, self.recv_chain_key = _kdf_rk(self.root_key, dh_output)

        # Generate new DH key pair for sending
        self.dh_keypair = X25519KeyPair.generate()

        # Derive new sending chain
        dh_output = compute_shared_secret(self.dh_keypair, self.dh_remote_public)
        self.root_key, self.send_chain_key = _kdf_rk(self.root_key, dh_output)

    def to_dict(self) -> dict:
        """
        Serialize ratchet state to dictionary for persistence.

        Returns:
            Dictionary representation of the state
        """
        def _encode_bytes(b: Optional[bytes]) -> Optional[str]:
            return base64.b64encode(b).decode("ascii") if b else None

        # Serialize skipped keys
        skipped = {}
        for (pub_b64, msg_num), key in self.skipped_keys.items():
            skipped_id = f"{pub_b64}:{msg_num}"
            skipped[skipped_id] = base64.b64encode(key).decode("ascii")

        return {
            "dh_private_key": _encode_bytes(self.dh_keypair.private_key) if self.dh_keypair else None,
            "dh_public_key": _encode_bytes(self.dh_keypair.public_key) if self.dh_keypair else None,
            "dh_remote_public": _encode_bytes(self.dh_remote_public),
            "root_key": _encode_bytes(self.root_key),
            "send_chain_key": _encode_bytes(self.send_chain_key),
            "recv_chain_key": _encode_bytes(self.recv_chain_key),
            "send_message_number": self.send_message_number,
            "recv_message_number": self.recv_message_number,
            "prev_chain_length": self.prev_chain_length,
            "skipped_keys": skipped,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RatchetState":
        """
        Deserialize ratchet state from dictionary.

        Args:
            data: Dictionary from to_dict()

        Returns:
            Restored RatchetState
        """
        def _decode_bytes(s: Optional[str]) -> Optional[bytes]:
            return base64.b64decode(s) if s else None

        state = cls()

        # Restore DH key pair
        priv = _decode_bytes(data.get("dh_private_key"))
        if priv:
            state.dh_keypair = X25519KeyPair.from_private_key(priv)
        else:
            state.dh_keypair = None

        state.dh_remote_public = _decode_bytes(data.get("dh_remote_public"))
        state.root_key = _decode_bytes(data.get("root_key")) or b""
        state.send_chain_key = _decode_bytes(data.get("send_chain_key"))
        state.recv_chain_key = _decode_bytes(data.get("recv_chain_key"))
        state.send_message_number = data.get("send_message_number", 0)
        state.recv_message_number = data.get("recv_message_number", 0)
        state.prev_chain_length = data.get("prev_chain_length", 0)

        # Restore skipped keys
        state.skipped_keys = {}
        for skipped_id, key_b64 in data.get("skipped_keys", {}).items():
            pub_b64, msg_num_str = skipped_id.rsplit(":", 1)
            state.skipped_keys[(pub_b64, int(msg_num_str))] = base64.b64decode(key_b64)

        return state
