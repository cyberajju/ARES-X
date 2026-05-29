"""
ARES-X Server entry point.

Initializes database, starts WebSocket server and HTTP API concurrently,
handles graceful shutdown, and runs periodic cleanup tasks.
"""

import asyncio
import logging
import signal
import sys

from server.config import ServerConfig
from server.database import Database
from server.message_queue import MessageQueue
from server.websocket_server import WebSocketServer
from server.api import HTTPServer

logger = logging.getLogger(__name__)


class AresServer:
    """Main server orchestrator."""

    def __init__(self, config: ServerConfig = None):
        self.config = config or ServerConfig.from_env()
        self.db = Database(self.config.db_path)
        self.mq = MessageQueue(self.config, self.db)
        self.ws_server = WebSocketServer(self.config, self.db, self.mq)
        self.http_server = HTTPServer(self.config, self.db)
        self._shutdown_event = asyncio.Event()
        self._cleanup_task = None

    async def start(self):
        """Start all server components."""
        # Start servers
        await self.ws_server.start()
        await self.http_server.start()

        # Start periodic cleanup
        self._cleanup_task = asyncio.ensure_future(self._periodic_cleanup())

        logger.info("ARES-X server started")
        logger.info(f"  WebSocket: ws://{self.config.host}:{self.config.ws_port}")
        logger.info(f"  HTTP API:  http://{self.config.host}:{self.config.http_port}")

    async def stop(self):
        """Stop all server components gracefully."""
        logger.info("Shutting down ARES-X server...")

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop servers
        await self.ws_server.stop()
        await self.http_server.stop()

        # Close database
        self.db.close()

        logger.info("ARES-X server stopped")

    async def run(self):
        """Run the server until shutdown signal."""
        await self.start()

        # Wait for shutdown
        await self._shutdown_event.wait()
        await self.stop()

    def shutdown(self):
        """Signal the server to shut down."""
        self._shutdown_event.set()

    async def _periodic_cleanup(self):
        """Periodically clean up expired messages."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                self.mq.run_cleanup()
                logger.debug("Expired message cleanup completed")
        except asyncio.CancelledError:
            pass


def setup_logging(level: str = 'INFO'):
    """Configure logging for the server."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def main():
    """Main entry point."""
    config = ServerConfig.from_env()
    setup_logging(config.log_level)

    server = AresServer(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Setup signal handlers
    def signal_handler():
        server.shutdown()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass

    try:
        loop.run_until_complete(server.run())
    except KeyboardInterrupt:
        loop.run_until_complete(server.stop())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
