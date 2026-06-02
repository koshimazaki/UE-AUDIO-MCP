"""Wwise connection singleton via waapi-client."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from waapi import WaapiClient

log = logging.getLogger(__name__)

_connection: WwiseConnection | None = None


class WwiseConnection:
    """Manages a single WAAPI WebSocket connection to Wwise."""

    DEFAULT_URL = "ws://127.0.0.1:8080/waapi"

    def __init__(self) -> None:
        self._client: WaapiClient | None = None
        self._url: str = self.DEFAULT_URL
        self._lock = threading.RLock()

    @property
    def client(self) -> WaapiClient | None:
        return self._client

    def connect(self, url: str | None = None) -> dict[str, Any]:
        """Connect to Wwise. Returns getInfo result on success."""
        try:
            from waapi import CannotConnectToWaapiException, WaapiClient
        except Exception as exc:
            raise RuntimeError(
                "waapi-client is required to connect to Wwise. "
                "Install the project dependencies with pip install -e '.[dev]'."
            ) from exc

        with self._lock:
            self._url = url or self.DEFAULT_URL
            if self._client is not None:
                self.disconnect()
            try:
                self._client = WaapiClient(url=self._url)
                info = self._client.call("ak.wwise.core.getInfo")
                log.info("Connected to Wwise %s", info.get("version", {}).get("displayName", "?"))
                return info
            except CannotConnectToWaapiException:
                self._client = None
                raise
            except Exception:
                # Clean up partially-created client on any unexpected error
                if self._client is not None:
                    try:
                        self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
                raise

    def disconnect(self) -> None:
        """Disconnect from Wwise."""
        with self._lock:
            if self._client is not None:
                try:
                    self._client.disconnect()
                except Exception as exc:
                    log.debug("Wwise disconnect error (ignored): %s", exc)
                self._client = None
                log.info("Disconnected from Wwise")

    def is_connected(self) -> bool:
        """Check if connected to Wwise."""
        with self._lock:
            if self._client is None:
                return False
            try:
                self._client.call("ak.wwise.core.getInfo")
                return True
            except Exception:
                log.debug("Wwise connection stale, cleaning up")
                self.disconnect()
                return False

    def call(self, uri: str, args: dict | None = None, options: dict | None = None) -> Any:
        """Call a WAAPI function. Raises RuntimeError if not connected."""
        with self._lock:
            if self._client is None:
                raise RuntimeError("Not connected to Wwise. Use wwise_connect first.")
            t0 = time.monotonic()
            try:
                result = self._client.call(uri, args, options)
                ms = (time.monotonic() - t0) * 1000
                try:
                    from ue_audio_mcp.session_log import get_session_logger
                    get_session_logger().log_waapi_call(uri, args or {}, "ok", ms)
                except Exception as log_exc:
                    log.debug("Session logging failed: %s", log_exc)
                return result
            except Exception as exc:
                ms = (time.monotonic() - t0) * 1000
                try:
                    from ue_audio_mcp.session_log import get_session_logger
                    get_session_logger().log_waapi_call(uri, args or {}, "error", ms, str(exc))
                except Exception as log_exc:
                    log.debug("Session logging failed: %s", log_exc)
                raise


def get_wwise_connection() -> WwiseConnection:
    """Return the global WwiseConnection singleton."""
    global _connection
    if _connection is None:
        _connection = WwiseConnection()
    return _connection
