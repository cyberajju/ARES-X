"""
Post-Quantum Cryptography placeholder module.

This module defines the abstract interface for post-quantum Key Encapsulation
Mechanisms (KEMs) and a hybrid key exchange class that combines classical
X25519 with a post-quantum KEM for quantum-resistant key agreement.

Upgrade Path:
- When NIST PQC standards are finalized and available in OpenSSL,
  implement concrete KEMs (e.g., ML-KEM/Kyber, ML-DSA/Dilithium)
  that inherit from PostQuantumKEM.
- The HybridKeyExchange class ensures backward-compatible security:
  even if the PQ algorithm is broken, X25519 still provides security
  against classical attackers.
- Integration: Replace direct X25519 usage in the handshake protocol
  with HybridKeyExchange to gain quantum resistance.
"""

from abc import ABC, abstractmethod

from crypto.key_exchange import X25519KeyPair, compute_shared_secret
from crypto.hkdf import derive_key


class PostQuantumKEM(ABC):
    """
    Abstract base class for post-quantum Key Encapsulation Mechanisms.

    Concrete implementations should wrap PQ algorithms such as:
    - ML-KEM (Kyber) for key encapsulation
    - ML-DSA (Dilithium) for digital signatures
    - SLH-DSA (SPHINCS+) for hash-based signatures
    """

    @abstractmethod
    def generate_keypair(self) -> tuple:
        """
        Generate a new key pair.

        Returns:
            Tuple of (public_key: bytes, private_key: bytes)
        """
        pass

    @abstractmethod
    def encapsulate(self, public_key: bytes) -> tuple:
        """
        Encapsulate: generate a shared secret and ciphertext.

        Args:
            public_key: Recipient's public key

        Returns:
            Tuple of (ciphertext: bytes, shared_secret: bytes)
        """
        pass

    @abstractmethod
    def decapsulate(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """
        Decapsulate: recover shared secret from ciphertext.

        Args:
            private_key: Recipient's private key
            ciphertext: Ciphertext from encapsulate()

        Returns:
            shared_secret: bytes
        """
        pass


class HybridKeyExchange:
    """
    Hybrid key exchange combining classical X25519 with a post-quantum KEM.

    The final shared secret is derived by combining both the X25519 shared
    secret and the PQ shared secret through HKDF, ensuring security as long
    as at least one of the two algorithms remains unbroken.

    Usage:
        # When a PQ KEM implementation is available:
        kem = ConcreteKyberKEM()
        hybrid = HybridKeyExchange(pq_kem=kem)
        result = hybrid.perform_exchange(peer_x25519_public, peer_pq_public)
        # result contains the hybrid shared secret

        # Without PQ (falls back to X25519-only):
        hybrid = HybridKeyExchange(pq_kem=None)
        result = hybrid.perform_exchange(peer_x25519_public, None)
    """

    def __init__(self, pq_kem: PostQuantumKEM = None):
        """
        Initialize hybrid key exchange.

        Args:
            pq_kem: Post-quantum KEM instance, or None for X25519-only mode
        """
        self._pq_kem = pq_kem
        self._x25519_keypair = X25519KeyPair.generate()

    @property
    def x25519_public_key(self) -> bytes:
        """Get the X25519 public key for this exchange."""
        return self._x25519_keypair.public_key

    def generate_pq_keypair(self) -> tuple:
        """
        Generate a PQ key pair if a KEM is configured.

        Returns:
            Tuple of (public_key, private_key) or (None, None) if no KEM
        """
        if self._pq_kem is None:
            return (None, None)
        return self._pq_kem.generate_keypair()

    def perform_exchange(
        self,
        peer_x25519_public: bytes,
        peer_pq_public: bytes = None,
    ) -> bytes:
        """
        Perform hybrid key exchange.

        Combines X25519 shared secret with PQ shared secret (if available)
        through HKDF to produce the final key material.

        Args:
            peer_x25519_public: Peer's X25519 public key (32 bytes)
            peer_pq_public: Peer's PQ public key (optional)

        Returns:
            32-byte derived shared secret
        """
        # Classical X25519 key agreement
        x25519_secret = compute_shared_secret(
            self._x25519_keypair, peer_x25519_public
        )

        # If PQ KEM is available, combine secrets
        if self._pq_kem is not None and peer_pq_public is not None:
            # Encapsulate to get PQ shared secret
            _ciphertext, pq_secret = self._pq_kem.encapsulate(peer_pq_public)
            # Combine both secrets
            combined_ikm = x25519_secret + pq_secret
        else:
            combined_ikm = x25519_secret

        # Derive final key using HKDF
        return derive_key(
            ikm=combined_ikm,
            salt=b"ARES-X-hybrid-exchange-v1",
            info=b"hybrid-shared-secret",
            length=32,
        )
