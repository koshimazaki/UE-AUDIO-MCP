"""Shared TypedDict definitions for MetaSounds node/pin data.

Used by both the hand-curated catalogue (metasound_nodes.py) and
engine sync scripts so pin schemas stay consistent.
"""

from __future__ import annotations

from typing import TypedDict, NotRequired


class MSPin(TypedDict):
    """A single MetaSounds pin (input or output)."""

    name: str
    type: str  # Audio, Float, Trigger, Int32, Bool, Time, String, Enum, WaveAsset, ...
    required: NotRequired[bool]  # catalogue only (default True for inputs)
    default: NotRequired[object]  # value if pin is not connected


class MSNode(TypedDict):
    """A full MetaSounds node definition."""

    name: str
    category: str
    description: str
    inputs: list[MSPin]
    outputs: list[MSPin]
    tags: NotRequired[list[str]]
    complexity: NotRequired[int]
    class_name: NotRequired[str]
    mcp_note: NotRequired[str]


# ---------------------------------------------------------------------------
# Type normalization — engine reports different notation than catalogue
# ---------------------------------------------------------------------------

def normalize_pin_type(engine_type: str) -> str:
    """Normalize engine pin type notation to catalogue format.

    Engine quirks handled:
      - ``Float:Array``  ->  ``Float[]``     (array suffix)
      - ``Enum:BiquadFilterType``  ->  ``Enum``  (strip enum subtype)
      - ``Metasound:...`` namespace prefixes  ->  stripped
    """
    if not engine_type:
        return engine_type

    # Array notation: "Float:Array" -> "Float[]"
    if engine_type.endswith(":Array"):
        base = engine_type.rsplit(":Array", 1)[0]
        return f"{normalize_pin_type(base)}[]"

    # Enum subtype: "Enum:BiquadFilterType" -> "Enum"
    if engine_type.startswith("Enum:"):
        return "Enum"

    # Namespace prefix stripping (e.g. "Metasound:Float" -> "Float")
    if ":" in engine_type:
        # Keep the last part (the actual type)
        return engine_type.rsplit(":", 1)[-1]

    return engine_type
