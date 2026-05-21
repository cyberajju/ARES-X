"""
Offline message delivery queue for ARES-X.

When recipients are offline, messages are stored encrypted in the database.
On reconnect, queued messages are delivered in order.
Includes TTL-based expiration and size limits.
"""

import secrets
import time
from typing import Optional

from server.config import ServerConfig
from server.database import Database


class MessageQueue:
    """Offline message queue with persistence via database."""

    def __init__(self, config: ServerConfig, database: Database):
        """Initialize message queue with config and database backend."""
        self.config = config
        self.db = database

    def enqueue(self, sender_id: str, recipient_id: str,
                encrypted_blob: bytes,
                self_destruct_seconds: Optional[int] = None) -> Optional[str]:
        """
        Enqueue an encrypted message for offline delivery.

        Args:
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            encrypted_blob: Opaque encrypted message data
            self_destruct_seconds: Optional TTL override for self-destructing messages

        Returns:
            message_id if enqueued successfully, None if queue is full
        """
        # Check queue size limit
        pending_count = self.db.get_message_count(recipient_id)
        if pending_count >= self.config.max_offline_queue:
            return None

        # Check message size limit
        if len(encrypted_blob) > self.config.max_message_size:
            return None

        # Use self-destruct timer if specified, otherwise default TTL
        ttl = self_destruct_seconds if self_destruct_seconds is not None else self.config.message_ttl

        message_id = secrets.token_hex(16)
        self.db.store_message(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            encrypted_blob=encrypted_blob,
            ttl=ttl,
        )
        return message_id

    def dequeue(self, recipient_id: str) -> list:
        """
        Get all pending messages for a recipient.

        Returns list of message dicts with message_id, sender_id,
        encrypted_blob, and timestamp.
        """
        return self.db.get_pending_messages(recipient_id)

    def acknowledge(self, message_id: str):
        """Confirm delivery of a message, removing it from the queue."""
        self.db.delete_message(message_id)

    def run_cleanup(self):
        """Remove expired messages from the queue."""
        self.db.cleanup_expired()
