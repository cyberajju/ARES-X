"""
HTTP REST API for ARES-X server.

Provides endpoints for user registration, key bundle retrieval,
prekey upload, and message management. Parses raw HTTP requests
using asyncio StreamReader.
"""

import asyncio
import json
import base64
import logging
import time
from typing import Optional

from server.config import ServerConfig
from server.database import Database

logger = logging.getLogger(__name__)


def parse_http_request(raw: bytes) -> dict:
    """
    Parse a raw HTTP request into components.

    Returns dict with method, path, headers, body.
    """
    # Split headers and body
    if b'\r\n\r\n' in raw:
        header_section, body = raw.split(b'\r\n\r\n', 1)
    elif b'\n\n' in raw:
        header_section, body = raw.split(b'\n\n', 1)
    else:
        header_section = raw
        body = b''

    lines = header_section.decode('utf-8', errors='replace').split('\r\n')
    if not lines:
        lines = header_section.decode('utf-8', errors='replace').split('\n')

    # Parse request line
    request_line = lines[0] if lines else ''
    parts = request_line.split(' ')
    method = parts[0] if len(parts) >= 1 else ''
    path = parts[1] if len(parts) >= 2 else '/'

    # Parse headers
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()

    return {
        'method': method,
        'path': path,
        'headers': headers,
        'body': body,
    }


def build_http_response(status_code: int, status_text: str,
                        body: bytes = b'', content_type: str = 'application/json') -> bytes:
    """Build a raw HTTP response."""
    response = f'HTTP/1.1 {status_code} {status_text}\r\n'
    response += f'Content-Type: {content_type}\r\n'
    response += f'Content-Length: {len(body)}\r\n'
    response += 'Connection: close\r\n'
    response += '\r\n'
    return response.encode('utf-8') + body


class HTTPServer:
    """HTTP REST API server for key management and message retrieval."""

    def __init__(self, config: ServerConfig, database: Database):
        self.config = config
        self.db = database
        self.server = None

    async def start(self):
        """Start the HTTP server."""
        self.server = await asyncio.start_server(
            self.handle_request,
            self.config.host,
            self.config.http_port,
        )
        logger.info(f"HTTP API server listening on {self.config.host}:{self.config.http_port}")

    async def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_request(self, reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter):
        """Handle an incoming HTTP request."""
        try:
            # Read the full request
            raw_request = await self._read_request(reader)
            if not raw_request:
                writer.close()
                return

            request = parse_http_request(raw_request)
            method = request['method']
            path = request['path']

            # Route to handler
            response = await self._route(method, path, request)
            writer.write(response)
            await writer.drain()

        except Exception as e:
            logger.error(f"HTTP request error: {e}")
            error_body = json.dumps({'error': 'Internal server error'}).encode('utf-8')
            writer.write(build_http_response(500, 'Internal Server Error', error_body))
            await writer.drain()
        finally:
            writer.close()

    async def _read_request(self, reader: asyncio.StreamReader) -> Optional[bytes]:
        """Read a complete HTTP request from the stream."""
        # Read headers first
        header_data = b''
        while True:
            line = await reader.readline()
            if not line:
                return None
            header_data += line
            if header_data.endswith(b'\r\n\r\n') or header_data.endswith(b'\n\n'):
                break

        # Check for Content-Length to read body
        header_text = header_data.decode('utf-8', errors='replace').lower()
        content_length = 0
        for line in header_text.split('\n'):
            if line.strip().startswith('content-length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                except ValueError:
                    pass
                break

        body = b''
        if content_length > 0:
            body = await reader.readexactly(content_length)

        return header_data + body

    async def _route(self, method: str, path: str, request: dict) -> bytes:
        """Route request to the appropriate handler."""
        # POST /register
        if method == 'POST' and path == '/register':
            return await self._handle_register(request)

        # GET /keys/{user_id}
        if method == 'GET' and path.startswith('/keys/'):
            user_id = path[len('/keys/'):]
            return await self._handle_get_keys(user_id)

        # POST /prekeys
        if method == 'POST' and path == '/prekeys':
            return await self._handle_upload_prekeys(request)

        # GET /messages/{user_id}
        if method == 'GET' and path.startswith('/messages/'):
            user_id = path[len('/messages/'):]
            return await self._handle_get_messages(user_id)

        # DELETE /messages/{message_id}
        if method == 'DELETE' and path.startswith('/messages/'):
            message_id = path[len('/messages/'):]
            return await self._handle_delete_message(message_id)

        # 404 Not Found
        body = json.dumps({'error': 'Not found'}).encode('utf-8')
        return build_http_response(404, 'Not Found', body)

    async def _handle_register(self, request: dict) -> bytes:
        """Handle POST /register - register a new user with public keys."""
        try:
            data = json.loads(request['body'].decode('utf-8'))
            user_id = data.get('user_id')
            identity_key = data.get('identity_key')
            signed_prekey = data.get('signed_prekey')
            prekey_signature = data.get('prekey_signature')

            if not all([user_id, identity_key, signed_prekey, prekey_signature]):
                body = json.dumps({'error': 'Missing required fields'}).encode('utf-8')
                return build_http_response(400, 'Bad Request', body)

            # Decode base64 keys
            identity_key_bytes = base64.b64decode(identity_key)
            signed_prekey_bytes = base64.b64decode(signed_prekey)
            prekey_sig_bytes = base64.b64decode(prekey_signature)

            self.db.register_user(user_id, identity_key_bytes, signed_prekey_bytes, prekey_sig_bytes)

            body = json.dumps({'status': 'registered', 'user_id': user_id}).encode('utf-8')
            return build_http_response(201, 'Created', body)

        except (json.JSONDecodeError, Exception) as e:
            body = json.dumps({'error': f'Bad request: {str(e)}'}).encode('utf-8')
            return build_http_response(400, 'Bad Request', body)

    async def _handle_get_keys(self, user_id: str) -> bytes:
        """Handle GET /keys/{user_id} - get key bundle for a user."""
        bundle = self.db.get_key_bundle(user_id)
        if bundle is None:
            body = json.dumps({'error': 'User not found'}).encode('utf-8')
            return build_http_response(404, 'Not Found', body)

        # Encode keys as base64
        response_data = {
            'user_id': bundle['user_id'],
            'identity_key': base64.b64encode(bundle['identity_key']).decode('ascii'),
            'signed_prekey': base64.b64encode(bundle['signed_prekey']).decode('ascii'),
            'prekey_signature': base64.b64encode(bundle['prekey_signature']).decode('ascii'),
            'one_time_prekey': (
                base64.b64encode(bundle['one_time_prekey']).decode('ascii')
                if bundle.get('one_time_prekey') else None
            ),
        }
        body = json.dumps(response_data).encode('utf-8')
        return build_http_response(200, 'OK', body)

    async def _handle_upload_prekeys(self, request: dict) -> bytes:
        """Handle POST /prekeys - upload one-time prekeys."""
        try:
            data = json.loads(request['body'].decode('utf-8'))
            user_id = data.get('user_id')
            prekeys = data.get('prekeys', [])

            if not user_id or not prekeys:
                body = json.dumps({'error': 'Missing user_id or prekeys'}).encode('utf-8')
                return build_http_response(400, 'Bad Request', body)

            # Verify user exists
            if self.db.get_user(user_id) is None:
                body = json.dumps({'error': 'User not found'}).encode('utf-8')
                return build_http_response(404, 'Not Found', body)

            # Decode and store prekeys
            prekey_bytes = [base64.b64decode(pk) for pk in prekeys]
            self.db.store_prekeys(user_id, prekey_bytes)

            body = json.dumps({'status': 'stored', 'count': len(prekeys)}).encode('utf-8')
            return build_http_response(201, 'Created', body)

        except (json.JSONDecodeError, Exception) as e:
            body = json.dumps({'error': f'Bad request: {str(e)}'}).encode('utf-8')
            return build_http_response(400, 'Bad Request', body)

    async def _handle_get_messages(self, user_id: str) -> bytes:
        """Handle GET /messages/{user_id} - get pending messages."""
        messages = self.db.get_pending_messages(user_id)

        response_data = {
            'messages': [
                {
                    'message_id': msg['message_id'],
                    'sender_id': msg['sender_id'],
                    'encrypted_blob': base64.b64encode(
                        msg['encrypted_blob'] if isinstance(msg['encrypted_blob'], bytes)
                        else msg['encrypted_blob'].encode('utf-8')
                    ).decode('ascii'),
                    'timestamp': msg['timestamp'],
                }
                for msg in messages
            ]
        }
        body = json.dumps(response_data).encode('utf-8')
        return build_http_response(200, 'OK', body)

    async def _handle_delete_message(self, message_id: str) -> bytes:
        """Handle DELETE /messages/{message_id} - confirm delivery."""
        self.db.delete_message(message_id)
        body = json.dumps({'status': 'deleted', 'message_id': message_id}).encode('utf-8')
        return build_http_response(200, 'OK', body)
