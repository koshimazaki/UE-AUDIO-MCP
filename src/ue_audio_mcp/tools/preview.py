"""Preview tools — transport control and SoundBank generation."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import TRANSPORT_ACTIONS
from ue_audio_mcp.server import mcp

log = logging.getLogger(__name__)


def _ok(data: dict | None = None) -> str:
    result = {"status": "ok"}
    if data:
        result.update(data)
    return json.dumps(result)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message})


@mcp.tool()
def wwise_preview(object_path: str, action: str = "play") -> str:
    """Preview a Wwise object (Event, Sound, Container) via transport.

    Args:
        object_path: Path to the object to preview
        action: Transport action — play, stop, or pause
    """
    action = action.lower()
    if action not in TRANSPORT_ACTIONS:
        return _error(f"Invalid action '{action}'. Valid: {sorted(TRANSPORT_ACTIONS)}")

    conn = get_wwise_connection()
    try:
        if action == "stop":
            # Get existing transports and stop them
            transports = conn.call("ak.wwise.core.transport.getList")
            transport_list = transports.get("list", []) if transports else []
            for t in transport_list:
                conn.call("ak.wwise.core.transport.executeAction", {
                    "transport": t["transport"],
                    "action": "stop",
                })
                conn.call("ak.wwise.core.transport.destroy", {
                    "transport": t["transport"],
                })
            return _ok({"action": "stop", "transports_stopped": len(transport_list)})

        # Create transport and execute action
        transport = conn.call("ak.wwise.core.transport.create", {
            "object": object_path,
        })
        transport_id = transport.get("transport")

        conn.call("ak.wwise.core.transport.executeAction", {
            "transport": transport_id,
            "action": action,
        })

        return _ok({
            "action": action,
            "transport_id": transport_id,
            "object": object_path,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_generate_banks(bank_names: str) -> str:
    """Generate Wwise SoundBanks.

    Args:
        bank_names: JSON array of bank names to generate (e.g. ["Weapons_Bank", "UI_Bank"])
    """
    try:
        names = json.loads(bank_names)
    except json.JSONDecodeError:
        return _error(f"Invalid bank_names JSON: {bank_names}")

    if not isinstance(names, list) or not names:
        return _error("bank_names must be a non-empty JSON array of strings")

    conn = get_wwise_connection()
    try:
        banks = [{"name": n} for n in names]
        result = conn.call("ak.wwise.core.soundbank.generate", {
            "soundbanks": banks,
        })
        return _ok({"banks_generated": len(names), "names": names, "result": result})
    except Exception as e:
        return _error(str(e))
