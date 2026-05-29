# ARES-X

**Military-grade end-to-end encrypted messaging system**

ARES-X is a secure messaging platform built entirely with Python standard library.
It implements the Signal Protocol (X3DH + Double Ratchet) for forward-secret,
authenticated messaging with zero-knowledge server architecture.

## Architecture

```
+-------------------+          +-------------------+          +-------------------+
|   Alice Client    |          |   ARES-X Server   |          |    Bob Client     |
|                   |          |                   |          |                   |
| +---------------+ |  WebSocket  +---------------+ |  WebSocket  +---------------+ |
| | Key Store     | |<-------->| | Message Queue | |<-------->| | Key Store     | |
| +---------------+ |          | +---------------+ |          | +---------------+ |
| | Session Mgr   | |          | | Database      | |          | | Session Mgr   | |
| +---------------+ |          | | (zero-knowledge)| |         | +---------------+ |
| | Messenger     | |          | +---------------+ |          | | Messenger     | |
| +---------------+ |          |                   |          | +---------------+ |
| | Double Ratchet| |          | No plaintext.     |          | | Double Ratchet| |
| +---------------+ |          | No private keys.  |          | +---------------+ |
+-------------------+          +-------------------+          +-------------------+
```

## Security Features

- **End-to-end encryption**: AES-256-GCM authenticated encryption
- **Forward secrecy**: Double Ratchet with continuous DH key rotation
- **X3DH handshake**: Extended Triple Diffie-Hellman for session establishment
- **Zero-knowledge server**: Server relays encrypted blobs only, never sees plaintext
- **Safety numbers**: Out-of-band identity verification between peers
- **Self-destruct messages**: Timed message deletion after delivery
- **Key store encryption**: Private keys encrypted at rest with passphrase
- **Authenticated messages**: GCM tags prevent tampering and forgery

## Directory Structure

```
ARES-X/
├── crypto/                 # Cryptographic primitives
│   ├── aes_gcm.py         # AES-256-GCM via OpenSSL EVP API
│   ├── key_exchange.py    # X25519 ECDH key exchange
│   ├── double_ratchet.py  # Double Ratchet Algorithm
│   ├── hkdf.py            # HKDF key derivation (RFC 5869)
│   ├── hmac_auth.py       # HMAC-SHA512 authentication
│   └── utils.py           # Secure random, constant-time compare
├── protocol/              # Protocol definitions
│   ├── messages.py        # Message types (KeyBundle, Envelope, etc.)
│   ├── handshake.py       # X3DH initiator and responder
│   └── ratchet_header.py  # Ratchet message header encoding
├── server/                # Relay server
│   ├── websocket_server.py # WebSocket server (asyncio)
│   ├── api.py             # HTTP REST API
│   ├── database.py        # SQLite zero-knowledge storage
│   ├── message_queue.py   # Offline message queuing
│   └── main.py            # Server entry point
├── client/                # Client library
│   ├── key_store.py       # Local key management (SQLite + encryption)
│   ├── session.py         # E2E session management
│   ├── messenger.py       # Message compose/receive pipeline
│   ├── main.py            # Client entry point
│   └── cli.py             # Terminal chat interface
├── tests/                 # Test suite
│   ├── test_crypto.py     # Cryptographic primitive tests
│   ├── test_protocol.py   # Protocol tests
│   ├── test_server.py     # Server component tests
│   └── test_e2e.py        # End-to-end integration tests
└── docs/                  # Documentation
    ├── SECURITY.md        # Security architecture
    ├── PROTOCOL.md        # Protocol specification
    └── THREAT_MODEL.md    # Threat model analysis
```

## How to Run

### Start the Server

```bash
python3 -m server.main --host 0.0.0.0 --port 8443
```

### Connect a Client

```bash
python3 -m client.cli --server localhost --port 8443 --user-id alice --db-path alice.db
```

### Example Usage

```
ares-x> /register
[OK] Registered with server. Keys generated.

ares-x> /connect bob
[OK] Session established with bob

ares-x> /msg Hello Bob, this is a secure message!
[SENT] -> bob: Hello Bob, this is a secure message!

ares-x> /verify
[VERIFY] Safety number with bob:
  12345 67890 11223 34455 66778 89900
  Compare this with your peer to verify identity.

ares-x> /destruct 30
[OK] Next message will self-destruct in 30s

ares-x> /msg This message will disappear
[SENT] -> bob: This message will disappear [self-destruct: 30s]
```

## Testing

Run the full test suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Run specific test modules:

```bash
python3 -m unittest tests.test_crypto -v
python3 -m unittest tests.test_protocol -v
python3 -m unittest tests.test_server -v
python3 -m unittest tests.test_e2e -v
```

## Technology

- **Language**: Python 3.9+ (standard library only, zero external dependencies)
- **Crypto Backend**: OpenSSL libcrypto via ctypes (AES-256-GCM, X25519)
- **Storage**: SQLite3 (both server and client)
- **Networking**: asyncio (WebSocket and HTTP)
- **Key Exchange**: X25519 (Curve25519 ECDH)
- **Encryption**: AES-256-GCM (128-bit tags, 96-bit nonces)
- **Key Derivation**: HKDF-SHA256 (RFC 5869)
- **Authentication**: HMAC-SHA512
- **Ratchet**: Double Ratchet Algorithm (Signal Protocol)
- **Handshake**: Extended Triple Diffie-Hellman (X3DH)
