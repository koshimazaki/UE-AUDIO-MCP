"""UE5 plugin connection singleton via TCP socket.

Mirrors the WwiseConnection pattern in connection.py.
Protocol: 4-byte big-endian uint32 length prefix + UTF-8 JSON payload.
Default: 127.0.0.1:9877.
"""

from __future__ import annotations

import json
import logging
import socket
import struct
import time
from typing import Any

log = logging.getLogger(__name__)

_connection: UE5PluginConnection | None = None

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 30.0
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 16 * 1024 * 1024  # 16 MB — reject anything larger


class UE5PluginConnection:
    """Manages a TCP connection to the UE5 C++ audio plugin."""

    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._host: str = DEFAULT_HOST
        self._port: int = DEFAULT_PORT

    def connect(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict[str, Any]:
        """Connect to the UE5 plugin. Returns engine info on success."""
        self._host = host
        self._port = port
        if self._sock is not None:
            self.disconnect()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(TIMEOUT)
            self._sock.connect((self._host, self._port))
            info = self.send_command({"action": "ping"})
            log.info("Connected to UE5 plugin at %s:%d", self._host, self._port)
            return info
        except (OSError, ConnectionError) as e:
            if self._sock is not None:
                try:
                    self._sock.close()
                except Exception as close_exc:
                    log.debug("Socket close error during connect cleanup: %s", close_exc)
                self._sock = None
            raise ConnectionError(f"Cannot connect to UE5 plugin at {host}:{port}: {e}") from e
        except Exception:
            if self._sock is not None:
                try:
                    self._sock.close()
                except Exception as close_exc:
                    log.debug("Socket close error during connect cleanup: %s", close_exc)
                self._sock = None
            raise

    def disconnect(self) -> None:
        """Disconnect from the UE5 plugin."""
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception as exc:
                log.debug("UE5 socket close error (ignored): %s", exc)
            self._sock = None
            log.info("Disconnected from UE5 plugin")

    def is_connected(self) -> bool:
        """Check if connected to the UE5 plugin.

        Verifies the socket is still alive via getpeername() when
        a real socket is present. Cleans up stale sockets as a side
        effect to prevent stale True on next call.
        """
        if self._sock is None:
            return False
        if not isinstance(self._sock, socket.socket):
            return True  # mock / test stub
        try:
            self._sock.getpeername()
            return True
        except OSError:
            # Socket is dead — clean up to avoid stale state
            log.debug("UE5 socket stale, cleaning up")
            self.disconnect()
            return False

    def send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON command and return the response dict.

        Raises RuntimeError if not connected.
        Cleans up the socket on communication failure so is_connected()
        won't return a stale True.
        """
        if self._sock is None:
            raise RuntimeError("Not connected to UE5 plugin. Use ue5_connect first.")
        action = command.get("action", "")
        t0 = time.monotonic()
        try:
            payload = json.dumps(command).encode("utf-8")
            header = struct.pack(">I", len(payload))
            self._sock.sendall(header + payload)
            result = self._recv_response()
            ms = (time.monotonic() - t0) * 1000
            status = result.get("status", "ok") if isinstance(result, dict) else "ok"
            try:
                from ue_audio_mcp.session_log import get_session_logger
                get_session_logger().log_tcp_command(action, command, status, ms)
            except Exception:
                pass
            return result
        except (OSError, ConnectionError, json.JSONDecodeError, struct.error) as e:
            ms = (time.monotonic() - t0) * 1000
            try:
                from ue_audio_mcp.session_log import get_session_logger
                get_session_logger().log_tcp_command(action, command, "error", ms, str(e))
            except Exception:
                pass
            try:
                log.warning("UE5 plugin communication failed, disconnecting: %s", e)
            finally:
                self.disconnect()
            raise

    def _recv_response(self) -> dict[str, Any]:
        """Read a length-prefixed JSON response from the socket."""
        raw_header = self._recv_raw(HEADER_SIZE)
        (length,) = struct.unpack(">I", raw_header)
        if length > MAX_MESSAGE_SIZE:
            raise ConnectionError(
                "Response too large: {} bytes (max {})".format(length, MAX_MESSAGE_SIZE)
            )
        raw_body = self._recv_raw(length)
        return json.loads(raw_body.decode("utf-8"))

    def _recv_raw(self, size: int) -> bytes:
        """Read exactly *size* bytes from the socket."""
        data = bytearray()
        while len(data) < size:
            chunk = self._sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("UE5 plugin connection closed unexpectedly")
            data.extend(chunk)
        return bytes(data)


def get_ue5_connection() -> UE5PluginConnection:
    """Return the global UE5PluginConnection singleton."""
    global _connection
    if _connection is None:
        _connection = UE5PluginConnection()
    return _connection
