# ARES-X Protocol Specification

## Overview

ARES-X uses a multi-layer protocol stack for secure messaging:

1. **Transport Layer**: WebSocket over TCP (optionally TLS)
2. **Envelope Layer**: JSON-encoded message envelopes with routing metadata
3. **Crypto Layer**: AES-256-GCM encrypted payloads with Double Ratchet key management
4. **Handshake Layer**: X3DH-based initial key agreement

## X3DH Handshake Flow

```
Alice (Initiator)                    Server                    Bob (Responder)
     |                                 |                            |
     |  1. Request Bob's KeyBundle     |                            |
     |-------------------------------->|                            |
     |                                 |                            |
     |  2. Return KeyBundle            |                            |
     |<--------------------------------|                            |
     |                                 |                            |
     |  3. Perform X3DH:              |                            |
     |     DH1 = DH(IK_A, SPK_B)     |                            |
     |     DH2 = DH(EK_A, IK_B)      |                            |
     |     DH3 = DH(EK_A, SPK_B)     |                            |
     |     DH4 = DH(EK_A, OPK_B)     |                            |
     |     SK = HKDF(DH1||DH2||DH3||DH4)                          |
     |                                 |                            |
     |  4. Send HandshakeMessage       |                            |
     |     + first encrypted message   |                            |
     |-------------------------------->|  5. Relay to Bob           |
     |                                 |--------------------------->|
     |                                 |                            |
     |                                 |     6. Bob completes X3DH: |
     |                                 |     DH1 = DH(SPK_B, IK_A) |
     |                                 |     DH2 = DH(IK_B, EK_A)  |
     |                                 |     DH3 = DH(SPK_B, EK_A) |
     |                                 |     DH4 = DH(OPK_B, EK_A) |
     |                                 |     SK = HKDF(same inputs) |
     |                                 |                            |
     |                                 |  7. Bob can now decrypt    |
     |                                 |                            |
```

### Key Bundle

Published to the server by each user:
- `identity_key`: Long-term X25519 public key (32 bytes)
- `signed_prekey`: Medium-term X25519 public key (32 bytes)
- `signed_prekey_signature`: HMAC-SHA512 of signed_prekey with identity private key
- `one_time_prekey`: Ephemeral X25519 public key (32 bytes, optional)

## Double Ratchet Message Flow

```
Alice                                          Bob
  |                                             |
  |  [DH Ratchet Step]                         |
  |  Generate new DH keypair                    |
  |  Compute DH output with Bob's ratchet key  |
  |  Derive new root key + sending chain key    |
  |                                             |
  |  [Symmetric Ratchet]                       |
  |  Derive message key from chain key          |
  |  Encrypt message with AES-256-GCM          |
  |                                             |
  |  Message(header, ciphertext, nonce, tag)    |
  |-------------------------------------------->|
  |                                             |
  |                                             |  [DH Ratchet Step]
  |                                             |  Compute DH with Alice's new key
  |                                             |  Derive root key + receiving chain
  |                                             |
  |                                             |  [Symmetric Ratchet]
  |                                             |  Derive message key from chain
  |                                             |  Decrypt message
  |                                             |
```

### Ratchet Message Header

Each encrypted message includes:
- `dh_public_key`: Sender's current DH ratchet public key (32 bytes)
- `previous_chain_length`: Number of messages in the previous sending chain
- `message_number`: Sequence number within current sending chain

## Wire Protocol Format

### WebSocket Frame Structure

Messages are sent as WebSocket binary frames with a 4-byte length prefix:

```
+--------+--------------------+
| Length  |    JSON Payload    |
| 4 bytes |   variable size    |
+--------+--------------------+
```

### Message Envelope (JSON)

```json
{
  "sender_id": "alice",
  "recipient_id": "bob",
  "timestamp": 1700000000.123,
  "message_type": "text|file|handshake|key_exchange",
  "payload": "<base64-encoded encrypted data>",
  "self_destruct_seconds": null
}
```

### Encrypted Message Payload (JSON, base64-encoded in envelope)

```json
{
  "header": {
    "dh_public_key": "<base64 32 bytes>",
    "previous_chain_length": 0,
    "message_number": 0
  },
  "ciphertext": "<base64>",
  "nonce": "<base64 12 bytes>",
  "tag": "<base64 16 bytes>"
}
```

## API Endpoints

### WebSocket API (port 8443)

| Message Type | Direction | Purpose |
|-------------|-----------|---------|
| `register` | Client -> Server | Register user with key bundle |
| `get_bundle` | Client -> Server | Request peer's key bundle |
| `message` | Client -> Server | Send encrypted message |
| `sync` | Client -> Server | Request queued offline messages |

### HTTP REST API (port 8080)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | POST | Register user and upload key bundle |
| `/bundle/<user_id>` | GET | Retrieve a user's public key bundle |
| `/messages/<user_id>` | GET | Fetch queued messages |
| `/messages/<user_id>` | DELETE | Acknowledge message delivery |
| `/health` | GET | Server health check |

## Message Types

| Type | Description |
|------|-------------|
| `text` | Encrypted text message (UTF-8) |
| `file` | Encrypted file transfer (chunked if > 32KB) |
| `handshake` | X3DH handshake initiation message |
| `key_exchange` | Key bundle exchange or update |
