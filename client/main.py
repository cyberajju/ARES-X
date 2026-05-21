"""
ARES-X Client entry point.

Provides the main AresClient class that manages connection to the server,
registration, session establishment, and message exchange.
"""

import asyncio
import json
import time
from typing import Optional, Callable

from client.key_store import KeyStore
from client.session import SessionManager
from client.messenger import Messenger
from protocol.messages import KeyBundle, MessageEnvelope, HandshakeMessage


class AresClient:
    """
    Main ARES-X client that connects to the server and manages messaging.

    Handles WebSocket connection, registration, session establishment,
    message sending/receiving, and auto-reconnection.
    """

    def __init__(
        self,
        user_id: str,
        server_host: str = "localhost",
        server_port: int = 8443,
        key_store_path: str = ":memory:",
        passphrase: str = "",
    ):
        """
        Initialize the ARES-X client.

        Args:
            user_id: Unique identifier for this user
            server_host: Server hostname
            server_port: Server port
            key_store_path: Path to key storage database
            passphrase: Passphrase for key encryption
        """
        self.user_id = user_id
        self.server_host = server_host
        self.server_port = server_port
        self._key_store = KeyStore(key_store_path, passphrase)
        self._session_manager = SessionManager(self._key_store)
        self._messenger = Messenger(self._session_manager, user_id)
        self._connected = False
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._message_callback: Optional[Callable] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

    @property
    def key_store(self) -> KeyStore:
        """Access the key store."""
        return self._key_store

    @property
    def session_manager(self) -> SessionManager:
        """Access the session manager."""
        return self._session_manager

    @property
    def messenger(self) -> Messenger:
        """Access the messenger."""
        return self._messenger

    async def connect(self):
        """
        Connect to the ARES-X server via TCP.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.server_host, self.server_port
            )
            self._connected = True
            self._reconnect_attempts = 0
        except (OSError, ConnectionRefusedError) as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to server: {e}")

    async def register(self):
        """
        Register with the server by uploading our public key bundle.

        Generates identity, signed prekey, and one-time prekeys if needed,
        then sends the public bundle to the server.
        """
        # Generate keys if not already present
        if self._key_store.get_identity_key() is None:
            self._key_store.generate_identity()
            self._key_store.generate_signed_prekey()
            self._key_store.generate_one_time_prekeys(20)

        bundle = self._key_store.export_public_bundle()
        registration = {
            "type": "register",
            "user_id": self.user_id,
            "bundle": bundle.to_bytes().decode("utf-8"),
        }

        if self._writer:
            data = json.dumps(registration).encode("utf-8")
            self._writer.write(len(data).to_bytes(4, "big") + data)
            await self._writer.drain()

    async def start_session(self, peer_id: str, peer_bundle: Optional[KeyBundle] = None):
        """
        Start an encrypted session with a peer.

        If peer_bundle is not provided, requests it from the server.

        Args:
            peer_id: Peer's user identifier
            peer_bundle: Peer's public key bundle (optional)
        """
        if peer_bundle is None:
            # Request bundle from server
            request = {
                "type": "get_bundle",
                "user_id": peer_id,
            }
            if self._writer:
                data = json.dumps(request).encode("utf-8")
                self._writer.write(len(data).to_bytes(4, "big") + data)
                await self._writer.drain()
            return

        # Create session using the bundle
        self._session_manager.create_session_initiator(peer_id, peer_bundle)

    async def send_message(self, peer_id: str, text: str, self_destruct: Optional[int] = None):
        """
        Send an encrypted text message to a peer.

        Args:
            peer_id: Recipient's user identifier
            text: Message text
            self_destruct: Optional self-destruct timer in seconds
        """
        envelope = self._messenger.compose_message(peer_id, text, self_destruct)

        if self._writer:
            data = envelope.to_bytes()
            self._writer.write(len(data).to_bytes(4, "big") + data)
            await self._writer.drain()

    async def receive_loop(self):
        """
        Listen for incoming messages and route them to the appropriate handler.

        Runs indefinitely until connection is lost.
        """
        while self._connected and self._reader:
            try:
                # Read message length (4 bytes)
                length_bytes = await self._reader.readexactly(4)
                msg_length = int.from_bytes(length_bytes, "big")

                # Read message data
                data = await self._reader.readexactly(msg_length)
                envelope = MessageEnvelope.from_bytes(data)

                # Route based on message type
                if envelope.message_type == "handshake":
                    self._messenger.handle_handshake(envelope)
                elif envelope.message_type == "text":
                    result = self._messenger.receive_message(envelope)
                    if self._message_callback:
                        self._message_callback(result)
                elif envelope.message_type == "file":
                    result = self._messenger.receive_file_message(envelope)
                    if self._message_callback:
                        self._message_callback(result)

            except asyncio.IncompleteReadError:
                self._connected = False
                break
            except Exception:
                continue

    async def sync_offline_messages(self):
        """
        Fetch and process any queued messages from the server.

        Sends a sync request and processes all queued messages.
        """
        if not self._writer:
            return

        request = {
            "type": "sync",
            "user_id": self.user_id,
        }
        data = json.dumps(request).encode("utf-8")
        self._writer.write(len(data).to_bytes(4, "big") + data)
        await self._writer.drain()

    async def reconnect(self):
        """
        Attempt to reconnect to the server with exponential backoff.
        """
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            wait_time = min(2 ** self._reconnect_attempts, 30)
            await asyncio.sleep(wait_time)
            try:
                await self.connect()
                return
            except ConnectionError:
                continue
        raise ConnectionError("Max reconnection attempts exceeded")

    def on_message(self, callback: Callable):
        """
        Set callback for incoming messages.

        Args:
            callback: Function to call with received message dict
        """
        self._message_callback = callback

    async def close(self):
        """Close connection and clean up."""
        self._connected = False
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._key_store.close()
