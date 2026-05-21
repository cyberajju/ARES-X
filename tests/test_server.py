"""
Tests for ARES-X server components.

Tests database CRUD, message queue, WebSocket frame encoding/decoding,
WebSocket handshake, HTTP request parsing, and API route matching.
"""

import unittest
import asyncio
import time
import json
import base64
import hashlib
import struct
import os
import tempfile

from server.config import ServerConfig
from server.database import Database
from server.message_queue import MessageQueue
from server.websocket_server import (
    compute_accept_key, encode_frame, decode_frame, mask_payload,
    OPCODE_TEXT, OPCODE_BINARY, OPCODE_CLOSE, OPCODE_PING, OPCODE_PONG,
    WebSocketServer, WebSocketConnection, WS_MAGIC_GUID,
)
from server.api import (
    parse_http_request, build_http_response, HTTPServer,
)


class TestServerConfig(unittest.TestCase):
    """Test server configuration."""

    def test_default_config(self):
        config = ServerConfig()
        self.assertEqual(config.host, '0.0.0.0')
        self.assertEqual(config.ws_port, 8765)
        self.assertEqual(config.http_port, 8080)
        self.assertEqual(config.max_message_size, 65536)
        self.assertEqual(config.message_ttl, 604800)
        self.assertEqual(config.max_offline_queue, 1000)

    def test_from_env(self):
        os.environ['ARES_WS_PORT'] = '9999'
        os.environ['ARES_HTTP_PORT'] = '8888'
        try:
            config = ServerConfig.from_env()
            self.assertEqual(config.ws_port, 9999)
            self.assertEqual(config.http_port, 8888)
        finally:
            del os.environ['ARES_WS_PORT']
            del os.environ['ARES_HTTP_PORT']


class TestDatabase(unittest.TestCase):
    """Test SQLite database operations."""

    def setUp(self):
        self.db = Database(':memory:')

    def tearDown(self):
        self.db.close()

    def test_register_user(self):
        self.db.register_user('alice', b'identity_key', b'signed_prekey', b'signature')
        user = self.db.get_user('alice')
        self.assertIsNotNone(user)
        self.assertEqual(user['user_id'], 'alice')
        self.assertEqual(bytes(user['public_identity_key']), b'identity_key')
        self.assertEqual(bytes(user['signed_prekey']), b'signed_prekey')
        self.assertEqual(bytes(user['prekey_signature']), b'signature')

    def test_get_user_not_found(self):
        user = self.db.get_user('nonexistent')
        self.assertIsNone(user)

    def test_register_user_replace(self):
        self.db.register_user('alice', b'key1', b'prekey1', b'sig1')
        self.db.register_user('alice', b'key2', b'prekey2', b'sig2')
        user = self.db.get_user('alice')
        self.assertEqual(bytes(user['public_identity_key']), b'key2')

    def test_store_and_consume_prekeys(self):
        self.db.register_user('alice', b'ik', b'spk', b'sig')
        prekeys = [b'prekey1', b'prekey2', b'prekey3']
        self.db.store_prekeys('alice', prekeys)

        # Consume prekeys one by one
        pk1 = self.db.consume_one_time_prekey('alice')
        self.assertEqual(pk1, b'prekey1')
        pk2 = self.db.consume_one_time_prekey('alice')
        self.assertEqual(pk2, b'prekey2')
        pk3 = self.db.consume_one_time_prekey('alice')
        self.assertEqual(pk3, b'prekey3')

        # No more prekeys
        pk4 = self.db.consume_one_time_prekey('alice')
        self.assertIsNone(pk4)

    def test_get_key_bundle(self):
        self.db.register_user('bob', b'ik', b'spk', b'sig')
        self.db.store_prekeys('bob', [b'otk1'])

        bundle = self.db.get_key_bundle('bob')
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle['user_id'], 'bob')
        self.assertEqual(bundle['identity_key'], b'ik')
        self.assertEqual(bundle['signed_prekey'], b'spk')
        self.assertEqual(bundle['prekey_signature'], b'sig')
        self.assertEqual(bundle['one_time_prekey'], b'otk1')

    def test_get_key_bundle_no_prekey(self):
        self.db.register_user('bob', b'ik', b'spk', b'sig')
        bundle = self.db.get_key_bundle('bob')
        self.assertIsNotNone(bundle)
        self.assertIsNone(bundle['one_time_prekey'])

    def test_get_key_bundle_user_not_found(self):
        bundle = self.db.get_key_bundle('nonexistent')
        self.assertIsNone(bundle)

    def test_store_and_get_messages(self):
        msg_id = 'msg001'
        self.db.store_message(msg_id, 'alice', 'bob', b'encrypted_data', 3600)

        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['message_id'], 'msg001')
        self.assertEqual(messages[0]['sender_id'], 'alice')
        self.assertEqual(bytes(messages[0]['encrypted_blob']), b'encrypted_data')

    def test_mark_delivered(self):
        self.db.store_message('msg001', 'alice', 'bob', b'data', 3600)
        self.db.mark_delivered('msg001')
        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 0)

    def test_delete_message(self):
        self.db.store_message('msg001', 'alice', 'bob', b'data', 3600)
        self.db.delete_message('msg001')
        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 0)

    def test_message_ttl_expiry(self):
        # Store with TTL of 0 (already expired)
        self.db.store_message('msg001', 'alice', 'bob', b'data', 0)
        # Wait a tiny bit to ensure it's expired
        time.sleep(0.01)
        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 0)

    def test_cleanup_expired(self):
        # Store message with 0 TTL
        self.db.store_message('msg001', 'alice', 'bob', b'data', 0)
        time.sleep(0.01)
        self.db.cleanup_expired()
        # Verify it's gone even if we ignore delivery status
        cursor = self.db.conn.execute(
            "SELECT * FROM messages WHERE message_id = ?", ('msg001',)
        )
        self.assertIsNone(cursor.fetchone())

    def test_session_management(self):
        self.db.update_session('sess1', 'alice')
        cursor = self.db.conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", ('sess1',)
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['user_id'], 'alice')

        self.db.remove_session('sess1')
        cursor = self.db.conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", ('sess1',)
        )
        self.assertIsNone(cursor.fetchone())

    def test_message_count(self):
        self.db.store_message('msg1', 'alice', 'bob', b'data1', 3600)
        self.db.store_message('msg2', 'alice', 'bob', b'data2', 3600)
        self.assertEqual(self.db.get_message_count('bob'), 2)
        self.assertEqual(self.db.get_message_count('alice'), 0)

    def test_message_ordering(self):
        self.db.store_message('msg1', 'alice', 'bob', b'first', 3600)
        time.sleep(0.01)
        self.db.store_message('msg2', 'alice', 'bob', b'second', 3600)
        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['message_id'], 'msg1')
        self.assertEqual(messages[1]['message_id'], 'msg2')


class TestMessageQueue(unittest.TestCase):
    """Test offline message queue."""

    def setUp(self):
        self.config = ServerConfig(max_offline_queue=5, max_message_size=1024, message_ttl=3600)
        self.db = Database(':memory:')
        self.mq = MessageQueue(self.config, self.db)

    def tearDown(self):
        self.db.close()

    def test_enqueue_dequeue(self):
        msg_id = self.mq.enqueue('alice', 'bob', b'encrypted_payload')
        self.assertIsNotNone(msg_id)

        messages = self.mq.dequeue('bob')
        self.assertEqual(len(messages), 1)
        self.assertEqual(bytes(messages[0]['encrypted_blob']), b'encrypted_payload')

    def test_acknowledge_removes_message(self):
        msg_id = self.mq.enqueue('alice', 'bob', b'data')
        self.mq.acknowledge(msg_id)
        messages = self.mq.dequeue('bob')
        self.assertEqual(len(messages), 0)

    def test_queue_limit(self):
        # Fill queue to max
        for i in range(5):
            result = self.mq.enqueue('alice', 'bob', f'msg{i}'.encode())
            self.assertIsNotNone(result)

        # Next enqueue should fail
        result = self.mq.enqueue('alice', 'bob', b'overflow')
        self.assertIsNone(result)

    def test_message_size_limit(self):
        # Message too large
        large_data = b'x' * 2048
        result = self.mq.enqueue('alice', 'bob', large_data)
        self.assertIsNone(result)

    def test_self_destruct_ttl(self):
        msg_id = self.mq.enqueue('alice', 'bob', b'data', self_destruct_seconds=0)
        self.assertIsNotNone(msg_id)
        time.sleep(0.01)
        messages = self.mq.dequeue('bob')
        self.assertEqual(len(messages), 0)

    def test_cleanup(self):
        self.mq.enqueue('alice', 'bob', b'data', self_destruct_seconds=0)
        time.sleep(0.01)
        self.mq.run_cleanup()
        messages = self.mq.dequeue('bob')
        self.assertEqual(len(messages), 0)


class TestWebSocketFrames(unittest.TestCase):
    """Test WebSocket frame encoding and decoding."""

    def _run(self, coro):
        """Run a coroutine synchronously."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_compute_accept_key(self):
        # Verify Sec-WebSocket-Accept computation per RFC 6455
        # SHA-1(key + "258EAFA5-E914-47DA-95CA-5AB9FE30B130") then base64
        client_key = "dGhlIHNhbXBsZSBub25jZQ=="
        expected = "ps+H7Q4QchZCcO+zkBqB7yJ2aqw="
        result = compute_accept_key(client_key)
        self.assertEqual(result, expected)
        # Verify the computation is SHA-1 of key+GUID, base64 encoded
        import hashlib as _hl
        manual = base64.b64encode(
            _hl.sha1((client_key + WS_MAGIC_GUID).encode('ascii')).digest()
        ).decode('ascii')
        self.assertEqual(result, manual)

    def test_encode_decode_text_frame(self):
        payload = b'Hello, World!'
        # Encode with mask (simulating client)
        frame = encode_frame(OPCODE_TEXT, payload, mask=True)

        # Decode it
        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_TEXT)
        self.assertEqual(decoded_payload, payload)

    def test_encode_decode_binary_frame(self):
        payload = b'\x00\x01\x02\x03' * 100
        frame = encode_frame(OPCODE_BINARY, payload, mask=True)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_BINARY)
        self.assertEqual(decoded_payload, payload)

    def test_encode_decode_no_mask(self):
        """Server-to-client frames are not masked."""
        payload = b'Server message'
        frame = encode_frame(OPCODE_TEXT, payload, mask=False)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_TEXT)
        self.assertEqual(decoded_payload, payload)

    def test_encode_decode_ping_pong(self):
        ping_data = b'ping-data'
        frame = encode_frame(OPCODE_PING, ping_data)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_PING)
        self.assertEqual(decoded_payload, ping_data)

    def test_encode_decode_close_frame(self):
        close_code = struct.pack('!H', 1000) + b'Normal closure'
        frame = encode_frame(OPCODE_CLOSE, close_code)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_CLOSE)
        code = struct.unpack('!H', decoded_payload[:2])[0]
        self.assertEqual(code, 1000)

    def test_medium_payload(self):
        """Test payload with 126 <= length < 65536."""
        payload = b'x' * 200
        frame = encode_frame(OPCODE_BINARY, payload, mask=True)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_BINARY)
        self.assertEqual(len(decoded_payload), 200)
        self.assertEqual(decoded_payload, payload)

    def test_large_payload(self):
        """Test payload with length >= 65536."""
        payload = b'y' * 70000
        frame = encode_frame(OPCODE_BINARY, payload, mask=False)

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_BINARY)
        self.assertEqual(len(decoded_payload), 70000)
        self.assertEqual(decoded_payload, payload)

    def test_mask_payload(self):
        payload = b'Hello'
        key = b'\x37\xfa\x21\x3d'
        masked = mask_payload(payload, key)
        # Applying mask twice should give original
        unmasked = mask_payload(masked, key)
        self.assertEqual(unmasked, payload)

    def test_empty_payload(self):
        frame = encode_frame(OPCODE_PING, b'')

        async def decode():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader)

        opcode, decoded_payload = self._run(decode())
        self.assertEqual(opcode, OPCODE_PING)
        self.assertEqual(decoded_payload, b'')

    def test_frame_exceeding_max_size_rejected(self):
        """Frames with payload exceeding max_payload_size are rejected."""
        # Create a frame with 1000-byte payload
        payload = b'x' * 1000
        frame = encode_frame(OPCODE_BINARY, payload, mask=False)

        async def decode_with_limit():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            # Set max to 500 bytes - the 1000-byte frame should be rejected
            return await decode_frame(reader, max_payload_size=500)

        with self.assertRaises(ValueError) as ctx:
            self._run(decode_with_limit())
        self.assertIn('1000', str(ctx.exception))
        self.assertIn('500', str(ctx.exception))

    def test_frame_within_max_size_accepted(self):
        """Frames within max_payload_size are accepted normally."""
        payload = b'x' * 100
        frame = encode_frame(OPCODE_BINARY, payload, mask=False)

        async def decode_with_limit():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader, max_payload_size=500)

        opcode, decoded_payload = self._run(decode_with_limit())
        self.assertEqual(opcode, OPCODE_BINARY)
        self.assertEqual(decoded_payload, payload)

    def test_frame_size_limit_zero_disables_check(self):
        """When max_payload_size is 0, no size limit is enforced."""
        payload = b'y' * 70000
        frame = encode_frame(OPCODE_BINARY, payload, mask=False)

        async def decode_no_limit():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader, max_payload_size=0)

        opcode, decoded_payload = self._run(decode_no_limit())
        self.assertEqual(opcode, OPCODE_BINARY)
        self.assertEqual(len(decoded_payload), 70000)

    def test_frame_size_limit_extended_length(self):
        """Size limit catches oversized frames using 16-bit extended length."""
        # Create a frame with 200-byte payload (uses 16-bit length since >= 126)
        payload = b'z' * 200
        frame = encode_frame(OPCODE_BINARY, payload, mask=False)

        async def decode_with_limit():
            reader = asyncio.StreamReader()
            reader.feed_data(frame)
            return await decode_frame(reader, max_payload_size=100)

        with self.assertRaises(ValueError):
            self._run(decode_with_limit())


class TestHTTPParsing(unittest.TestCase):
    """Test HTTP request parsing and response building."""

    def test_parse_get_request(self):
        raw = b'GET /keys/alice HTTP/1.1\r\nHost: localhost\r\nAccept: application/json\r\n\r\n'
        req = parse_http_request(raw)
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/keys/alice')
        self.assertEqual(req['headers']['host'], 'localhost')

    def test_parse_post_request_with_body(self):
        body = b'{"user_id": "alice"}'
        raw = (
            b'POST /register HTTP/1.1\r\n'
            b'Content-Type: application/json\r\n'
            b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
            b'\r\n' + body
        )
        req = parse_http_request(raw)
        self.assertEqual(req['method'], 'POST')
        self.assertEqual(req['path'], '/register')
        self.assertEqual(req['body'], body)

    def test_parse_delete_request(self):
        raw = b'DELETE /messages/msg123 HTTP/1.1\r\nHost: localhost\r\n\r\n'
        req = parse_http_request(raw)
        self.assertEqual(req['method'], 'DELETE')
        self.assertEqual(req['path'], '/messages/msg123')

    def test_build_response_200(self):
        body = b'{"status": "ok"}'
        response = build_http_response(200, 'OK', body)
        self.assertIn(b'HTTP/1.1 200 OK', response)
        self.assertIn(b'Content-Type: application/json', response)
        self.assertIn(b'Content-Length: 16', response)
        self.assertTrue(response.endswith(body))

    def test_build_response_404(self):
        body = b'{"error": "not found"}'
        response = build_http_response(404, 'Not Found', body)
        self.assertIn(b'HTTP/1.1 404 Not Found', response)

    def test_build_response_empty_body(self):
        response = build_http_response(204, 'No Content', b'')
        self.assertIn(b'Content-Length: 0', response)


class TestHTTPAPI(unittest.TestCase):
    """Test HTTP API endpoint routing and handling."""

    def setUp(self):
        self.config = ServerConfig()
        self.db = Database(':memory:')
        self.http_server = HTTPServer(self.config, self.db)

    def tearDown(self):
        self.db.close()

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_register_endpoint(self):
        body = json.dumps({
            'user_id': 'alice',
            'identity_key': base64.b64encode(b'identity_key_32bytes_padding!!!!').decode(),
            'signed_prekey': base64.b64encode(b'signed_prekey_32bytes_padding!!!').decode(),
            'prekey_signature': base64.b64encode(b'signature_64bytes_padding' + b'!' * 39).decode(),
        }).encode()

        request = {
            'method': 'POST',
            'path': '/register',
            'headers': {'content-type': 'application/json'},
            'body': body,
        }

        response = self._run(self.http_server._route('POST', '/register', request))
        self.assertIn(b'201', response)
        self.assertIn(b'registered', response)

        # Verify user was stored
        user = self.db.get_user('alice')
        self.assertIsNotNone(user)

    def test_get_keys_endpoint(self):
        self.db.register_user('bob', b'ik_data', b'spk_data', b'sig_data')
        self.db.store_prekeys('bob', [b'otk1'])

        response = self._run(self.http_server._route('GET', '/keys/bob', {}))
        self.assertIn(b'200', response)

        # Parse response body
        body_start = response.find(b'\r\n\r\n') + 4
        body = json.loads(response[body_start:])
        self.assertEqual(body['user_id'], 'bob')
        self.assertEqual(base64.b64decode(body['identity_key']), b'ik_data')

    def test_get_keys_not_found(self):
        response = self._run(self.http_server._route('GET', '/keys/unknown', {}))
        self.assertIn(b'404', response)

    def test_upload_prekeys_endpoint(self):
        self.db.register_user('alice', b'ik', b'spk', b'sig')
        body = json.dumps({
            'user_id': 'alice',
            'prekeys': [
                base64.b64encode(b'prekey1').decode(),
                base64.b64encode(b'prekey2').decode(),
            ],
        }).encode()

        request = {
            'method': 'POST',
            'path': '/prekeys',
            'headers': {'content-type': 'application/json'},
            'body': body,
        }

        response = self._run(self.http_server._route('POST', '/prekeys', request))
        self.assertIn(b'201', response)
        self.assertIn(b'"count": 2', response)

    def test_get_messages_endpoint(self):
        self.db.store_message('msg1', 'alice', 'bob', b'encrypted', 3600)

        response = self._run(self.http_server._route('GET', '/messages/bob', {}))
        self.assertIn(b'200', response)

        body_start = response.find(b'\r\n\r\n') + 4
        body = json.loads(response[body_start:])
        self.assertEqual(len(body['messages']), 1)
        self.assertEqual(body['messages'][0]['message_id'], 'msg1')

    def test_delete_message_endpoint(self):
        self.db.store_message('msg1', 'alice', 'bob', b'data', 3600)

        response = self._run(self.http_server._route('DELETE', '/messages/msg1', {}))
        self.assertIn(b'200', response)

        # Verify message was deleted
        messages = self.db.get_pending_messages('bob')
        self.assertEqual(len(messages), 0)

    def test_404_unknown_endpoint(self):
        response = self._run(self.http_server._route('GET', '/unknown', {}))
        self.assertIn(b'404', response)

    def test_register_missing_fields(self):
        body = json.dumps({'user_id': 'alice'}).encode()
        request = {
            'method': 'POST',
            'path': '/register',
            'headers': {},
            'body': body,
        }
        response = self._run(self.http_server._route('POST', '/register', request))
        self.assertIn(b'400', response)


class TestServerStartStop(unittest.TestCase):
    """Test that the server can start and accept connections."""

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_websocket_server_start_stop(self):
        async def run_test():
            config = ServerConfig(ws_port=0, http_port=0)
            db = Database(':memory:')
            mq = MessageQueue(config, db)
            ws = WebSocketServer(config, db, mq)

            await ws.start()
            # Verify server is running
            self.assertIsNotNone(ws.server)
            self.assertTrue(ws.server.is_serving())

            await ws.stop()
            db.close()

        self._run(run_test())

    def test_http_server_start_stop(self):
        async def run_test():
            config = ServerConfig(http_port=0)
            db = Database(':memory:')
            http = HTTPServer(config, db)

            await http.start()
            self.assertIsNotNone(http.server)
            self.assertTrue(http.server.is_serving())

            await http.stop()
            db.close()

        self._run(run_test())


if __name__ == '__main__':
    unittest.main()
