# ARES-X Threat Model

## Assets Protected

### Primary Assets
- **Message content**: The plaintext of all messages between users
- **Private keys**: Identity keys, signed prekeys, one-time prekeys, ratchet keys
- **Session state**: Double Ratchet chain keys and message keys

### Secondary Assets
- **Contact relationships**: Who communicates with whom
- **Message timing**: When messages are sent and received
- **File content**: Encrypted file transfers between users

## Adversary Models

### 1. Passive Network Eavesdropper

**Capabilities**: Can observe all network traffic between client and server.

**What they see**:
- Encrypted WebSocket frames
- IP addresses of communicating parties
- Message sizes and timing patterns

**Mitigations**:
- All message content is end-to-end encrypted with AES-256-GCM
- Key material is never sent in plaintext
- HKDF-derived keys have no correlation to observable traffic

**Residual risk**: Traffic analysis can reveal communication patterns.

### 2. Compromised Server

**Capabilities**: Full control over the relay server, including stored data,
database contents, and message routing.

**What they can do**:
- Read all stored data (only encrypted blobs)
- Modify or drop messages in transit
- Correlate sender/recipient metadata
- Attempt to impersonate users (blocked by identity verification)

**Mitigations**:
- Zero-knowledge storage: server never has access to plaintext or keys
- End-to-end encryption means server compromise does not reveal content
- Safety numbers allow users to detect identity key substitution (MITM)
- Message integrity via AES-GCM authentication tags

**Residual risk**: Metadata (who talks to whom, when, message sizes) is visible
to the server. Active MITM is possible if users do not verify safety numbers.

### 3. Compromised Device (Past)

**Capabilities**: Attacker obtained a copy of the device's key material at
some point in the past, but does not have ongoing access.

**What they can do**:
- Decrypt messages that were encrypted with the compromised keys

**Mitigations**:
- Forward secrecy via Double Ratchet: keys are continuously rotated
- Past keys are deleted after use
- One-time prekeys provide break-in recovery for new sessions
- After a few message exchanges, the ratchet moves beyond compromised state

**Residual risk**: Messages encrypted during the compromise window are exposed.

### 4. Compromised Device (Active/Current)

**Capabilities**: Attacker has full, ongoing access to an unlocked device.

**What they can do**:
- Read all current session keys
- Decrypt all current and future messages
- Impersonate the device owner

**Mitigations**:
- Key store encryption with passphrase (requires passphrase to access keys)
- Self-destruct timers limit the window of readable message history
- No mitigation exists for a fully compromised device with unlocked keys

**Residual risk**: This is a non-goal -- if the device is fully compromised
while in active use, all bets are off.

## Attack Vectors and Mitigations

| Attack Vector | Mitigation |
|--------------|------------|
| Ciphertext tampering | AES-GCM authentication tag detects any modification |
| Replay attacks | Message numbers and DH ratchet prevent replay |
| Key reuse | Each message uses a unique derived message key |
| Brute force on AES-256 | 2^256 key space makes brute force infeasible |
| MITM during handshake | Safety numbers allow out-of-band verification |
| Server message injection | End-to-end authentication; forged messages fail decryption |
| Timing attacks | Constant-time comparison (hmac.compare_digest) for all auth |
| Nonce reuse | Random 12-byte nonces with negligible collision probability |

## What ARES-X Does NOT Protect Against

1. **Metadata surveillance**: The server and network observers can see who
   communicates with whom, message timing, and message sizes. Use an
   anonymity network (Tor, mixnet) if metadata protection is required.

2. **Endpoint compromise**: A fully compromised device with active access
   defeats end-to-end encryption. Physical security of devices is assumed.

3. **Rubber-hose cryptanalysis**: If a user is coerced into revealing their
   passphrase, all locally stored data is accessible.

4. **Screenshots and copies**: A malicious recipient can copy plaintext
   messages before self-destruct timers expire. Self-destruct is cooperative.

5. **Quantum computing**: X25519 is not quantum-resistant. A sufficiently
   powerful quantum computer could break ECDH. Post-quantum hybrid key
   exchange is planned for a future version.

6. **Social engineering**: ARES-X cannot prevent users from being tricked into
   communicating with the wrong person. Safety number verification helps but
   requires user diligence.

7. **Denial of service**: A compromised server or network can drop all messages,
   effectively preventing communication.

8. **Group messaging**: ARES-X currently supports only 1:1 sessions. Group
   key distribution introduces additional complexities not yet addressed.
