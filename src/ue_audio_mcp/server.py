"""FastMCP server for Wwise game audio via WAAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from ue_audio_mcp.connection import get_wwise_connection

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Try connecting to Wwise on startup; warn if unavailable."""
    conn = get_wwise_connection()
    try:
        info = conn.connect()
        log.info("Wwise ready: %s", info.get("version", {}).get("displayName", "?"))
    except Exception:
        log.warning("Wwise not available — use wwise_connect to connect later")
    try:
        yield None
    finally:
        conn.disconnect()


mcp = FastMCP(
    "ue-audio-mcp",
    instructions="MCP server for game audio — Wwise (WAAPI) + MetaSounds knowledge. "
    "Create objects, events, mix buses, generate soundbanks, query nodes, validate graphs.",
    lifespan=lifespan,
)

# Import tool modules AFTER mcp is defined (they register @mcp.tool decorators)
import ue_audio_mcp.tools.core  # noqa: E402, F401
import ue_audio_mcp.tools.objects  # noqa: E402, F401
import ue_audio_mcp.tools.events  # noqa: E402, F401
import ue_audio_mcp.tools.preview  # noqa: E402, F401
import ue_audio_mcp.tools.templates  # noqa: E402, F401
import ue_audio_mcp.tools.metasounds  # noqa: E402, F401
import ue_audio_mcp.tools.ms_graph  # noqa: E402, F401


def main():
    """Entry point for the ue-audio-mcp CLI."""
    mcp.run()


if __name__ == "__main__":
    main()
