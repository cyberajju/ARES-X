"""
HKDF - HMAC-based Key Derivation Function (RFC 5869).

Implements the Extract-then-Expand paradigm for deriving cryptographically
strong keying material from input key material.
"""

import hashlib
import hmac
import math


def hkdf_extract(salt: bytes, ikm: bytes, hash_func: str = "sha256") -> bytes:
    """
    HKDF-Extract: Extract a pseudorandom key from input keying material.

    Args:
        salt: Optional salt value (non-secret random value).
              If empty/None, uses a string of zeroes equal to hash length.
        ikm: Input keying material
        hash_func: Hash function name ('sha256' or 'sha512')

    Returns:
        Pseudorandom key (PRK) of hash output length
    """
    if not salt:
        hash_len = hashlib.new(hash_func).digest_size
        salt = b"\x00" * hash_len
    return hmac.new(salt, ikm, hash_func).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int, hash_func: str = "sha256") -> bytes:
    """
    HKDF-Expand: Expand a pseudorandom key to the desired length.

    Args:
        prk: Pseudorandom key (from extract phase)
        info: Context and application specific information
        length: Output length in bytes (max 255 * hash_length)
        hash_func: Hash function name ('sha256' or 'sha512')

    Returns:
        Output keying material of the requested length

    Raises:
        ValueError: If length exceeds maximum allowed
    """
    hash_len = hashlib.new(hash_func).digest_size
    max_length = 255 * hash_len

    if length > max_length:
        raise ValueError(f"Requested length {length} exceeds maximum {max_length}")
    if length < 0:
        raise ValueError("Length must be non-negative")

    # Number of iterations needed
    n = math.ceil(length / hash_len)

    okm = b""
    t = b""
    for i in range(1, n + 1):
        t = hmac.new(prk, t + info + bytes([i]), hash_func).digest()
        okm += t

    return okm[:length]


def derive_key(ikm: bytes, salt: bytes, info: bytes, length: int, hash_func: str = "sha256") -> bytes:
    """
    Derive a key using HKDF extract-then-expand.

    Convenience function that performs both HKDF phases.

    Args:
        ikm: Input keying material
        salt: Salt for extraction (can be empty)
        info: Context info for expansion
        length: Desired output key length in bytes

    Returns:
        Derived key material of the requested length
    """
    prk = hkdf_extract(salt, ikm, hash_func)
    return hkdf_expand(prk, info, length, hash_func)
