"""
ARES-X Client Library

Provides key storage, session management, message encryption/decryption,
and a command-line interface for secure messaging.
"""

from client.key_store import KeyStore
from client.session import Session, SessionManager
from client.messenger import Messenger
from client.main import AresClient

__all__ = [
    "KeyStore",
    "Session",
    "SessionManager",
    "Messenger",
    "AresClient",
]
