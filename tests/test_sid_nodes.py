"""Tests for SID MetaSounds node definitions, templates, and orchestrator pattern."""

from __future__ import annotations

import json
import os

from ue_audio_mcp.knowledge.metasound_nodes import (
    METASOUND_NODES,
    get_nodes_by_category,
    search_nodes,
)


# ===================================================================
# SID Node Definitions
# ===================================================================

SID_NODE_NAMES = [
    "SID Oscillator",
    "SID Envelope",
    "SID Filter",
    "SID Voice",
    "SID Chip",
]


def test_all_sid_nodes_registered():
    """All 5 SID nodes must be present in the catalogue."""
    for name in SID_NODE_NAMES:
        assert name in METASOUND_NODES, f"Missing SID node: {name}"


def test_sid_nodes_in_sidkit_category():
    """All SID nodes must be in the ReSID SIDKIT Edition category."""
    sidkit_nodes = get_nodes_by_category("ReSID SIDKIT Edition")
    assert len(sidkit_nodes) == 5
    names = {n["name"] for n in sidkit_nodes}
    assert names == set(SID_NODE_NAMES)


def test_sid_oscillator_pins():
    """SID Oscillator must have correct input/output pins."""
    node = METASOUND_NODES["SID Oscillator"]
    in_names = {p["name"] for p in node["inputs"]}
    assert "Frequency" in in_names
    assert "Pulse Width" in in_names
    assert "Waveform" in in_names
    assert "Chip Model" in in_names
    out_names = {p["name"] for p in node["outputs"]}
    assert "Out" in out_names


def test_sid_envelope_pins():
    """SID Envelope must have Gate trigger and ADSR int inputs."""
    node = METASOUND_NODES["SID Envelope"]
    in_names = {p["name"] for p in node["inputs"]}
    assert "Gate" in in_names
    assert "Attack" in in_names
    assert "Decay" in in_names
    assert "Sustain" in in_names
    assert "Release" in in_names
    for pin in node["inputs"]:
        if pin["name"] == "Gate":
            assert pin["type"] == "Trigger"
        elif pin["name"] in ("Attack", "Decay", "Sustain", "Release"):
            assert pin["type"] == "Int32"


def test_sid_filter_pins():
    """SID Filter must have audio in/out and filter controls."""
    node = METASOUND_NODES["SID Filter"]
    in_names = {p["name"] for p in node["inputs"]}
    assert "In" in in_names
    assert "Cutoff" in in_names
    assert "Resonance" in in_names
    assert "Mode" in in_names
    assert "Chip Model" in in_names
    assert "Res Boost" in in_names
    for pin in node["inputs"]:
        if pin["name"] == "In":
            assert pin["type"] == "Audio"


def test_sid_voice_pins():
    """SID Voice must combine oscillator + envelope pins."""
    node = METASOUND_NODES["SID Voice"]
    in_names = {p["name"] for p in node["inputs"]}
    assert "Gate" in in_names
    assert "Frequency" in in_names
    assert "Waveform" in in_names
    assert "Attack" in in_names
    assert "Release" in in_names


def test_sid_chip_pins():
    """SID Chip must have 3-voice inputs + filter + global controls."""
    node = METASOUND_NODES["SID Chip"]
    in_names = {p["name"] for p in node["inputs"]}
    for v in (1, 2, 3):
        assert f"Gate {v}" in in_names
        assert f"Freq {v}" in in_names
        assert f"PW {v}" in in_names
        assert f"Wave {v}" in in_names
        assert f"A {v}" in in_names
        assert f"D {v}" in in_names
        assert f"S {v}" in in_names
        assert f"R {v}" in in_names
    assert "Filter Cutoff" in in_names
    assert "Filter Resonance" in in_names
    assert "Filter Mode" in in_names
    assert "Filter Routing" in in_names
    assert "Volume" in in_names
    assert "Chip Model" in in_names
    assert "Res Boost" in in_names
    out_names = {p["name"] for p in node["outputs"]}
    assert "Out" in out_names
    assert "Voice 1 Out" in out_names
    assert "Voice 2 Out" in out_names
    assert "Voice 3 Out" in out_names


def test_sid_nodes_have_sid_tag():
    """All SID nodes must have the 'sid' tag for search."""
    for name in SID_NODE_NAMES:
        node = METASOUND_NODES[name]
        assert "sid" in node["tags"], f"{name} missing 'sid' tag"


def test_search_finds_sid_nodes():
    """Searching for 'sid' should find all 5 SID nodes."""
    results = search_nodes("sid")
    result_names = {n["name"] for n in results}
    for name in SID_NODE_NAMES:
        assert name in result_names, f"Search for 'sid' missed {name}"


def test_search_chiptune():
    """Searching for 'chiptune' should find SID nodes."""
    results = search_nodes("chiptune")
    result_names = {n["name"] for n in results}
    assert len(result_names) >= 3


def test_search_c64():
    """Searching for 'c64' should find SID nodes."""
    results = search_nodes("c64")
    result_names = {n["name"] for n in results}
    assert len(result_names) >= 4


# ===================================================================
# SID Templates
# ===================================================================

TEMPLATE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "ue_audio_mcp", "templates", "metasounds"
)

SID_TEMPLATES = ["sid_bass.json", "sid_lead.json", "sid_chip_tune.json"]


def test_sid_templates_exist():
    """All 3 SID templates must exist as JSON files."""
    for tpl in SID_TEMPLATES:
        path = os.path.join(TEMPLATE_DIR, tpl)
        assert os.path.exists(path), f"Missing template: {tpl}"


def test_sid_templates_valid_json():
    """All SID templates must be valid JSON."""
    for tpl in SID_TEMPLATES:
        path = os.path.join(TEMPLATE_DIR, tpl)
        with open(path) as f:
            data = json.load(f)
        assert "name" in data
        assert "nodes" in data
        assert "connections" in data
        assert data["asset_type"] == "Source"


def test_sid_bass_template_structure():
    """SID Bass template must use SID Voice and SID Filter nodes."""
    path = os.path.join(TEMPLATE_DIR, "sid_bass.json")
    with open(path) as f:
        data = json.load(f)
    node_types = {n["node_type"] for n in data["nodes"]}
    assert "SID Voice" in node_types
    assert "SID Filter" in node_types
    assert "SID Envelope" in node_types


def test_sid_lead_template_structure():
    """SID Lead template must use two SID Oscillators and SID Filter."""
    path = os.path.join(TEMPLATE_DIR, "sid_lead.json")
    with open(path) as f:
        data = json.load(f)
    node_types = [n["node_type"] for n in data["nodes"]]
    osc_count = sum(1 for t in node_types if t == "SID Oscillator")
    assert osc_count == 2, f"Expected 2 SID Oscillators, got {osc_count}"
    assert "SID Filter" in node_types
    assert "SID Envelope" in node_types


def test_sid_chip_tune_template_structure():
    """SID Chip Tune template must use the full SID Chip node."""
    path = os.path.join(TEMPLATE_DIR, "sid_chip_tune.json")
    with open(path) as f:
        data = json.load(f)
    node_types = {n["node_type"] for n in data["nodes"]}
    assert "SID Chip" in node_types


def test_sid_templates_connections_reference_valid_nodes():
    """All connections in SID templates must reference existing node IDs."""
    for tpl in SID_TEMPLATES:
        path = os.path.join(TEMPLATE_DIR, tpl)
        with open(path) as f:
            data = json.load(f)
        node_ids = {n["id"] for n in data["nodes"]}
        node_ids.add("__graph__")
        for conn in data["connections"]:
            assert conn["from_node"] in node_ids, f"{tpl}: unknown from_node '{conn['from_node']}'"
            assert conn["to_node"] in node_ids, f"{tpl}: unknown to_node '{conn['to_node']}'"


# ===================================================================
# SID Orchestrator Pattern
# ===================================================================

def test_sid_synth_pattern_registered():
    """The sid_synth pattern must be in the orchestrator PATTERNS registry."""
    from ue_audio_mcp.tools.systems import PATTERNS
    assert "sid_synth" in PATTERNS


def test_sid_synth_pattern_uses_chip_tune_template():
    """The sid_synth pattern must reference the sid_chip_tune template."""
    from ue_audio_mcp.tools.systems import PATTERNS
    pattern = PATTERNS["sid_synth"]
    assert pattern["ms_template"] == "sid_chip_tune"


def test_sid_synth_pattern_has_default_params():
    """The sid_synth pattern must have sensible default parameters."""
    from ue_audio_mcp.tools.systems import PATTERNS
    params = PATTERNS["sid_synth"]["default_params"]["metasounds"]
    assert "Lead Freq" in params
    assert "Bass Freq" in params
    assert "Filter Cutoff" in params


def test_sid_synth_pattern_wiring():
    """The sid_synth pattern must have blueprint to metasound wiring."""
    from ue_audio_mcp.tools.systems import PATTERNS
    wiring = PATTERNS["sid_synth"]["connections"]["wiring"]
    assert len(wiring) >= 3
    trigger_wires = [w for w in wiring if w["type"] == "trigger"]
    assert len(trigger_wires) >= 1
    param_wires = [w for w in wiring if w["type"] == "param"]
    assert len(param_wires) >= 2


# ===================================================================
# C++ File Structure (existence checks)
# ===================================================================

PLUGIN_DIR = os.path.join(
    os.path.dirname(__file__), "..", "ue5_plugin", "UEAudioMCP"
)


def test_sid_module_files_exist():
    """SIDMetaSoundNodes module scaffold files must exist."""
    expected = [
        "Source/SIDMetaSoundNodes/SIDMetaSoundNodes.Build.cs",
        "Source/SIDMetaSoundNodes/Public/SIDMetaSoundNodesModule.h",
        "Source/SIDMetaSoundNodes/Public/SIDNodeEnums.h",
        "Source/SIDMetaSoundNodes/Private/SIDMetaSoundNodesModule.cpp",
        "Source/SIDMetaSoundNodes/Private/SIDNodeEnums.cpp",
    ]
    for rel in expected:
        path = os.path.join(PLUGIN_DIR, rel)
        assert os.path.exists(path), f"Missing module file: {rel}"


def test_sid_node_cpp_files_exist():
    """All 5 SID node .cpp files must exist."""
    expected = [
        "SIDOscillatorNode.cpp",
        "SIDEnvelopeNode.cpp",
        "SIDFilterNode.cpp",
        "SIDVoiceNode.cpp",
        "SIDChipNode.cpp",
    ]
    nodes_dir = os.path.join(PLUGIN_DIR, "Source", "SIDMetaSoundNodes", "Private", "Nodes")
    for fname in expected:
        path = os.path.join(nodes_dir, fname)
        assert os.path.exists(path), f"Missing node file: {fname}"


def test_resid_thirdparty_files_exist():
    """ReSID ThirdParty files must be copied."""
    thirdparty = os.path.join(PLUGIN_DIR, "Source", "ThirdParty", "ReSID")
    assert os.path.isdir(thirdparty), "ThirdParty/ReSID directory missing"
    key_files = ["sid.h", "siddefs.h", "filter.h", "voice.h",
                 "envelope.h", "filter_new.h", "filter_new_impl.h"]
    for fname in key_files:
        path = os.path.join(thirdparty, fname)
        assert os.path.exists(path), f"Missing reSID file: {fname}"


def test_uplugin_has_sid_module():
    """The .uplugin must list SIDMetaSoundNodes as a Runtime module."""
    path = os.path.join(PLUGIN_DIR, "UEAudioMCP.uplugin")
    with open(path) as f:
        data = json.load(f)
    modules = {m["Name"]: m for m in data["Modules"]}
    assert "SIDMetaSoundNodes" in modules
    assert modules["SIDMetaSoundNodes"]["Type"] == "Runtime"
    assert modules["SIDMetaSoundNodes"]["LoadingPhase"] == "Default"


def test_node_registry_has_sid_entries():
    """The AudioMCPNodeRegistry.h must contain SID node mappings."""
    path = os.path.join(PLUGIN_DIR, "Source", "UEAudioMCP", "Public", "AudioMCPNodeRegistry.h")
    with open(path) as f:
        content = f.read()
    for node_name in ["SID Oscillator", "SID Envelope", "SID Filter", "SID Voice", "SID Chip"]:
        assert node_name in content, f"Node registry missing: {node_name}"
