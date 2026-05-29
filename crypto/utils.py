"""
Cryptographic utility functions.

Provides secure random generation, constant-time comparison,
base64 encoding helpers, and byte manipulation utilities.
"""

import base64
import hmac
import secrets


def generate_random_bytes(n: int) -> bytes:
    """Generate n cryptographically secure random bytes."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return secrets.token_bytes(n)


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Compare two byte strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a, b)


def bytes_to_base64(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string."""
    return base64.urlsafe_b64encode(data).decode("ascii")


def base64_to_bytes(data: str) -> bytes:
    """Decode URL-safe base64 string to bytes."""
    return base64.urlsafe_b64decode(data.encode("ascii"))


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte strings. They must be the same length."""
    if len(a) != len(b):
        raise ValueError("Byte strings must be the same length for XOR")
    return bytes(x ^ y for x, y in zip(a, b))
