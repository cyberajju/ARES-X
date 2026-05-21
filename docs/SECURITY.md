# ARES-X Security Architecture

## Threat Model Overview

ARES-X is designed to provide end-to-end encrypted messaging with forward secrecy,
protecting message content from all parties except the sender and recipient. The
server operates in a zero-knowledge configuration -- it relays encrypted blobs
without access to plaintext content, metadata about message content, or private keys.

## Cryptographic Primitives

| Primitive | Algorithm | Purpose |
|-----------|-----------|---------|
| Key Exchange | X25519 (Curve25519 ECDH) | Elliptic curve Diffie-Hellman for shared secrets |
| Symmetric Encryption | AES-256-GCM | Authenticated encryption with associated data |
| Key Derivation | HKDF-SHA256 (RFC 5869) | Deriving keys from shared secrets |
| Message Auth | HMAC-SHA512 | Prekey signatures and message authentication |
| Hashing | SHA-256 | Safety numbers, fingerprints |
| Random | os.urandom (via secrets) | Key generation, nonces |

### Rationale

- **X25519**: Small key size (32 bytes), constant-time operations, no weak points from
  parameter choices. Widely reviewed and deployed.
- **AES-256-GCM**: NIST-approved, hardware-accelerated on modern CPUs, provides both
  confidentiality and integrity in a single operation.
- **HKDF**: Standard key derivation with extract-then-expand paradigm, suitable for
  deriving multiple independent keys from a single shared secret.

## Key Management Lifecycle

1. **Identity Key Generation**: A long-term X25519 keypair generated once per client
   installation. Stored encrypted at rest (AES-GCM with passphrase-derived key).

2. **Signed Prekey**: Medium-term X25519 keypair signed with the identity key.
   Rotated periodically. Used in X3DH to prove prekey ownership.

3. **One-Time Prekeys**: Ephemeral X25519 keypairs generated in batches and uploaded
   to the server. Each is used exactly once then discarded. Provides an additional
   layer of forward secrecy in the initial handshake.

4. **Ratchet Keys**: Generated on-the-fly during message exchange. Each message
   potentially uses a new DH key, and symmetric chain keys are advanced with every
   message.

5. **Message Keys**: Derived from chain keys via HMAC. Used exactly once for a single
   message then discarded.

## Forward Secrecy

ARES-X achieves forward secrecy through the Double Ratchet algorithm:

- **DH Ratchet**: Each reply generates a new DH keypair. Compromise of a past key
  does not reveal future messages.
- **Symmetric Ratchet**: Within a sending chain, each message key is derived from the
  previous chain key. Old chain keys are deleted after use.
- **One-Time Prekeys**: Even if the identity key and signed prekey are later compromised,
  sessions initiated with a one-time prekey remain secret (the OTP is deleted after use).

## Zero-Knowledge Server Design

The server:
- Stores only encrypted message blobs with opaque routing metadata
- Cannot decrypt any message content
- Does not store private keys
- Does not have access to shared secrets or session state
- Uses content-addressable storage for messages (SHA-256 of ciphertext)
- Deletes messages after delivery confirmation

## Self-Destruct Implementation

- Self-destruct timers are set by the sender as metadata in the message envelope
- The timer starts when the message is delivered (received and decrypted)
- After expiry, the client marks the message for deletion from local storage
- The server has no role in self-destruct (it cannot read the timer metadata)
- This is a cooperative mechanism: a malicious recipient could ignore the timer

## Limitations and Non-Goals

- **No metadata protection**: The server sees sender/recipient IDs and message timing.
  Use Tor or a mixnet for metadata resistance.
- **No deniability**: Messages are authenticated; a recipient can prove who sent a message.
- **Device compromise**: If a device is fully compromised while unlocked, current session
  keys are exposed. Forward secrecy limits the damage to future messages only.
- **No multi-device**: Each device maintains independent sessions.
- **Self-destruct is cooperative**: Recipients can screenshot or copy messages before expiry.
- **No post-quantum security**: X25519 is vulnerable to quantum computers. A future
  upgrade to hybrid key exchange (ML-KEM + X25519) is planned.
