"""
HMAC-SHA512 message authentication.

Provides sign and verify functions for message authentication codes
with constant-time comparison to prevent timing attacks.
"""

import hmac as _hmac

from crypto.utils import constant_time_compare


def sign(key: bytes, message: bytes) -> bytes:
    """
    Create an HMAC-SHA512 signature for a message.

    Args:
        key: Secret key for HMAC
        message: Message to authenticate

    Returns:
        64-byte HMAC-SHA512 signature
    """
    return _hmac.new(key, message, "sha512").digest()


def verify(key: bytes, message: bytes, signature: bytes) -> bool:
    """
    Verify an HMAC-SHA512 signature for a message.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        key: Secret key for HMAC
        message: Message that was authenticated
        signature: Signature to verify

    Returns:
        True if signature is valid, False otherwise
    """
    expected = sign(key, message)
    return constant_time_compare(expected, signature)
