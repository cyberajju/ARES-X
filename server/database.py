"""
SQLite zero-knowledge storage for ARES-X.

All message content is stored as opaque encrypted blobs.
The server never has access to decryption keys.
Uses WAL mode for concurrent access.
"""

import sqlite3
import time
import secrets
from typing import Optional


class Database:
    """Zero-knowledge SQLite storage backend."""

    def __init__(self, db_path: str = ':memory:'):
        """Initialize database and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    public_identity_key BLOB NOT NULL,
                    signed_prekey BLOB NOT NULL,
                    prekey_signature BLOB NOT NULL,
                    registered_at REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS one_time_prekeys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    prekey BLOB NOT NULL,
                    used INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT NOT NULL,
                    encrypted_blob BLOB NOT NULL,
                    timestamp REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    delivered INTEGER DEFAULT 0
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    connected_at REAL NOT NULL,
                    last_active REAL NOT NULL
                )
            """)
            # Indexes for efficient queries
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_recipient
                ON messages(recipient_id, delivered)
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_expires
                ON messages(expires_at)
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_prekeys_user
                ON one_time_prekeys(user_id, used)
            """)

    def register_user(self, user_id: str, identity_key: bytes,
                      signed_prekey: bytes, prekey_signature: bytes):
        """Register a new user with their public keys."""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO users
                   (user_id, public_identity_key, signed_prekey, prekey_signature, registered_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, identity_key, signed_prekey, prekey_signature, time.time())
            )

    def get_user(self, user_id: str) -> Optional[dict]:
        """Get user record by user_id."""
        cursor = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def get_key_bundle(self, user_id: str) -> Optional[dict]:
        """Get a user's key bundle including one unused one-time prekey if available."""
        user = self.get_user(user_id)
        if user is None:
            return None

        bundle = {
            'user_id': user['user_id'],
            'identity_key': user['public_identity_key'],
            'signed_prekey': user['signed_prekey'],
            'prekey_signature': user['prekey_signature'],
            'one_time_prekey': None,
        }

        # Try to get an unused one-time prekey
        otk = self.consume_one_time_prekey(user_id)
        if otk is not None:
            bundle['one_time_prekey'] = otk

        return bundle

    def store_prekeys(self, user_id: str, prekeys: list):
        """Store one-time prekeys for a user."""
        with self.conn:
            for prekey in prekeys:
                self.conn.execute(
                    "INSERT INTO one_time_prekeys (user_id, prekey, used) VALUES (?, ?, 0)",
                    (user_id, prekey)
                )

    def consume_one_time_prekey(self, user_id: str) -> Optional[bytes]:
        """Consume and return one unused one-time prekey, or None if none available."""
        with self.conn:
            cursor = self.conn.execute(
                "SELECT id, prekey FROM one_time_prekeys WHERE user_id = ? AND used = 0 LIMIT 1",
                (user_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            self.conn.execute(
                "UPDATE one_time_prekeys SET used = 1 WHERE id = ?",
                (row['id'],)
            )
            return bytes(row['prekey'])

    def store_message(self, message_id: str, sender_id: str, recipient_id: str,
                      encrypted_blob: bytes, ttl: int):
        """Store an encrypted message for later delivery."""
        now = time.time()
        expires_at = now + ttl
        with self.conn:
            self.conn.execute(
                """INSERT INTO messages
                   (message_id, sender_id, recipient_id, encrypted_blob, timestamp, expires_at, delivered)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (message_id, sender_id, recipient_id, encrypted_blob, now, expires_at)
            )

    def get_pending_messages(self, recipient_id: str) -> list:
        """Get all pending (undelivered, unexpired) messages for a recipient."""
        now = time.time()
        cursor = self.conn.execute(
            """SELECT message_id, sender_id, recipient_id, encrypted_blob, timestamp, expires_at
               FROM messages
               WHERE recipient_id = ? AND delivered = 0 AND expires_at > ?
               ORDER BY timestamp ASC""",
            (recipient_id, now)
        )
        return [dict(row) for row in cursor.fetchall()]

    def mark_delivered(self, message_id: str):
        """Mark a message as delivered."""
        with self.conn:
            self.conn.execute(
                "UPDATE messages SET delivered = 1 WHERE message_id = ?",
                (message_id,)
            )

    def delete_message(self, message_id: str):
        """Delete a message by ID."""
        with self.conn:
            self.conn.execute(
                "DELETE FROM messages WHERE message_id = ?",
                (message_id,)
            )

    def cleanup_expired(self):
        """Delete all expired messages."""
        now = time.time()
        with self.conn:
            self.conn.execute(
                "DELETE FROM messages WHERE expires_at <= ?",
                (now,)
            )

    def update_session(self, session_id: str, user_id: str):
        """Create or update a session record."""
        now = time.time()
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO sessions
                   (session_id, user_id, connected_at, last_active)
                   VALUES (?, ?, ?, ?)""",
                (session_id, user_id, now, now)
            )

    def remove_session(self, session_id: str):
        """Remove a session record."""
        with self.conn:
            self.conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )

    def get_message_count(self, recipient_id: str) -> int:
        """Get count of pending messages for a recipient."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM messages WHERE recipient_id = ? AND delivered = 0",
            (recipient_id,)
        )
        return cursor.fetchone()[0]

    def close(self):
        """Close the database connection."""
        self.conn.close()
