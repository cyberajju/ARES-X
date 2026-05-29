"""
ARES-X Core Cryptographic Primitives

Military-grade encryption using:
- AES-256-GCM (via OpenSSL libcrypto)
- X25519 key exchange (via OpenSSL libcrypto)
- HKDF key derivation (RFC 5869)
- HMAC-SHA512 message authentication
"""

from crypto.utils import (
    generate_random_bytes,
    constant_time_compare,
    bytes_to_base64,
    base64_to_bytes,
    xor_bytes,
)
from crypto.aes_gcm import encrypt, decrypt
from crypto.key_exchange import X25519KeyPair, compute_shared_secret
from crypto.hkdf import hkdf_extract, hkdf_expand, derive_key
from crypto.hmac_auth import sign, verify
from crypto.post_quantum import PostQuantumKEM, HybridKeyExchange

__all__ = [
    "generate_random_bytes",
    "constant_time_compare",
    "bytes_to_base64",
    "base64_to_bytes",
    "xor_bytes",
    "encrypt",
    "decrypt",
    "X25519KeyPair",
    "compute_shared_secret",
    "hkdf_extract",
    "hkdf_expand",
    "derive_key",
    "sign",
    "verify",
    "PostQuantumKEM",
    "HybridKeyExchange",
]
