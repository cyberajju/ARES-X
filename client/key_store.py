"""
Local key storage and management for ARES-X client.

Stores identity keys, signed prekeys, and one-time prekeys in SQLite.
Private key material is encrypted with AES-GCM if a passphrase is provided.
"""

import sqlite3
import hashlib
import os
import time
from typing import Optional, List, Tuple

from crypto.key_exchange import X25519KeyPair
from crypto.hkdf import derive_key
from crypto.aes_gcm import encrypt as aes_encrypt, decrypt as aes_decrypt
from crypto.hmac_auth import sign as hmac_sign
from crypto.utils import generate_random_bytes
from protocol.messages import KeyBundle


# Constants
KEY_ENCRYPTION_INFO = b"ARES-X_KEY_STORE_ENCRYPTION"
SIGNING_INFO = b"ARES-X_PREKEY_SIGNING"


class KeyStore:
    """
    Local key storage and management using SQLite.

    Stores identity keypairs, signed prekeys with rotation timestamps,
    and one-time prekeys (batch generated). Private key material is
    encrypted with AES-GCM using a key derived from the user passphrase.
    """

    def __init__(self, db_path: str, passphrase: str = ""):
        """
        Initialize key store with SQLite storage.

        Args:
            db_path: Path to SQLite database file (use ':memory:' for in-memory)
            passphrase: Optional passphrase to encrypt private keys at rest
        """
        self.db_path = db_path
        self._passphrase = passphrase
        self._encryption_key: Optional[bytes] = None

        if passphrase:
            # Derive encryption key from passphrase via HKDF
            salt = b"ARES-X_KEYSTORE_SALT"
            self._encryption_key = derive_key(
                ikm=passphrase.encode("utf-8"),
                salt=salt,
                info=KEY_ENCRYPTION_INFO,
                length=32,
            )

        self._conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        """Create storage tables if they don't exist."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS identity_keys (
                id INTEGER PRIMARY KEY,
                private_key BLOB NOT NULL,
                public_key BLOB NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signed_prekeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                private_key BLOB NOT NULL,
                public_key BLOB NOT NULL,
                signature BLOB NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS one_time_prekeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                private_key BLOB NOT NULL,
                public_key BLOB NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
        self._conn.commit()

    def _protect_key(self, key_bytes: bytes) -> bytes:
        """Encrypt private key if passphrase is set, otherwise return raw."""
        if self._encryption_key:
            nonce, ciphertext, tag = aes_encrypt(self._encryption_key, key_bytes)
            return nonce + tag + ciphertext
        return key_bytes

    def _unprotect_key(self, stored: bytes) -> bytes:
        """Decrypt private key if passphrase is set, otherwise return raw."""
        if self._encryption_key:
            nonce = stored[:12]
            tag = stored[12:28]
            ciphertext = stored[28:]
            return aes_decrypt(self._encryption_key, nonce, ciphertext, tag)
        return stored

    def generate_identity(self) -> X25519KeyPair:
        """
        Generate and store a new identity keypair.

        Returns:
            The generated X25519KeyPair
        """
        keypair = X25519KeyPair.generate()
        protected_private = self._protect_key(keypair.private_key)

        cursor = self._conn.cursor()
        # Remove any existing identity (only one allowed)
        cursor.execute("DELETE FROM identity_keys")
        cursor.execute(
            "INSERT INTO identity_keys (id, private_key, public_key, created_at) VALUES (1, ?, ?, ?)",
            (protected_private, keypair.public_key, time.time()),
        )
        self._conn.commit()
        return keypair

    def get_identity_key(self) -> Optional[X25519KeyPair]:
        """
        Load identity keypair from storage.

        Returns:
            X25519KeyPair or None if no identity exists
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT private_key, public_key FROM identity_keys WHERE id=1")
        row = cursor.fetchone()
        if row is None:
            return None

        private_key = self._unprotect_key(row[0])
        return X25519KeyPair.from_private_key(private_key)

    def generate_signed_prekey(self) -> Tuple[bytes, bytes]:
        """
        Generate a signed prekey and store it.

        Signs the prekey public key with the identity key using HMAC-SHA512.

        Returns:
            Tuple of (public_key, signature)

        Raises:
            RuntimeError: If no identity key exists
        """
        identity = self.get_identity_key()
        if identity is None:
            raise RuntimeError("No identity key found. Generate identity first.")

        keypair = X25519KeyPair.generate()
        # Sign the prekey public key with identity private key (using HMAC)
        signature = hmac_sign(identity.private_key, keypair.public_key)

        protected_private = self._protect_key(keypair.private_key)
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO signed_prekeys (private_key, public_key, signature, created_at) VALUES (?, ?, ?, ?)",
            (protected_private, keypair.public_key, signature, time.time()),
        )
        self._conn.commit()
        return keypair.public_key, signature

    def generate_one_time_prekeys(self, count: int = 20) -> List[bytes]:
        """
        Batch generate one-time prekeys.

        Args:
            count: Number of prekeys to generate

        Returns:
            List of public keys
        """
        public_keys = []
        cursor = self._conn.cursor()

        for _ in range(count):
            keypair = X25519KeyPair.generate()
            protected_private = self._protect_key(keypair.private_key)
            cursor.execute(
                "INSERT INTO one_time_prekeys (private_key, public_key) VALUES (?, ?)",
                (protected_private, keypair.public_key),
            )
            public_keys.append(keypair.public_key)

        self._conn.commit()
        return public_keys

    def export_public_bundle(self) -> KeyBundle:
        """
        Export public key bundle for registration with server.

        Returns:
            KeyBundle containing identity key, signed prekey, signature,
            and optionally a one-time prekey

        Raises:
            RuntimeError: If required keys are missing
        """
        identity = self.get_identity_key()
        if identity is None:
            raise RuntimeError("No identity key found.")

        cursor = self._conn.cursor()
        # Get most recent signed prekey
        cursor.execute(
            "SELECT public_key, signature FROM signed_prekeys ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No signed prekey found.")
        signed_prekey_pub, signature = row

        # Get an unused one-time prekey
        cursor.execute(
            "SELECT public_key FROM one_time_prekeys WHERE used=0 LIMIT 1"
        )
        otp_row = cursor.fetchone()
        one_time_prekey = otp_row[0] if otp_row else None

        return KeyBundle(
            identity_key=identity.public_key,
            signed_prekey=signed_prekey_pub,
            signed_prekey_signature=signature,
            one_time_prekey=one_time_prekey,
        )

    def get_prekey_pair(self, public_key: bytes) -> Optional[X25519KeyPair]:
        """
        Retrieve a keypair by its public key.

        Searches signed prekeys and one-time prekeys.

        Args:
            public_key: The public key to search for

        Returns:
            X25519KeyPair or None if not found
        """
        cursor = self._conn.cursor()

        # Check signed prekeys
        cursor.execute(
            "SELECT private_key FROM signed_prekeys WHERE public_key=?",
            (public_key,),
        )
        row = cursor.fetchone()
        if row:
            private_key = self._unprotect_key(row[0])
            return X25519KeyPair.from_private_key(private_key)

        # Check one-time prekeys
        cursor.execute(
            "SELECT id, private_key FROM one_time_prekeys WHERE public_key=?",
            (public_key,),
        )
        row = cursor.fetchone()
        if row:
            otp_id, protected_private = row
            private_key = self._unprotect_key(protected_private)
            # Mark as used
            cursor.execute(
                "UPDATE one_time_prekeys SET used=1 WHERE id=?", (otp_id,)
            )
            self._conn.commit()
            return X25519KeyPair.from_private_key(private_key)

        return None

    def get_signed_prekey(self) -> Optional[X25519KeyPair]:
        """
        Get the most recent signed prekey pair.

        Returns:
            X25519KeyPair or None
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT private_key FROM signed_prekeys ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            private_key = self._unprotect_key(row[0])
            return X25519KeyPair.from_private_key(private_key)
        return None

    def close(self):
        """Close database connection."""
        self._conn.close()
