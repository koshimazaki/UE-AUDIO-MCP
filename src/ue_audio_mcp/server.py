"""MCP server for game audio: Wwise (WAAPI), MetaSounds and Blueprints (UE5 plugin)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.session_log import get_session_logger
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[None]:
    """Try connecting to Wwise on startup; warn if unavailable."""
    session_logger = get_session_logger()
    session_logger.start_session()
    session_logger.rotate_logs()

    wwise = get_wwise_connection()
    try:
        info = wwise.connect()
        log.info("Wwise ready: %s", info.get("version", {}).get("displayName", "?"))
    except Exception as exc:
        log.warning("Wwise not available — use wwise_connect to connect later: %s", exc)

    ue5 = get_ue5_connection()
    try:
        ue5.connect()
        log.info("UE5 plugin ready")
    except Exception as exc:
        log.warning("UE5 plugin not available — use ue5_connect to connect later: %s", exc)

    try:
        yield None
    finally:
        session_logger.end_session()
        wwise.disconnect()
        ue5.disconnect()


mcp = MCPServer(
    "ue-audio-mcp",
    instructions="MCP server for game audio — Wwise (WAAPI) + MetaSounds (Builder API) + UE5 Blueprints. "
    "Create objects, events, mix buses, generate soundbanks, query nodes, validate graphs, "
    "build MetaSounds patches, search Blueprint nodes, stage actors/cameras, execute functions via UE5 plugin.",
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
import ue_audio_mcp.tools.ue5_core  # noqa: E402, F401
import ue_audio_mcp.tools.ms_builder  # noqa: E402, F401
import ue_audio_mcp.tools.blueprints  # noqa: E402, F401
import ue_audio_mcp.tools.variables  # noqa: E402, F401
import ue_audio_mcp.tools.presets  # noqa: E402, F401
import ue_audio_mcp.tools.bp_builder  # noqa: E402, F401
import ue_audio_mcp.tools.systems  # noqa: E402, F401
import ue_audio_mcp.tools.world_setup  # noqa: E402, F401
import ue_audio_mcp.tools.camera  # noqa: E402, F401
import ue_audio_mcp.tools.audit  # noqa: E402, F401


def main():
    """Entry point for the ue-audio-mcp CLI."""
    mcp.run()


if __name__ == "__main__":
    # `python -m ue_audio_mcp.server` runs this file as __main__, but the tool
    # modules register on the importable ue_audio_mcp.server module, so run that.
    from ue_audio_mcp.server import main as _main

    _main()
