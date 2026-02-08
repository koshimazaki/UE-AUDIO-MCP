"""UE5 Editor Python script — dump all Blueprint graphs + audio assets as JSON.

Run INSIDE the UE5 editor via:
  1. Edit > Editor Preferences > Python > enable "Developer Mode"
  2. Window > Developer Tools > Output Log > Python console
  3. Paste:  exec(open('/path/to/dump_blueprints_ue5.py').read())

Or via console command:
  py exec(open('/path/to/dump_blueprints_ue5.py').read())

Output:
  {ProjectDir}/Saved/AudioMCP/blueprint_scan.json
  {ProjectDir}/Saved/AudioMCP/audio_assets.json
  {ProjectDir}/Saved/AudioMCP/anim_notifies.json

Requirements:
  - Editor Scripting Utilities plugin enabled
  - Python Editor Script Plugin enabled
"""

import unreal
import json
import os

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "AudioMCP")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BLUEPRINT_CLASSES = ["Blueprint", "WidgetBlueprint", "AnimBlueprint"]
AUDIO_CLASSES = [
    "SoundWave", "SoundCue", "MetaSoundSource", "MetaSoundPatch",
    "SoundAttenuation", "SoundClass", "SoundConcurrency", "SoundMix",
    "ReverbEffect", "SoundControlBus", "SoundControlBusMix",
]
ANIM_CLASSES = ["AnimSequence", "AnimMontage"]

AUDIO_KEYWORDS = {
    "PlaySound", "SpawnSound", "PostEvent", "PlayMetaSound",
    "SetSwitch", "SetState", "SetRTPCValue", "PostTrigger",
    "AudioComponent", "PlaySound2D", "SpawnSoundAtLocation",
    "SpawnSoundAttached", "SetFloatParameter", "SetIntParameter",
    "OnAudioFinished", "FadeIn", "FadeOut", "SetVolumeMultiplier",
    "SetPitchMultiplier", "AkAudioEvent", "PostAkEvent",
}

INTERACTION_KEYWORDS = {
    "OnComponentBeginOverlap", "OnComponentEndOverlap",
    "OnComponentHit", "OnActorBeginOverlap",
    "AnimNotify", "PlayAnimMontage",
    "InputAction", "EnhancedInputAction",
    "GameplayAbility", "ActivateAbility",
    "SpawnActor", "DestroyActor",
    "OnClicked", "OnPressed", "OnReleased",
    "LineTrace", "SweepTrace",
    "GetPhysicalMaterial", "PhysicalMaterial",
    "SetTimer", "Timeline",
}

ALL_KEYWORDS = AUDIO_KEYWORDS | INTERACTION_KEYWORDS


# ---------------------------------------------------------------------------
# Asset scanning
# ---------------------------------------------------------------------------

def get_asset_registry():
    return unreal.AssetRegistryHelpers.get_asset_registry()


def find_assets_by_class(class_names):
    registry = get_asset_registry()
    results = []
    for class_name in class_names:
        ar_filter = unreal.ARFilter()
        ar_filter.class_names = [unreal.Name(class_name)]
        ar_filter.recursive_classes = True
        assets = registry.get_assets(ar_filter)
        for asset in assets:
            results.append({
                "package_name": str(asset.package_name),
                "asset_name": str(asset.asset_name),
                "asset_class": str(asset.asset_class_path.asset_name) if hasattr(asset, 'asset_class_path') else class_name,
                "package_path": str(asset.package_path),
            })
    return results


# ---------------------------------------------------------------------------
# Blueprint graph inspection
# ---------------------------------------------------------------------------

def inspect_blueprint(asset_path):
    bp = unreal.EditorAssetLibrary.load_asset(asset_path)
    if bp is None:
        return None

    result = {
        "path": asset_path,
        "name": str(bp.get_name()),
        "parent_class": "",
        "graphs": [],
        "variables": [],
        "components": [],
        "audio_relevant": False,
        "audio_nodes": [],
        "interaction_nodes": [],
    }

    # Parent class
    try:
        gen_class = bp.get_editor_property("generated_class")
        if gen_class:
            parent = gen_class.get_super_class()
            if parent:
                result["parent_class"] = str(parent.get_name())
    except Exception:
        pass

    # Components
    try:
        scs = bp.get_editor_property("simple_construction_script")
        if scs:
            all_nodes = scs.get_all_nodes()
            for scs_node in all_nodes:
                comp_template = scs_node.get_editor_property("component_template")
                if comp_template:
                    comp_info = {
                        "name": str(comp_template.get_name()),
                        "class": str(comp_template.get_class().get_name()),
                    }
                    result["components"].append(comp_info)
                    if "Audio" in comp_info["class"] or "Sound" in comp_info["class"]:
                        result["audio_relevant"] = True
    except Exception:
        pass

    # Event graphs
    try:
        graphs = bp.get_editor_property("ubergraph_pages")
        if graphs:
            for graph in graphs:
                graph_data = inspect_graph(graph)
                result["graphs"].append(graph_data)
                for node in graph_data.get("nodes", []):
                    node_title = node.get("title", "")
                    node_class = node.get("class", "")
                    combined = node_title + " " + node_class
                    for kw in AUDIO_KEYWORDS:
                        if kw.lower() in combined.lower():
                            result["audio_nodes"].append({
                                "keyword": kw,
                                "node_title": node_title,
                                "node_class": node_class,
                                "graph": graph_data.get("name", ""),
                            })
                            result["audio_relevant"] = True
                            break
                    for kw in INTERACTION_KEYWORDS:
                        if kw.lower() in combined.lower():
                            result["interaction_nodes"].append({
                                "keyword": kw,
                                "node_title": node_title,
                                "node_class": node_class,
                                "graph": graph_data.get("name", ""),
                            })
                            break
    except Exception as e:
        result["graphs_error"] = str(e)

    # Function graphs
    try:
        func_graphs = bp.get_editor_property("function_graphs")
        if func_graphs:
            for graph in func_graphs:
                graph_data = inspect_graph(graph)
                graph_data["type"] = "function"
                result["graphs"].append(graph_data)
    except Exception:
        pass

    # Variables
    try:
        new_vars = bp.get_editor_property("new_variables")
        if new_vars:
            for var in new_vars:
                result["variables"].append({
                    "name": str(var.get_editor_property("var_name")),
                    "type": str(var.get_editor_property("var_type")),
                })
    except Exception:
        pass

    return result


def inspect_graph(graph):
    graph_data = {
        "name": str(graph.get_name()),
        "type": "event",
        "nodes": [],
    }

    try:
        schema = graph.get_editor_property("schema")
        if schema:
            graph_data["schema"] = str(schema.get_class().get_name())
    except Exception:
        pass

    try:
        nodes = graph.get_editor_property("nodes")
        if nodes:
            for node in nodes:
                node_data = inspect_node(node)
                if node_data:
                    graph_data["nodes"].append(node_data)
    except Exception as e:
        graph_data["nodes_error"] = str(e)

    return graph_data


def inspect_node(node):
    if node is None:
        return None

    node_data = {
        "class": str(node.get_class().get_name()),
        "title": "",
        "pins": [],
        "position": {"x": 0, "y": 0},
    }

    try:
        node_data["title"] = str(node.get_node_title(unreal.NodeTitleType.FULL_TITLE))
    except Exception:
        try:
            node_data["title"] = str(node.get_name())
        except Exception:
            pass

    try:
        node_data["position"]["x"] = node.get_editor_property("node_pos_x")
        node_data["position"]["y"] = node.get_editor_property("node_pos_y")
    except Exception:
        pass

    try:
        pins = node.get_all_pins()
        if pins:
            for pin in pins:
                pin_data = {
                    "name": str(pin.get_name()),
                    "direction": "input" if pin.direction == unreal.EdGraphPinDirection.EGPD_INPUT else "output",
                    "type": str(pin.pin_type),
                    "connected": bool(pin.linked_to),
                }
                if pin.linked_to:
                    pin_data["connected_to"] = []
                    for linked_pin in pin.linked_to:
                        owner = linked_pin.get_owning_node()
                        pin_data["connected_to"].append({
                            "node": str(owner.get_name()) if owner else "?",
                            "pin": str(linked_pin.get_name()),
                        })
                node_data["pins"].append(pin_data)
    except Exception:
        pass

    try:
        comment = node.get_editor_property("node_comment")
        if comment:
            node_data["comment"] = str(comment)
    except Exception:
        pass

    return node_data


# ---------------------------------------------------------------------------
# Animation notify scanning
# ---------------------------------------------------------------------------

def scan_anim_notifies():
    results = []
    assets = find_assets_by_class(ANIM_CLASSES)

    for asset_info in assets:
        try:
            anim = unreal.EditorAssetLibrary.load_asset(asset_info["package_name"])
            if anim is None:
                continue

            notifies = []
            try:
                anim_notifies = anim.get_editor_property("notifies")
                if anim_notifies:
                    for notify in anim_notifies:
                        notify_data = {
                            "trigger_time": notify.get_editor_property("trigger_time_offset"),
                            "notify_name": str(notify.get_editor_property("notify_name")),
                        }
                        try:
                            notify_obj = notify.get_editor_property("notify")
                            if notify_obj:
                                notify_data["class"] = str(notify_obj.get_class().get_name())
                        except Exception:
                            pass
                        try:
                            notify_state = notify.get_editor_property("notify_state_class")
                            if notify_state:
                                notify_data["state_class"] = str(notify_state.get_name())
                        except Exception:
                            pass
                        notifies.append(notify_data)
            except Exception:
                pass

            if notifies:
                results.append({
                    "path": asset_info["package_name"],
                    "name": asset_info["asset_name"],
                    "class": asset_info["asset_class"],
                    "notifies": notifies,
                })
        except Exception:
            continue

    return results


# ---------------------------------------------------------------------------
# Audio asset scanning
# ---------------------------------------------------------------------------

def scan_audio_assets():
    results = {
        "metasounds": [],
        "sound_waves": [],
        "sound_cues": [],
        "attenuation": [],
        "sound_classes": [],
        "reverb_effects": [],
        "control_buses": [],
        "other": [],
    }

    assets = find_assets_by_class(AUDIO_CLASSES)

    for asset_info in assets:
        cls = asset_info["asset_class"]
        entry = {
            "path": asset_info["package_name"],
            "name": asset_info["asset_name"],
            "class": cls,
        }

        if "MetaSound" in cls:
            results["metasounds"].append(entry)
        elif cls == "SoundWave":
            results["sound_waves"].append(entry)
        elif cls == "SoundCue":
            results["sound_cues"].append(entry)
        elif cls == "SoundAttenuation":
            results["attenuation"].append(entry)
        elif cls == "SoundClass":
            results["sound_classes"].append(entry)
        elif cls == "ReverbEffect":
            results["reverb_effects"].append(entry)
        elif "ControlBus" in cls:
            results["control_buses"].append(entry)
        else:
            results["other"].append(entry)

    results["summary"] = {
        "total": sum(len(v) for v in results.values() if isinstance(v, list)),
        "metasounds": len(results["metasounds"]),
        "sound_waves": len(results["sound_waves"]),
        "sound_cues": len(results["sound_cues"]),
        "attenuation": len(results["attenuation"]),
        "sound_classes": len(results["sound_classes"]),
        "reverb_effects": len(results["reverb_effects"]),
        "control_buses": len(results["control_buses"]),
    }

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    unreal.log("=" * 60)
    unreal.log("[AudioMCP] Starting project audio scan...")
    unreal.log("=" * 60)

    # 1. Audio assets
    unreal.log("[AudioMCP] Scanning audio assets...")
    audio = scan_audio_assets()
    audio_path = os.path.join(OUTPUT_DIR, "audio_assets.json")
    with open(audio_path, "w") as f:
        json.dump(audio, f, indent=2)
    unreal.log("[AudioMCP] Audio assets: {} total".format(audio["summary"]["total"]))
    for k, v in audio["summary"].items():
        if k != "total":
            unreal.log("[AudioMCP]   {}: {}".format(k, v))

    # 2. Anim notifies
    unreal.log("[AudioMCP] Scanning animation notifies...")
    notifies = scan_anim_notifies()
    notifies_path = os.path.join(OUTPUT_DIR, "anim_notifies.json")
    with open(notifies_path, "w") as f:
        json.dump(notifies, f, indent=2)
    unreal.log("[AudioMCP] Anim assets with notifies: {}".format(len(notifies)))

    # 3. Blueprints
    unreal.log("[AudioMCP] Scanning Blueprints for audio interactions...")
    bp_assets = find_assets_by_class(BLUEPRINT_CLASSES)
    unreal.log("[AudioMCP] Found {} Blueprint assets, inspecting...".format(len(bp_assets)))

    all_bps = []
    audio_bps = []
    interaction_bps = []

    for i, asset_info in enumerate(bp_assets):
        if i % 50 == 0:
            unreal.log("[AudioMCP]   Progress: {}/{}".format(i, len(bp_assets)))

        bp_data = inspect_blueprint(asset_info["package_name"])
        if bp_data is None:
            continue

        all_bps.append(bp_data)
        if bp_data.get("audio_relevant"):
            audio_bps.append(bp_data)
        if bp_data.get("interaction_nodes"):
            interaction_bps.append(bp_data)

    bp_path = os.path.join(OUTPUT_DIR, "blueprint_scan.json")
    with open(bp_path, "w") as f:
        json.dump({
            "total_scanned": len(all_bps),
            "audio_relevant": len(audio_bps),
            "interaction_relevant": len(interaction_bps),
            "blueprints": all_bps,
        }, f, indent=2)

    # 4. Summary
    unreal.log("=" * 60)
    unreal.log("[AudioMCP] SCAN COMPLETE")
    unreal.log("=" * 60)
    unreal.log("[AudioMCP] Audio assets: {}".format(audio["summary"]["total"]))
    unreal.log("[AudioMCP]   MetaSounds: {}".format(audio["summary"]["metasounds"]))
    unreal.log("[AudioMCP]   SoundWaves: {}".format(audio["summary"]["sound_waves"]))
    unreal.log("[AudioMCP] Anim notifies: {} assets with notifies".format(len(notifies)))
    unreal.log("[AudioMCP] Blueprints scanned: {}".format(len(all_bps)))
    unreal.log("[AudioMCP]   Audio-relevant: {}".format(len(audio_bps)))
    unreal.log("[AudioMCP]   With interactions: {}".format(len(interaction_bps)))
    unreal.log("")

    if audio_bps:
        unreal.log("[AudioMCP] Audio-relevant Blueprints:")
        for bp in audio_bps:
            audio_kws = set(n["keyword"] for n in bp.get("audio_nodes", []))
            unreal.log("[AudioMCP]   {} ({}) -- {}".format(
                bp["name"], bp["parent_class"], ", ".join(sorted(audio_kws))
            ))

    if interaction_bps:
        unreal.log("")
        unreal.log("[AudioMCP] Interaction Blueprints (audio hookup candidates):")
        for bp in interaction_bps:
            int_kws = set(n["keyword"] for n in bp.get("interaction_nodes", []))
            has_audio = "YES" if bp.get("audio_relevant") else "NO"
            unreal.log("[AudioMCP]   {} -- interactions: {} | audio wired: {}".format(
                bp["name"], ", ".join(sorted(int_kws)), has_audio
            ))

    unreal.log("")
    unreal.log("[AudioMCP] Output saved to: {}".format(OUTPUT_DIR))
    unreal.log("[AudioMCP]   blueprint_scan.json")
    unreal.log("[AudioMCP]   audio_assets.json")
    unreal.log("[AudioMCP]   anim_notifies.json")


main()
