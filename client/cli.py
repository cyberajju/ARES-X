"""
ARES-X Command-Line Interface for secure messaging.

Provides an interactive terminal-based chat interface using asyncio
for concurrent network and user input handling.
"""

import asyncio
import argparse
import sys
import time
from typing import Optional

from client.main import AresClient
from protocol.messages import KeyBundle


class AresCLI:
    """
    Interactive command-line interface for ARES-X secure messaging.

    Commands:
        /register           - Generate keys and register with server
        /connect <peer_id>  - Initiate session with a peer
        /msg <text>         - Send encrypted message to active peer
        /file <path>        - Send encrypted file to active peer
        /verify             - Show safety number for active session
        /destruct <seconds> - Set self-destruct timer for next message
        /history            - Show message history
        /quit               - Exit the client
    """

    def __init__(self, client: AresClient):
        """
        Initialize CLI.

        Args:
            client: AresClient instance to use
        """
        self.client = client
        self.active_peer: Optional[str] = None
        self.self_destruct_timer: Optional[int] = None
        self._running = False
        self._history = []

    def _print(self, msg: str):
        """Print a message to the console."""
        print(msg, flush=True)

    def _print_help(self):
        """Display available commands."""
        self._print("\n=== ARES-X Secure Messenger ===")
        self._print("Commands:")
        self._print("  /register           - Generate keys and register")
        self._print("  /connect <peer_id>  - Start session with peer")
        self._print("  /msg <text>         - Send message to active peer")
        self._print("  /file <path>        - Send file to active peer")
        self._print("  /verify             - Show safety number")
        self._print("  /destruct <seconds> - Set self-destruct timer")
        self._print("  /history            - Show message history")
        self._print("  /quit               - Exit")
        self._print("")

    async def _handle_command(self, line: str):
        """Process a command line input."""
        line = line.strip()
        if not line:
            return

        parts = line.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/register":
            await self._cmd_register()
        elif cmd == "/connect":
            await self._cmd_connect(args)
        elif cmd == "/msg":
            await self._cmd_msg(args)
        elif cmd == "/file":
            await self._cmd_file(args)
        elif cmd == "/verify":
            self._cmd_verify()
        elif cmd == "/destruct":
            self._cmd_destruct(args)
        elif cmd == "/history":
            self._cmd_history()
        elif cmd == "/quit":
            self._running = False
        elif cmd == "/help":
            self._print_help()
        else:
            self._print(f"Unknown command: {cmd}. Type /help for commands.")

    async def _cmd_register(self):
        """Handle /register command."""
        try:
            await self.client.register()
            self._print("[OK] Registered with server. Keys generated.")
        except Exception as e:
            self._print(f"[ERROR] Registration failed: {e}")

    async def _cmd_connect(self, peer_id: str):
        """Handle /connect command."""
        if not peer_id:
            self._print("[ERROR] Usage: /connect <peer_id>")
            return
        self.active_peer = peer_id
        try:
            await self.client.start_session(peer_id)
            self._print(f"[OK] Session request sent to {peer_id}")
        except Exception as e:
            self._print(f"[ERROR] Failed to connect to {peer_id}: {e}")

    async def _cmd_msg(self, text: str):
        """Handle /msg command."""
        if not self.active_peer:
            self._print("[ERROR] No active peer. Use /connect <peer_id> first.")
            return
        if not text:
            self._print("[ERROR] Usage: /msg <text>")
            return
        try:
            await self.client.send_message(
                self.active_peer, text, self.self_destruct_timer
            )
            self._history.append({
                "direction": "sent",
                "peer": self.active_peer,
                "text": text,
                "timestamp": time.time(),
            })
            destruct_info = ""
            if self.self_destruct_timer:
                destruct_info = f" [self-destruct: {self.self_destruct_timer}s]"
                self.self_destruct_timer = None
            self._print(f"[SENT] -> {self.active_peer}: {text}{destruct_info}")
        except Exception as e:
            self._print(f"[ERROR] Failed to send: {e}")

    async def _cmd_file(self, path: str):
        """Handle /file command."""
        if not self.active_peer:
            self._print("[ERROR] No active peer. Use /connect <peer_id> first.")
            return
        if not path:
            self._print("[ERROR] Usage: /file <path>")
            return
        try:
            import os
            with open(path, "rb") as f:
                data = f.read()
            filename = os.path.basename(path)
            envelope = self.client.messenger.compose_file_message(
                self.active_peer, filename, data
            )
            self._print(f"[SENT] File: {filename} ({len(data)} bytes)")
        except FileNotFoundError:
            self._print(f"[ERROR] File not found: {path}")
        except Exception as e:
            self._print(f"[ERROR] Failed to send file: {e}")

    def _cmd_verify(self):
        """Handle /verify command."""
        if not self.active_peer:
            self._print("[ERROR] No active peer. Use /connect <peer_id> first.")
            return
        session = self.client.session_manager.get_session(self.active_peer)
        if session is None:
            self._print("[ERROR] No active session with peer.")
            return
        our_identity = self.client.key_store.get_identity_key()
        if our_identity is None:
            self._print("[ERROR] No identity key.")
            return
        safety_number = session.get_safety_number(our_identity.public_key)
        self._print(f"[VERIFY] Safety number with {self.active_peer}:")
        self._print(f"  {safety_number}")
        self._print("  Compare this with your peer to verify identity.")

    def _cmd_destruct(self, seconds_str: str):
        """Handle /destruct command."""
        try:
            seconds = int(seconds_str)
            if seconds <= 0:
                raise ValueError()
            self.self_destruct_timer = seconds
            self._print(f"[OK] Next message will self-destruct in {seconds}s")
        except (ValueError, TypeError):
            self._print("[ERROR] Usage: /destruct <seconds> (positive integer)")

    def _cmd_history(self):
        """Handle /history command."""
        if not self._history:
            self._print("[INFO] No message history.")
            return
        self._print("\n=== Message History ===")
        for msg in self._history[-20:]:
            direction = "->" if msg["direction"] == "sent" else "<-"
            ts = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
            self._print(f"  [{ts}] {direction} {msg['peer']}: {msg['text']}")
        self._print("")

    def _on_message_received(self, msg: dict):
        """Callback for incoming messages."""
        self._history.append({
            "direction": "received",
            "peer": msg["sender"],
            "text": msg.get("text", "[file]"),
            "timestamp": msg["timestamp"],
        })
        destruct_info = ""
        if msg.get("self_destruct"):
            destruct_info = f" [self-destruct: {msg['self_destruct']}s]"
        self._print(f"\n[RECV] <- {msg['sender']}: {msg.get('text', '[file]')}{destruct_info}")

    async def run(self):
        """Run the interactive CLI loop."""
        self._running = True
        self.client.on_message(self._on_message_received)

        self._print_help()
        self._print(f"User ID: {self.client.user_id}")
        self._print(f"Server: {self.client.server_host}:{self.client.server_port}")
        self._print("")

        # Use a simple input loop (works without actual network)
        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("ares-x> ")
                )
                await self._handle_command(line)
            except (EOFError, KeyboardInterrupt):
                self._running = False
                break

        self._print("\n[INFO] Shutting down...")
        await self.client.close()


def main():
    """Entry point for ARES-X CLI."""
    parser = argparse.ArgumentParser(description="ARES-X Secure Messenger CLI")
    parser.add_argument("--server", default="localhost", help="Server hostname")
    parser.add_argument("--port", type=int, default=8443, help="Server port")
    parser.add_argument("--user-id", required=True, help="Your user ID")
    parser.add_argument("--db-path", default=":memory:", help="Key store database path")
    parser.add_argument("--passphrase", default="", help="Key store passphrase")

    args = parser.parse_args()

    client = AresClient(
        user_id=args.user_id,
        server_host=args.server,
        server_port=args.port,
        key_store_path=args.db_path,
        passphrase=args.passphrase,
    )

    cli = AresCLI(client)
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
