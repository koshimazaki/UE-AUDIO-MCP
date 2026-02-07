"""UE5 plugin core tools — connect, info, status."""

from __future__ import annotations

import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


@mcp.tool()
def ue5_connect(host: str = "127.0.0.1", port: int = 9877) -> str:
    """Connect to the UE5 audio plugin via TCP.

    Args:
        host: Plugin host address (default 127.0.0.1)
        port: Plugin TCP port (default 9877)
    """
    conn = get_ue5_connection()
    try:
        info = conn.connect(host, port)
        return _ok({"message": "Connected to UE5 plugin", "info": info})
    except Exception as e:
        return _error(f"Cannot connect to UE5 plugin: {e}")


@mcp.tool()
def ue5_get_info() -> str:
    """Get UE5 engine info (version, project, features)."""
    conn = get_ue5_connection()
    try:
        info = conn.send_command({"action": "ping"})
        return _ok({"info": info})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ue5_status() -> str:
    """Get combined status of Wwise and UE5 plugin connections."""
    wwise = get_wwise_connection()
    ue5 = get_ue5_connection()
    return _ok({
        "wwise_connected": wwise.is_connected(),
        "ue5_connected": ue5.is_connected(),
    })
