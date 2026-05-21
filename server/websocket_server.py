"""
WebSocket server implementation for ARES-X (RFC 6455).

Implements WebSocket protocol from scratch using asyncio raw sockets.
Handles HTTP upgrade handshake, frame parsing/building, ping/pong keepalive,
and message routing between connected clients.
"""

import asyncio
import base64
import hashlib
import struct
import logging
import secrets
import time
from typing import Optional

from server.config import ServerConfig
from server.database import Database
from server.message_queue import MessageQueue

logger = logging.getLogger(__name__)

# WebSocket magic GUID per RFC 6455
WS_MAGIC_GUID = "258EAFA5-E914-47DA-95CA-5AB9FE30B130"

# WebSocket opcodes
OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def compute_accept_key(key: str) -> str:
    """Compute Sec-WebSocket-Accept value from client key."""
    combined = key.strip() + WS_MAGIC_GUID
    sha1_hash = hashlib.sha1(combined.encode('ascii')).digest()
    return base64.b64encode(sha1_hash).decode('ascii')


def mask_payload(payload: bytes, masking_key: bytes) -> bytes:
    """Apply or remove XOR mask to payload data."""
    result = bytearray(len(payload))
    for i in range(len(payload)):
        result[i] = payload[i] ^ masking_key[i % 4]
    return bytes(result)


def encode_frame(opcode: int, payload: bytes, mask: bool = False) -> bytes:
    """
    Encode a WebSocket frame.

    Args:
        opcode: Frame opcode (text, binary, close, ping, pong)
        payload: Frame payload data
        mask: Whether to mask the payload (client-to-server only)

    Returns:
        Encoded frame bytes
    """
    frame = bytearray()

    # First byte: FIN=1 + opcode
    frame.append(0x80 | opcode)

    # Second byte: MASK bit + payload length
    length = len(payload)
    mask_bit = 0x80 if mask else 0x00

    if length < 126:
        frame.append(mask_bit | length)
    elif length < 65536:
        frame.append(mask_bit | 126)
        frame.extend(struct.pack('!H', length))
    else:
        frame.append(mask_bit | 127)
        frame.extend(struct.pack('!Q', length))

    if mask:
        masking_key = secrets.token_bytes(4)
        frame.extend(masking_key)
        frame.extend(mask_payload(payload, masking_key))
    else:
        frame.extend(payload)

    return bytes(frame)


async def decode_frame(reader: asyncio.StreamReader):
    """
    Decode a WebSocket frame from a stream reader.

    Returns:
        Tuple of (opcode, payload) or (None, None) on connection close.
    """
    # Read first two bytes
    data = await reader.readexactly(2)
    first_byte = data[0]
    second_byte = data[1]

    # Parse FIN and opcode
    fin = (first_byte >> 7) & 1
    opcode = first_byte & 0x0F

    # Parse mask and payload length
    is_masked = (second_byte >> 7) & 1
    payload_length = second_byte & 0x7F

    if payload_length == 126:
        data = await reader.readexactly(2)
        payload_length = struct.unpack('!H', data)[0]
    elif payload_length == 127:
        data = await reader.readexactly(8)
        payload_length = struct.unpack('!Q', data)[0]

    # Read masking key if present
    masking_key = None
    if is_masked:
        masking_key = await reader.readexactly(4)

    # Read payload
    payload = await reader.readexactly(payload_length)

    # Unmask if needed
    if masking_key:
        payload = mask_payload(payload, masking_key)

    return opcode, payload


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.user_id = None
        self.session_id = secrets.token_hex(16)
        self.connected_at = time.time()
        self.last_active = time.time()
        self._closed = False

    async def send_frame(self, opcode: int, payload: bytes):
        """Send a WebSocket frame (server-to-client, no mask)."""
        if self._closed:
            return
        frame = encode_frame(opcode, payload, mask=False)
        self.writer.write(frame)
        await self.writer.drain()

    async def read_frame(self):
        """Read a WebSocket frame. Returns (opcode, payload)."""
        return await decode_frame(self.reader)

    async def send_message(self, data: bytes):
        """Send a binary message to the client."""
        await self.send_frame(OPCODE_BINARY, data)

    async def send_text(self, text: str):
        """Send a text message to the client."""
        await self.send_frame(OPCODE_TEXT, text.encode('utf-8'))

    async def close(self, code: int = 1000, reason: str = ''):
        """Send close frame and close connection."""
        if self._closed:
            return
        self._closed = True
        payload = struct.pack('!H', code) + reason.encode('utf-8')
        try:
            await self.send_frame(OPCODE_CLOSE, payload)
            self.writer.close()
        except Exception:
            pass

    @property
    def is_closed(self) -> bool:
        return self._closed


class WebSocketServer:
    """WebSocket server for real-time message relay."""

    def __init__(self, config: ServerConfig, database: Database, message_queue: MessageQueue):
        self.config = config
        self.db = database
        self.mq = message_queue
        self.connections = {}  # user_id -> WebSocketConnection
        self.server = None

    async def start(self):
        """Start the WebSocket server."""
        self.server = await asyncio.start_server(
            self.handle_connection,
            self.config.host,
            self.config.ws_port,
        )
        logger.info(f"WebSocket server listening on {self.config.host}:{self.config.ws_port}")

    async def stop(self):
        """Stop the WebSocket server and close all connections."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Close all active connections
        for user_id, conn in list(self.connections.items()):
            await conn.close()
        self.connections.clear()

    async def handle_connection(self, reader: asyncio.StreamReader,
                                writer: asyncio.StreamWriter):
        """Handle a new incoming connection."""
        conn = None
        try:
            # Perform WebSocket upgrade handshake
            if not await self._do_handshake(reader, writer):
                writer.close()
                return

            conn = WebSocketConnection(reader, writer)

            # First message must be authentication
            authenticated = await self._authenticate(conn)
            if not authenticated:
                await conn.close(code=4001, reason='Authentication required')
                return

            # Register connection
            self.connections[conn.user_id] = conn
            self.db.update_session(conn.session_id, conn.user_id)
            logger.info(f"User {conn.user_id} connected (session {conn.session_id})")

            # Deliver pending messages
            await self._deliver_pending(conn)

            # Message loop
            await self._message_loop(conn)

        except asyncio.IncompleteReadError:
            logger.debug("Connection closed unexpectedly")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            if conn and conn.user_id:
                self.connections.pop(conn.user_id, None)
                self.db.remove_session(conn.session_id)
                logger.info(f"User {conn.user_id} disconnected")
            if conn and not conn.is_closed:
                await conn.close()

    async def _do_handshake(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter) -> bool:
        """Perform HTTP upgrade to WebSocket."""
        # Read HTTP request
        request_line = await reader.readline()
        if not request_line:
            return False

        headers = {}
        while True:
            line = await reader.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            if b':' in line:
                key, value = line.decode('utf-8').split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Validate upgrade request
        ws_key = headers.get('sec-websocket-key')
        if not ws_key:
            writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            await writer.drain()
            return False

        # Compute accept key
        accept_key = compute_accept_key(ws_key)

        # Send upgrade response
        response = (
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {accept_key}\r\n'
            '\r\n'
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()
        return True

    async def _authenticate(self, conn: WebSocketConnection) -> bool:
        """
        Authenticate the client. First message must contain user_id.
        In production this would verify a signed token.
        """
        try:
            opcode, payload = await asyncio.wait_for(
                conn.read_frame(), timeout=10.0
            )
            if opcode not in (OPCODE_TEXT, OPCODE_BINARY):
                return False

            # Parse auth message: expect JSON with user_id
            import json
            auth_data = json.loads(payload.decode('utf-8'))
            user_id = auth_data.get('user_id')
            if not user_id:
                return False

            # Verify user exists
            user = self.db.get_user(user_id)
            if user is None:
                return False

            conn.user_id = user_id
            # Send auth success
            await conn.send_text(json.dumps({'status': 'authenticated', 'user_id': user_id}))
            return True

        except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
            return False

    async def _deliver_pending(self, conn: WebSocketConnection):
        """Deliver queued messages to a newly connected client."""
        messages = self.mq.dequeue(conn.user_id)
        for msg in messages:
            try:
                await conn.send_message(msg['encrypted_blob'])
                self.mq.acknowledge(msg['message_id'])
            except Exception:
                break

    async def _message_loop(self, conn: WebSocketConnection):
        """Main message processing loop."""
        import json

        while not conn.is_closed:
            try:
                opcode, payload = await asyncio.wait_for(
                    conn.read_frame(),
                    timeout=self.config.ping_interval + self.config.ping_timeout
                )
            except asyncio.TimeoutError:
                # Send ping
                await conn.send_frame(OPCODE_PING, b'')
                try:
                    opcode, payload = await asyncio.wait_for(
                        conn.read_frame(), timeout=self.config.ping_timeout
                    )
                except asyncio.TimeoutError:
                    logger.info(f"Ping timeout for {conn.user_id}")
                    break

            conn.last_active = time.time()

            if opcode == OPCODE_CLOSE:
                await conn.close()
                break
            elif opcode == OPCODE_PING:
                await conn.send_frame(OPCODE_PONG, payload)
            elif opcode == OPCODE_PONG:
                continue
            elif opcode in (OPCODE_TEXT, OPCODE_BINARY):
                await self._route_message(conn, payload)

    async def _route_message(self, sender_conn: WebSocketConnection, payload: bytes):
        """Route a message to its recipient."""
        import json

        try:
            # Parse envelope to get recipient
            envelope = json.loads(payload.decode('utf-8'))
            recipient_id = envelope.get('recipient_id')
            if not recipient_id:
                return

            # If recipient is online, deliver directly
            recipient_conn = self.connections.get(recipient_id)
            if recipient_conn and not recipient_conn.is_closed:
                await recipient_conn.send_message(payload)
            else:
                # Store for offline delivery
                self_destruct = envelope.get('self_destruct_seconds')
                self.mq.enqueue(
                    sender_id=sender_conn.user_id,
                    recipient_id=recipient_id,
                    encrypted_blob=payload,
                    self_destruct_seconds=self_destruct,
                )
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to route message: {e}")
