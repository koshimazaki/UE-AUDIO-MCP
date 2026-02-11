"""Tests for MetaSounds engine sync — ms_sync_from_engine + helpers."""

from __future__ import annotations

import json

import ue_audio_mcp.ue5_connection as ue5_module
from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES, CLASS_NAME_TO_DISPLAY
from ue_audio_mcp.tools.ms_builder import (
    ms_sync_from_engine,
    _engine_node_to_nodedef,
    _normalize_pin_type,
    _infer_category,
)


# ---------------------------------------------------------------------------
# Sample engine node responses for testing
# ---------------------------------------------------------------------------

def _make_engine_node(
    class_name: str = "UE::TestNode::Audio",
    namespace: str = "UE",
    name: str = "TestNode",
    variant: str = "Audio",
    inputs: list | None = None,
    outputs: list | None = None,
    category: str = "",
    description: str = "",
    keywords: list | None = None,
    deprecated: bool = False,
) -> dict:
    """Build a mock engine node dict."""
    return {
        "class_name": class_name,
        "namespace": namespace,
        "name": name,
        "variant": variant,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "category": category,
        "description": description,
        "keywords": keywords or [],
        "deprecated": deprecated,
    }


MOCK_ENGINE_RESPONSE = {
    "status": "ok",
    "message": "Found 5 node classes (5 shown)",
    "total": 5,
    "shown": 5,
    "nodes": [
        _make_engine_node(
            class_name="UE::Sine::Audio",
            namespace="UE", name="Sine", variant="Audio",
            inputs=[
                {"name": "Enabled", "type": "Bool", "default": True},
                {"name": "Frequency", "type": "Float", "default": 440.0},
            ],
            outputs=[{"name": "Audio", "type": "Audio"}],
            category="Generators|Oscillators",
            description="Pure sine wave oscillator.",
        ),
        _make_engine_node(
            class_name="UE::NewSuperFilter::Audio",
            namespace="UE", name="NewSuperFilter", variant="Audio",
            inputs=[
                {"name": "In", "type": "Audio"},
                {"name": "Cutoff", "type": "Float", "default": 1000.0},
                {"name": "Resonance", "type": "Float", "default": 0.5},
            ],
            outputs=[{"name": "Out", "type": "Audio"}],
            category="Filters",
            description="A brand new filter node.",
        ),
        _make_engine_node(
            class_name="UE::Add::Float",
            namespace="UE", name="Add", variant="Float",
            inputs=[
                {"name": "PrimaryOperand", "type": "Float"},
                {"name": "AdditionalOperands", "type": "Float"},
            ],
            outputs=[{"name": "Out", "type": "Float"}],
            category="Math",
        ),
        _make_engine_node(
            class_name="UE::NoiseGen::Enum:ENoiseType",
            namespace="UE", name="NoiseGen", variant="Enum:ENoiseType",
            inputs=[
                {"name": "Type", "type": "Enum:ENoiseType"},
                {"name": "Seed", "type": "Int32"},
            ],
            outputs=[{"name": "Audio", "type": "Audio"}],
            category="Generators",
        ),
        _make_engine_node(
            class_name="", namespace="", name="", variant="",
            inputs=[], outputs=[],
        ),
    ],
}


# ---------------------------------------------------------------------------
# _engine_node_to_nodedef tests
# ---------------------------------------------------------------------------

class TestEngineNodeToNodedef:
    def test_basic_conversion(self):
        enode = _make_engine_node(
            class_name="UE::TestOsc::Audio",
            name="TestOsc", variant="Audio",
            inputs=[{"name": "Freq", "type": "Float", "default": 440.0}],
            outputs=[{"name": "Audio", "type": "Audio"}],
            category="Generators",
            description="Test oscillator.",
        )
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        assert result["name"] == "TestOsc (Audio)"
        assert result["category"] == "Generators"
        assert result["description"] == "Test oscillator."
        assert len(result["inputs"]) == 1
        assert result["inputs"][0]["name"] == "Freq"
        assert result["inputs"][0]["type"] == "Float"
        assert result["inputs"][0]["default"] == 440.0
        assert len(result["outputs"]) == 1
        assert result["outputs"][0]["name"] == "Audio"

    def test_none_variant_uses_plain_name(self):
        enode = _make_engine_node(name="BPMToSeconds", variant="None")
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        assert result["name"] == "BPMToSeconds"

    def test_empty_variant_uses_plain_name(self):
        enode = _make_engine_node(name="SomeNode", variant="")
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        assert result["name"] == "SomeNode"

    def test_empty_name_returns_none(self):
        enode = _make_engine_node(name="", variant="")
        result = _engine_node_to_nodedef(enode)
        assert result is None

    def test_existing_display_name_used(self):
        """If CLASS_NAME_TO_DISPLAY already has a mapping, use it."""
        enode = _make_engine_node(
            class_name="UE::Sine::Audio",
            name="Sine", variant="Audio",
        )
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        # Should use the existing catalogue name "Sine" not "Sine (Audio)"
        assert result["name"] == "Sine"

    def test_default_description_generated(self):
        enode = _make_engine_node(name="FooNode", variant="Bar", description="")
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        assert "FooNode" in result["description"]

    def test_keywords_become_tags(self):
        enode = _make_engine_node(
            name="TestNode", variant="Audio",
            keywords=["Synth", "Oscillator"],
        )
        result = _engine_node_to_nodedef(enode)
        assert result is not None
        assert "synth" in result["tags"]
        assert "oscillator" in result["tags"]


# ---------------------------------------------------------------------------
# _normalize_pin_type tests
# ---------------------------------------------------------------------------

class TestNormalizePinType:
    def test_simple_types(self):
        assert _normalize_pin_type("Audio") == "Audio"
        assert _normalize_pin_type("Float") == "Float"
        assert _normalize_pin_type("Int32") == "Int32"
        assert _normalize_pin_type("Bool") == "Bool"
        assert _normalize_pin_type("Trigger") == "Trigger"

    def test_enum_type(self):
        assert _normalize_pin_type("Enum:ENoiseType") == "Enum"

    def test_empty_defaults_to_audio(self):
        assert _normalize_pin_type("") == "Audio"

    def test_namespaced_type(self):
        result = _normalize_pin_type("MetasoundFrontend:Trigger")
        assert result == "Trigger"


# ---------------------------------------------------------------------------
# _infer_category tests
# ---------------------------------------------------------------------------

class TestInferCategory:
    def test_from_category_field(self):
        assert _infer_category({"category": "Generators|Oscillators"}) == "Generators"

    def test_filter_keyword(self):
        assert _infer_category({"category": "Filter Nodes"}) == "Filters"

    def test_from_namespace_fallback(self):
        assert _infer_category({"category": "", "namespace": "UE", "name": "Delay"}) == "Effects"

    def test_unknown_returns_other(self):
        assert _infer_category({"category": "", "namespace": "", "name": "XyzUnknown"}) == "Other"

    def test_math_category(self):
        assert _infer_category({"category": "Math Operations"}) == "Math"

    def test_pipe_delimited_last_segment(self):
        result = _infer_category({"category": "Audio|Custom|SpecialNodes"})
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# ms_sync_from_engine tool tests
# ---------------------------------------------------------------------------

class TestMsSyncFromEngine:
    def test_sync_basic(self, ue5_conn, mock_ue5_plugin):
        """Sync with mock response, verify new + updated counts."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)

        # Track catalogue size before
        size_before = len(METASOUND_NODES)

        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        assert result["total"] == 5
        # Sine exists, so it's updated; empty-name node is skipped
        # NewSuperFilter, Add (Float), NoiseGen are candidates for new/update
        assert result["new"] + result["updated"] > 0
        assert result["catalogue_size"] >= size_before

    def test_sync_updates_existing_pins(self, ue5_conn, mock_ue5_plugin):
        """Verify that existing node pins are overwritten by engine data."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)

        # Get Sine's original inputs for comparison
        original_sine_inputs = [p.copy() for p in METASOUND_NODES["Sine"]["inputs"]]

        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"

        # Sine's inputs should now match the mock (2 pins: Enabled, Frequency)
        sine = METASOUND_NODES["Sine"]
        pin_names = [p["name"] for p in sine["inputs"]]
        assert "Enabled" in pin_names
        assert "Frequency" in pin_names

        # Restore original for other tests
        METASOUND_NODES["Sine"]["inputs"] = original_sine_inputs

    def test_sync_adds_new_nodes(self, ue5_conn, mock_ue5_plugin):
        """Verify new nodes from engine get added to catalogue."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)

        # Remove test node if it exists from a previous run
        METASOUND_NODES.pop("NewSuperFilter (Audio)", None)

        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        assert "NewSuperFilter (Audio)" in METASOUND_NODES

        nsf = METASOUND_NODES["NewSuperFilter (Audio)"]
        assert nsf["category"] == "Filters"
        assert len(nsf["inputs"]) == 3
        assert len(nsf["outputs"]) == 1

        # Clean up
        METASOUND_NODES.pop("NewSuperFilter (Audio)", None)

    def test_sync_skips_empty_name(self, ue5_conn, mock_ue5_plugin):
        """Nodes with empty names should be silently skipped."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)
        size_before = len(METASOUND_NODES)
        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        # Empty-name node should not be added
        assert "" not in METASOUND_NODES

    def test_sync_not_connected(self):
        """Should return error when not connected to UE5 plugin."""
        ue5_module._connection = None
        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "error"
        assert "Not connected" in result["message"]
        ue5_module._connection = None

    def test_sync_empty_response(self, ue5_conn, mock_ue5_plugin):
        """Empty node list from engine should return gracefully."""
        mock_ue5_plugin.set_response("list_metasound_nodes", {
            "status": "ok", "nodes": [], "total": 0, "shown": 0,
            "message": "Found 0 node classes (0 shown)",
        })
        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        assert result["total"] == 0
        assert result["new"] == 0

    def test_sync_error_response(self, ue5_conn, mock_ue5_plugin):
        """Engine error should be forwarded."""
        mock_ue5_plugin.set_response("list_metasound_nodes", {
            "status": "error", "message": "SearchEngine not available",
        })
        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "error"
        assert "SearchEngine" in result["message"]

    def test_sync_updates_class_name_mapping(self, ue5_conn, mock_ue5_plugin):
        """New class_name -> display_name mappings should be added."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)

        # Remove the mapping if it exists
        CLASS_NAME_TO_DISPLAY.pop("UE::NewSuperFilter::Audio", None)

        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        assert "UE::NewSuperFilter::Audio" in CLASS_NAME_TO_DISPLAY

        # Clean up
        CLASS_NAME_TO_DISPLAY.pop("UE::NewSuperFilter::Audio", None)
        METASOUND_NODES.pop("NewSuperFilter (Audio)", None)

    def test_sync_with_filter(self, ue5_conn, mock_ue5_plugin):
        """Filter param should be forwarded to the engine command."""
        mock_ue5_plugin.set_response("list_metasound_nodes", {
            "status": "ok", "nodes": [], "total": 0, "shown": 0,
            "message": "Found 0 node classes (0 shown)",
        })
        result = json.loads(ms_sync_from_engine(filter="Sine"))
        assert result["status"] == "ok"
        # Verify the command was sent with filter
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["action"] == "list_metasound_nodes"
        assert cmd["filter"] == "Sine"

    def test_sync_returns_categories(self, ue5_conn, mock_ue5_plugin):
        """Sync result should include category breakdown."""
        mock_ue5_plugin.set_response("list_metasound_nodes", MOCK_ENGINE_RESPONSE)
        result = json.loads(ms_sync_from_engine())
        assert result["status"] == "ok"
        assert "categories" in result
        assert isinstance(result["categories"], dict)


# ---------------------------------------------------------------------------
# Standalone script diff logic
# ---------------------------------------------------------------------------

class TestScriptDiffLogic:
    def test_build_diff_new_node(self):
        """New nodes should appear in diff."""
        from scripts.sync_nodes_from_engine import _build_diff

        engine_nodes = [_make_engine_node(
            class_name="UE::BrandNew::Audio",
            name="BrandNew", variant="Audio",
            inputs=[{"name": "In", "type": "Audio"}],
            outputs=[{"name": "Out", "type": "Audio"}],
            category="Effects",
        )]
        diff = _build_diff(engine_nodes, METASOUND_NODES)
        assert diff["new_count"] >= 1
        new_names = [n["name"] for n in diff["new_nodes"]]
        assert "BrandNew (Audio)" in new_names

    def test_build_diff_pin_changes(self):
        """Pin differences should be detected."""
        from scripts.sync_nodes_from_engine import _build_diff

        # Use Sine which exists in catalogue
        engine_nodes = [_make_engine_node(
            class_name="UE::Sine::Audio",
            name="Sine", variant="Audio",
            inputs=[
                {"name": "Enabled", "type": "Bool"},
                {"name": "Frequency", "type": "Float"},
                {"name": "BrandNewPin", "type": "Audio"},
            ],
            outputs=[{"name": "Audio", "type": "Audio"}],
        )]
        diff = _build_diff(engine_nodes, METASOUND_NODES)
        # Should detect pin changes (Sine has more pins in catalogue)
        assert diff["total_pin_changes"] > 0
