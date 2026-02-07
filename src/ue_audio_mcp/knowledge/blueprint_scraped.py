"""Load scraped Blueprint node specs from JSON files.

Looks for bp_node_specs.json (full) or node_specs_sample.json (partial)
in the scripts/ directory at the project root.
"""

from __future__ import annotations

import json
import os
from typing import Any

_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "scripts",
)

_FULL_PATH = os.path.join(_SCRIPTS_DIR, "bp_node_specs.json")
_SAMPLE_PATH = os.path.join(_SCRIPTS_DIR, "node_specs_sample.json")


def load_scraped_nodes() -> dict[str, Any]:
    """Load scraped Blueprint nodes, preferring full data over sample.

    Returns dict keyed by node name with inputs/outputs/target fields.
    Returns empty dict if no data file is found.
    """
    for path in (_FULL_PATH, _SAMPLE_PATH):
        if os.path.isfile(path):
            with open(path) as f:
                return json.load(f)
    return {}
