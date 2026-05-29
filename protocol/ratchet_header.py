"""
Binary header encoding for Double Ratchet messages.

Wire format: 32 bytes DH key + 4 bytes prev_chain_length + 4 bytes message_number = 40 bytes total.
"""

import struct


HEADER_SIZE = 40  # 32 + 4 + 4
DH_KEY_SIZE = 32


class Header:
    """
    Binary-encoded Double Ratchet message header.

    Contains the sender's current DH ratchet public key, the previous
    sending chain length, and the current message number.
    """

    def __init__(self, dh_ratchet_key: bytes, prev_chain_length: int, message_number: int):
        """
        Initialize header.

        Args:
            dh_ratchet_key: 32-byte DH ratchet public key
            prev_chain_length: Number of messages in the previous sending chain
            message_number: Message number in the current sending chain
        """
        if len(dh_ratchet_key) != DH_KEY_SIZE:
            raise ValueError(f"DH ratchet key must be {DH_KEY_SIZE} bytes, got {len(dh_ratchet_key)}")
        if prev_chain_length < 0:
            raise ValueError("prev_chain_length must be non-negative")
        if message_number < 0:
            raise ValueError("message_number must be non-negative")

        self.dh_ratchet_key = dh_ratchet_key
        self.prev_chain_length = prev_chain_length
        self.message_number = message_number

    def encode(self) -> bytes:
        """
        Encode header to binary format.

        Returns:
            40-byte encoded header
        """
        return self.dh_ratchet_key + struct.pack(">II", self.prev_chain_length, self.message_number)

    @classmethod
    def decode(cls, data: bytes) -> "Header":
        """
        Decode header from binary format.

        Args:
            data: 40-byte encoded header

        Returns:
            Decoded Header instance

        Raises:
            ValueError: If data is not exactly 40 bytes
        """
        if len(data) != HEADER_SIZE:
            raise ValueError(f"Header must be {HEADER_SIZE} bytes, got {len(data)}")

        dh_ratchet_key = data[:DH_KEY_SIZE]
        prev_chain_length, message_number = struct.unpack(">II", data[DH_KEY_SIZE:])
        return cls(dh_ratchet_key, prev_chain_length, message_number)

    def associated_data(self) -> bytes:
        """
        Generate associated data for AEAD encryption.

        The full encoded header is used as associated data to bind
        the header to the ciphertext.

        Returns:
            Associated data bytes (the encoded header)
        """
        return self.encode()
