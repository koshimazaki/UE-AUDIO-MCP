"""Preview tools — transport control and SoundBank generation."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import TRANSPORT_ACTIONS
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok

log = logging.getLogger(__name__)


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
            # Get existing transports, optionally filtered by object_path
            transports = conn.call("ak.wwise.core.transport.getList")
            transport_list = transports.get("list", []) if transports else []

            # Filter to matching object if path provided
            if object_path:
                transport_list = [
                    t for t in transport_list
                    if t.get("object") == object_path
                ]

            stopped = 0
            errors = []
            for t in transport_list:
                tid = t["transport"]
                try:
                    conn.call("ak.wwise.core.transport.executeAction", {
                        "transport": tid,
                        "action": "stop",
                    })
                    conn.call("ak.wwise.core.transport.destroy", {
                        "transport": tid,
                    })
                    stopped += 1
                except Exception as exc:
                    errors.append(f"transport {tid}: {exc}")

            result_data = {"action": "stop", "transports_stopped": stopped}
            if errors:
                result_data["errors"] = errors
            return _ok(result_data)

        # Clean up any existing transports for this object to avoid leaks
        existing = conn.call("ak.wwise.core.transport.getList")
        existing_list = existing.get("list", []) if existing else []
        for t in existing_list:
            if t.get("object") == object_path:
                try:
                    conn.call("ak.wwise.core.transport.destroy", {"transport": t["transport"]})
                except Exception:
                    pass

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

    if not all(isinstance(n, str) for n in names):
        return _error("All bank names must be strings")

    conn = get_wwise_connection()
    try:
        banks = [{"name": n} for n in names]
        result = conn.call("ak.wwise.core.soundbank.generate", {
            "soundbanks": banks,
        })
        return _ok({"banks_generated": len(names), "names": names, "result": result})
    except Exception as e:
        return _error(str(e))
