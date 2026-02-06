"""Wwise connection singleton via waapi-client."""

from __future__ import annotations

import json
import logging
from typing import Any

from waapi import CannotConnectToWaapiException, WaapiClient

log = logging.getLogger(__name__)

_connection: WwiseConnection | None = None


class WwiseConnection:
    """Manages a single WAAPI WebSocket connection to Wwise."""

    DEFAULT_URL = "ws://127.0.0.1:8080/waapi"

    def __init__(self) -> None:
        self._client: WaapiClient | None = None
        self._url: str = self.DEFAULT_URL

    @property
    def client(self) -> WaapiClient | None:
        return self._client

    def connect(self, url: str | None = None) -> dict[str, Any]:
        """Connect to Wwise. Returns getInfo result on success."""
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

    def disconnect(self) -> None:
        """Disconnect from Wwise."""
        if self._client is not None:
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
            log.info("Disconnected from Wwise")

    def is_connected(self) -> bool:
        """Check if connected to Wwise."""
        if self._client is None:
            return False
        try:
            self._client.call("ak.wwise.core.getInfo")
            return True
        except Exception:
            self._client = None
            return False

    def call(self, uri: str, args: dict | None = None, options: dict | None = None) -> Any:
        """Call a WAAPI function. Raises RuntimeError if not connected."""
        if self._client is None:
            raise RuntimeError("Not connected to Wwise. Use wwise_connect first.")
        kwargs = {}
        if args:
            kwargs["args"] = args  # positional in waapi-client
        if options:
            kwargs["options"] = options
        # waapi-client signature: call(uri, args=None, options=None)
        return self._client.call(uri, args, options)


def get_wwise_connection() -> WwiseConnection:
    """Return the global WwiseConnection singleton."""
    global _connection
    if _connection is None:
        _connection = WwiseConnection()
    return _connection
