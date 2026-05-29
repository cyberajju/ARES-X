"""
X3DH-like initial key agreement for ARES-X.

Implements both initiator and responder sides of the Extended Triple
Diffie-Hellman protocol to establish a shared secret between two parties.
"""

from typing import Optional, Tuple

from crypto.key_exchange import X25519KeyPair, compute_shared_secret
from crypto.hkdf import derive_key
from protocol.messages import KeyBundle


# Protocol info string for HKDF derivation
X3DH_INFO = b"ARES-X_X3DH"


class X3DHInitiator:
    """
    X3DH initiator (Alice) side of the handshake.

    Performs 3 or 4 DH operations against the responder's key bundle
    to derive a shared secret.
    """

    def perform_handshake(
        self, our_identity: X25519KeyPair, peer_bundle: KeyBundle
    ) -> Tuple[bytes, bytes]:
        """
        Perform the X3DH handshake as initiator.

        DH operations:
            DH1 = DH(our_identity, peer_signed_prekey)
            DH2 = DH(our_ephemeral, peer_identity_key)
            DH3 = DH(our_ephemeral, peer_signed_prekey)
            DH4 = DH(our_ephemeral, peer_one_time_prekey)  [optional]

        Args:
            our_identity: Our long-term identity key pair
            peer_bundle: The responder's published key bundle

        Returns:
            Tuple of (shared_secret, ephemeral_public_key)
        """
        # Generate ephemeral key pair
        ephemeral = X25519KeyPair.generate()

        # DH1: our identity private x peer signed prekey public
        dh1 = compute_shared_secret(our_identity, peer_bundle.signed_prekey)

        # DH2: our ephemeral private x peer identity public
        dh2 = compute_shared_secret(ephemeral, peer_bundle.identity_key)

        # DH3: our ephemeral private x peer signed prekey public
        dh3 = compute_shared_secret(ephemeral, peer_bundle.signed_prekey)

        # Concatenate DH outputs
        dh_concat = dh1 + dh2 + dh3

        # DH4: our ephemeral private x peer one-time prekey public (if available)
        if peer_bundle.one_time_prekey is not None:
            dh4 = compute_shared_secret(ephemeral, peer_bundle.one_time_prekey)
            dh_concat += dh4

        # Derive shared secret via HKDF
        shared_secret = derive_key(
            ikm=dh_concat,
            salt=b"",
            info=X3DH_INFO,
            length=32,
        )

        return shared_secret, ephemeral.public_key


class X3DHResponder:
    """
    X3DH responder (Bob) side of the handshake.

    Performs matching DH operations to derive the same shared secret.
    """

    def complete_handshake(
        self,
        our_identity: X25519KeyPair,
        our_signed_prekey: X25519KeyPair,
        our_one_time_prekey: Optional[X25519KeyPair],
        peer_identity_key: bytes,
        peer_ephemeral_key: bytes,
    ) -> bytes:
        """
        Complete the X3DH handshake as responder.

        DH operations (mirrors initiator):
            DH1 = DH(our_signed_prekey, peer_identity_key)
            DH2 = DH(our_identity, peer_ephemeral_key)
            DH3 = DH(our_signed_prekey, peer_ephemeral_key)
            DH4 = DH(our_one_time_prekey, peer_ephemeral_key)  [optional]

        Args:
            our_identity: Our long-term identity key pair
            our_signed_prekey: Our signed prekey pair
            our_one_time_prekey: Our one-time prekey pair (if used)
            peer_identity_key: Peer's identity public key (32 bytes)
            peer_ephemeral_key: Peer's ephemeral public key (32 bytes)

        Returns:
            Shared secret (must match initiator's)
        """
        # DH1: our signed prekey private x peer identity public
        dh1 = compute_shared_secret(our_signed_prekey, peer_identity_key)

        # DH2: our identity private x peer ephemeral public
        dh2 = compute_shared_secret(our_identity, peer_ephemeral_key)

        # DH3: our signed prekey private x peer ephemeral public
        dh3 = compute_shared_secret(our_signed_prekey, peer_ephemeral_key)

        # Concatenate DH outputs
        dh_concat = dh1 + dh2 + dh3

        # DH4: our one-time prekey private x peer ephemeral public (if used)
        if our_one_time_prekey is not None:
            dh4 = compute_shared_secret(our_one_time_prekey, peer_ephemeral_key)
            dh_concat += dh4

        # Derive shared secret via HKDF
        shared_secret = derive_key(
            ikm=dh_concat,
            salt=b"",
            info=X3DH_INFO,
            length=32,
        )

        return shared_secret
