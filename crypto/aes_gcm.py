"""
AES-256-GCM authenticated encryption via ctypes bindings to OpenSSL libcrypto.

Provides encrypt and decrypt functions using the EVP cipher API.
Uses 12-byte random nonce and 16-byte authentication tag.
Supports Additional Authenticated Data (AAD).
"""

import ctypes
import ctypes.util
from ctypes import c_void_p, c_int, c_char_p, c_size_t, POINTER, byref, create_string_buffer

from crypto.utils import generate_random_bytes

# Constants
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32
EVP_CTRL_GCM_GET_TAG = 0x10
EVP_CTRL_GCM_SET_TAG = 0x11

# Load OpenSSL libcrypto
_lib_path = ctypes.util.find_library("crypto")
if _lib_path is None:
    raise RuntimeError("libcrypto not found")
_libcrypto = ctypes.CDLL(_lib_path)

# Setup function signatures
_libcrypto.EVP_CIPHER_CTX_new.argtypes = []
_libcrypto.EVP_CIPHER_CTX_new.restype = c_void_p

_libcrypto.EVP_CIPHER_CTX_free.argtypes = [c_void_p]
_libcrypto.EVP_CIPHER_CTX_free.restype = None

_libcrypto.EVP_aes_256_gcm.argtypes = []
_libcrypto.EVP_aes_256_gcm.restype = c_void_p

_libcrypto.EVP_EncryptInit_ex.argtypes = [c_void_p, c_void_p, c_void_p, c_char_p, c_char_p]
_libcrypto.EVP_EncryptInit_ex.restype = c_int

_libcrypto.EVP_EncryptUpdate.argtypes = [c_void_p, c_char_p, POINTER(c_int), c_char_p, c_int]
_libcrypto.EVP_EncryptUpdate.restype = c_int

_libcrypto.EVP_EncryptFinal_ex.argtypes = [c_void_p, c_char_p, POINTER(c_int)]
_libcrypto.EVP_EncryptFinal_ex.restype = c_int

_libcrypto.EVP_CIPHER_CTX_ctrl.argtypes = [c_void_p, c_int, c_int, c_void_p]
_libcrypto.EVP_CIPHER_CTX_ctrl.restype = c_int

_libcrypto.EVP_DecryptInit_ex.argtypes = [c_void_p, c_void_p, c_void_p, c_char_p, c_char_p]
_libcrypto.EVP_DecryptInit_ex.restype = c_int

_libcrypto.EVP_DecryptUpdate.argtypes = [c_void_p, c_char_p, POINTER(c_int), c_char_p, c_int]
_libcrypto.EVP_DecryptUpdate.restype = c_int

_libcrypto.EVP_DecryptFinal_ex.argtypes = [c_void_p, c_char_p, POINTER(c_int)]
_libcrypto.EVP_DecryptFinal_ex.restype = c_int


def encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> tuple:
    """
    Encrypt plaintext using AES-256-GCM.

    Args:
        key: 32-byte encryption key
        plaintext: Data to encrypt
        aad: Additional Authenticated Data (optional)

    Returns:
        Tuple of (nonce, ciphertext, tag) where nonce is 12 bytes and tag is 16 bytes

    Raises:
        ValueError: If key is not 32 bytes
        RuntimeError: If encryption fails
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")

    nonce = generate_random_bytes(NONCE_SIZE)
    ctx = _libcrypto.EVP_CIPHER_CTX_new()
    if not ctx:
        raise RuntimeError("Failed to create cipher context")

    try:
        # Initialize encryption with AES-256-GCM
        cipher = _libcrypto.EVP_aes_256_gcm()
        if _libcrypto.EVP_EncryptInit_ex(ctx, cipher, None, None, None) != 1:
            raise RuntimeError("EVP_EncryptInit_ex failed (cipher setup)")

        # Set nonce
        if _libcrypto.EVP_EncryptInit_ex(ctx, None, None, key, nonce) != 1:
            raise RuntimeError("EVP_EncryptInit_ex failed (key/nonce)")

        # Process AAD if provided
        outlen = c_int(0)
        if aad:
            if _libcrypto.EVP_EncryptUpdate(ctx, None, byref(outlen), aad, len(aad)) != 1:
                raise RuntimeError("EVP_EncryptUpdate failed (AAD)")

        # Encrypt plaintext
        ciphertext_buf = create_string_buffer(len(plaintext) + 16)
        outlen = c_int(0)
        if _libcrypto.EVP_EncryptUpdate(ctx, ciphertext_buf, byref(outlen), plaintext, len(plaintext)) != 1:
            raise RuntimeError("EVP_EncryptUpdate failed (plaintext)")
        ciphertext_len = outlen.value

        # Finalize
        final_buf = create_string_buffer(16)
        final_len = c_int(0)
        if _libcrypto.EVP_EncryptFinal_ex(ctx, final_buf, byref(final_len)) != 1:
            raise RuntimeError("EVP_EncryptFinal_ex failed")
        ciphertext_len += final_len.value

        # Get authentication tag
        tag_buf = create_string_buffer(TAG_SIZE)
        if _libcrypto.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, TAG_SIZE, tag_buf) != 1:
            raise RuntimeError("Failed to get GCM tag")

        ciphertext = ciphertext_buf.raw[:ciphertext_len]
        tag = tag_buf.raw[:TAG_SIZE]

        return (nonce, ciphertext, tag)

    finally:
        _libcrypto.EVP_CIPHER_CTX_free(ctx)


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes = b"") -> bytes:
    """
    Decrypt ciphertext using AES-256-GCM.

    Args:
        key: 32-byte encryption key
        nonce: 12-byte nonce used during encryption
        ciphertext: Encrypted data
        tag: 16-byte authentication tag
        aad: Additional Authenticated Data (must match encryption)

    Returns:
        Decrypted plaintext bytes

    Raises:
        ValueError: If key, nonce, or tag are wrong size
        RuntimeError: If decryption or authentication fails
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"Nonce must be {NONCE_SIZE} bytes, got {len(nonce)}")
    if len(tag) != TAG_SIZE:
        raise ValueError(f"Tag must be {TAG_SIZE} bytes, got {len(tag)}")

    ctx = _libcrypto.EVP_CIPHER_CTX_new()
    if not ctx:
        raise RuntimeError("Failed to create cipher context")

    try:
        # Initialize decryption with AES-256-GCM
        cipher = _libcrypto.EVP_aes_256_gcm()
        if _libcrypto.EVP_DecryptInit_ex(ctx, cipher, None, None, None) != 1:
            raise RuntimeError("EVP_DecryptInit_ex failed (cipher setup)")

        # Set key and nonce
        if _libcrypto.EVP_DecryptInit_ex(ctx, None, None, key, nonce) != 1:
            raise RuntimeError("EVP_DecryptInit_ex failed (key/nonce)")

        # Process AAD if provided
        outlen = c_int(0)
        if aad:
            if _libcrypto.EVP_DecryptUpdate(ctx, None, byref(outlen), aad, len(aad)) != 1:
                raise RuntimeError("EVP_DecryptUpdate failed (AAD)")

        # Decrypt ciphertext
        plaintext_buf = create_string_buffer(len(ciphertext) + 16)
        outlen = c_int(0)
        if _libcrypto.EVP_DecryptUpdate(ctx, plaintext_buf, byref(outlen), ciphertext, len(ciphertext)) != 1:
            raise RuntimeError("EVP_DecryptUpdate failed (ciphertext)")
        plaintext_len = outlen.value

        # Set expected tag before finalization
        tag_buf = create_string_buffer(TAG_SIZE)
        tag_buf.value = tag
        if _libcrypto.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, TAG_SIZE, tag_buf) != 1:
            raise RuntimeError("Failed to set GCM tag")

        # Finalize and verify authentication
        final_buf = create_string_buffer(16)
        final_len = c_int(0)
        ret = _libcrypto.EVP_DecryptFinal_ex(ctx, final_buf, byref(final_len))
        if ret != 1:
            raise RuntimeError("Decryption failed: authentication tag mismatch")
        plaintext_len += final_len.value

        return plaintext_buf.raw[:plaintext_len]

    finally:
        _libcrypto.EVP_CIPHER_CTX_free(ctx)
