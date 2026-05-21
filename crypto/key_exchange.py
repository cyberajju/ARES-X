"""
X25519 Diffie-Hellman key exchange via ctypes bindings to OpenSSL libcrypto.

Provides key generation, public key extraction, and shared secret computation
using the EVP_PKEY API with NID_X25519.
"""

import ctypes
import ctypes.util
from ctypes import c_void_p, c_int, c_char_p, c_size_t, POINTER, byref, create_string_buffer

from crypto.utils import generate_random_bytes

# Constants
NID_X25519 = 1034
KEY_SIZE = 32

# Load OpenSSL libcrypto
_lib_path = ctypes.util.find_library("crypto")
if _lib_path is None:
    raise RuntimeError("libcrypto not found")
_libcrypto = ctypes.CDLL(_lib_path)

# Setup function signatures
_libcrypto.EVP_PKEY_new_raw_private_key.argtypes = [c_int, c_void_p, c_char_p, c_size_t]
_libcrypto.EVP_PKEY_new_raw_private_key.restype = c_void_p

_libcrypto.EVP_PKEY_new_raw_public_key.argtypes = [c_int, c_void_p, c_char_p, c_size_t]
_libcrypto.EVP_PKEY_new_raw_public_key.restype = c_void_p

_libcrypto.EVP_PKEY_get_raw_public_key.argtypes = [c_void_p, c_char_p, POINTER(c_size_t)]
_libcrypto.EVP_PKEY_get_raw_public_key.restype = c_int

_libcrypto.EVP_PKEY_get_raw_private_key.argtypes = [c_void_p, c_char_p, POINTER(c_size_t)]
_libcrypto.EVP_PKEY_get_raw_private_key.restype = c_int

_libcrypto.EVP_PKEY_free.argtypes = [c_void_p]
_libcrypto.EVP_PKEY_free.restype = None

_libcrypto.EVP_PKEY_CTX_new.argtypes = [c_void_p, c_void_p]
_libcrypto.EVP_PKEY_CTX_new.restype = c_void_p

_libcrypto.EVP_PKEY_CTX_free.argtypes = [c_void_p]
_libcrypto.EVP_PKEY_CTX_free.restype = None

_libcrypto.EVP_PKEY_derive_init.argtypes = [c_void_p]
_libcrypto.EVP_PKEY_derive_init.restype = c_int

_libcrypto.EVP_PKEY_derive_set_peer.argtypes = [c_void_p, c_void_p]
_libcrypto.EVP_PKEY_derive_set_peer.restype = c_int

_libcrypto.EVP_PKEY_derive.argtypes = [c_void_p, c_char_p, POINTER(c_size_t)]
_libcrypto.EVP_PKEY_derive.restype = c_int


def _create_pkey_from_private(private_key_bytes: bytes) -> c_void_p:
    """Create an EVP_PKEY from raw private key bytes."""
    pkey = _libcrypto.EVP_PKEY_new_raw_private_key(
        NID_X25519, None, private_key_bytes, c_size_t(KEY_SIZE)
    )
    if not pkey:
        raise RuntimeError("Failed to create EVP_PKEY from private key")
    return pkey


def _create_pkey_from_public(public_key_bytes: bytes) -> c_void_p:
    """Create an EVP_PKEY from raw public key bytes."""
    pkey = _libcrypto.EVP_PKEY_new_raw_public_key(
        NID_X25519, None, public_key_bytes, c_size_t(KEY_SIZE)
    )
    if not pkey:
        raise RuntimeError("Failed to create EVP_PKEY from public key")
    return pkey


def _extract_public_key(pkey: c_void_p) -> bytes:
    """Extract raw public key bytes from an EVP_PKEY."""
    pub_len = c_size_t(KEY_SIZE)
    pub_buf = create_string_buffer(KEY_SIZE)
    if _libcrypto.EVP_PKEY_get_raw_public_key(pkey, pub_buf, byref(pub_len)) != 1:
        raise RuntimeError("Failed to extract public key")
    return pub_buf.raw[:pub_len.value]


def _extract_private_key(pkey: c_void_p) -> bytes:
    """Extract raw private key bytes from an EVP_PKEY."""
    priv_len = c_size_t(KEY_SIZE)
    priv_buf = create_string_buffer(KEY_SIZE)
    if _libcrypto.EVP_PKEY_get_raw_private_key(pkey, priv_buf, byref(priv_len)) != 1:
        raise RuntimeError("Failed to extract private key")
    return priv_buf.raw[:priv_len.value]


class X25519KeyPair:
    """
    X25519 key pair for Diffie-Hellman key exchange.

    Generates or wraps a private key and derives the corresponding public key.
    """

    def __init__(self, private_key_bytes: bytes, public_key_bytes: bytes):
        """Initialize with raw key bytes. Use generate() or from_private_key() instead."""
        self._private_key = private_key_bytes
        self._public_key = public_key_bytes

    @classmethod
    def generate(cls) -> "X25519KeyPair":
        """Generate a new random X25519 key pair."""
        # Generate 32 random bytes as private key seed
        private_bytes = generate_random_bytes(KEY_SIZE)

        # Create EVP_PKEY to let OpenSSL clamp the key and derive public key
        pkey = _create_pkey_from_private(private_bytes)
        try:
            # Extract the actual private key (after clamping)
            actual_private = _extract_private_key(pkey)
            # Derive public key
            public_bytes = _extract_public_key(pkey)
        finally:
            _libcrypto.EVP_PKEY_free(pkey)

        return cls(actual_private, public_bytes)

    @classmethod
    def from_private_key(cls, private_key_bytes: bytes) -> "X25519KeyPair":
        """Create a key pair from an existing private key."""
        if len(private_key_bytes) != KEY_SIZE:
            raise ValueError(f"Private key must be {KEY_SIZE} bytes, got {len(private_key_bytes)}")

        pkey = _create_pkey_from_private(private_key_bytes)
        try:
            actual_private = _extract_private_key(pkey)
            public_bytes = _extract_public_key(pkey)
        finally:
            _libcrypto.EVP_PKEY_free(pkey)

        return cls(actual_private, public_bytes)

    @property
    def public_key(self) -> bytes:
        """Get the 32-byte public key."""
        return self._public_key

    @property
    def private_key(self) -> bytes:
        """Get the 32-byte private key."""
        return self._private_key


def compute_shared_secret(private_key_pair: X25519KeyPair, peer_public_key: bytes) -> bytes:
    """
    Compute X25519 shared secret using local private key and peer's public key.

    Args:
        private_key_pair: Local X25519 key pair
        peer_public_key: Peer's 32-byte public key

    Returns:
        32-byte shared secret

    Raises:
        ValueError: If peer public key is wrong size
        RuntimeError: If key derivation fails
    """
    if len(peer_public_key) != KEY_SIZE:
        raise ValueError(f"Peer public key must be {KEY_SIZE} bytes, got {len(peer_public_key)}")

    # Create EVP_PKEY for our private key
    our_pkey = _create_pkey_from_private(private_key_pair.private_key)
    # Create EVP_PKEY for peer's public key
    peer_pkey = _create_pkey_from_public(peer_public_key)

    try:
        # Create derivation context
        ctx = _libcrypto.EVP_PKEY_CTX_new(our_pkey, None)
        if not ctx:
            raise RuntimeError("Failed to create EVP_PKEY_CTX")

        try:
            # Initialize key derivation
            if _libcrypto.EVP_PKEY_derive_init(ctx) != 1:
                raise RuntimeError("EVP_PKEY_derive_init failed")

            # Set peer's public key
            if _libcrypto.EVP_PKEY_derive_set_peer(ctx, peer_pkey) != 1:
                raise RuntimeError("EVP_PKEY_derive_set_peer failed")

            # Determine shared secret length
            secret_len = c_size_t(0)
            if _libcrypto.EVP_PKEY_derive(ctx, None, byref(secret_len)) != 1:
                raise RuntimeError("EVP_PKEY_derive failed (length query)")

            # Derive the shared secret
            secret_buf = create_string_buffer(secret_len.value)
            if _libcrypto.EVP_PKEY_derive(ctx, secret_buf, byref(secret_len)) != 1:
                raise RuntimeError("EVP_PKEY_derive failed")

            return secret_buf.raw[:secret_len.value]

        finally:
            _libcrypto.EVP_PKEY_CTX_free(ctx)

    finally:
        _libcrypto.EVP_PKEY_free(our_pkey)
        _libcrypto.EVP_PKEY_free(peer_pkey)
