"""
Server configuration for ARES-X.

Uses a dataclass with sensible defaults that can be overridden
via environment variables with the ARES_ prefix.
"""

import os
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Server configuration with environment variable override support."""
    host: str = '0.0.0.0'
    ws_port: int = 8765
    http_port: int = 8080
    db_path: str = 'ares_x.db'
    max_message_size: int = 65536  # 64KB
    message_ttl: int = 604800  # 7 days in seconds
    max_offline_queue: int = 1000
    max_connections: int = 100
    ping_interval: int = 30
    ping_timeout: int = 10
    log_level: str = 'INFO'

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables with ARES_ prefix."""
        return cls(
            host=os.environ.get('ARES_HOST', '0.0.0.0'),
            ws_port=int(os.environ.get('ARES_WS_PORT', '8765')),
            http_port=int(os.environ.get('ARES_HTTP_PORT', '8080')),
            db_path=os.environ.get('ARES_DB_PATH', 'ares_x.db'),
            max_message_size=int(os.environ.get('ARES_MAX_MESSAGE_SIZE', '65536')),
            message_ttl=int(os.environ.get('ARES_MESSAGE_TTL', '604800')),
            max_offline_queue=int(os.environ.get('ARES_MAX_OFFLINE_QUEUE', '1000')),
            max_connections=int(os.environ.get('ARES_MAX_CONNECTIONS', '100')),
            ping_interval=int(os.environ.get('ARES_PING_INTERVAL', '30')),
            ping_timeout=int(os.environ.get('ARES_PING_TIMEOUT', '10')),
            log_level=os.environ.get('ARES_LOG_LEVEL', 'INFO'),
        )
