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


MODULE_MAP = {
    "Blueprint": "Engine",
    "WidgetBlueprint": "UMGEditor",
    "AnimBlueprint": "Engine",
    "SoundWave": "Engine",
    "SoundCue": "Engine",
    "MetaSoundSource": "MetasoundEngine",
    "MetaSoundPatch": "MetasoundEngine",
    "SoundAttenuation": "Engine",
    "SoundClass": "Engine",
    "SoundConcurrency": "Engine",
    "SoundMix": "Engine",
    "ReverbEffect": "Engine",
    "SoundControlBus": "AudioModulation",
    "SoundControlBusMix": "AudioModulation",
    "AnimSequence": "Engine",
    "AnimMontage": "Engine",
}


def find_assets_by_class(class_names):
    """UE 5.7 compatible: uses get_assets_by_class (no ARFilter needed)."""
    registry = get_asset_registry()
    results = []
    seen = set()
    for class_name in class_names:
        module = MODULE_MAP.get(class_name, "Engine")
        class_path = unreal.TopLevelAssetPath("/Script/" + module, class_name)
        assets = registry.get_assets_by_class(class_path, search_sub_classes=False)
        if not assets and module == "Engine":
            for alt_module in ["MetasoundEngine", "AudioModulation", "UMGEditor"]:
                class_path = unreal.TopLevelAssetPath("/Script/" + alt_module, class_name)
                assets = registry.get_assets_by_class(class_path, search_sub_classes=False)
                if assets:
                    break
        for asset in assets:
            pkg = str(asset.package_name)
            if pkg in seen:
                continue
            seen.add(pkg)
            results.append({
                "package_name": pkg,
                "asset_name": str(asset.asset_name),
                "asset_class": str(asset.asset_class_path.asset_name) if hasattr(asset, 'asset_class_path') else class_name,
                "package_path": str(asset.package_path),
            })
    return results


# ---------------------------------------------------------------------------
# Blueprint graph inspection
# ---------------------------------------------------------------------------

def inspect_blueprint(asset_path):
    """UE 5.7 compatible Blueprint inspection using BlueprintEditorLibrary + CDO."""
    bp = unreal.EditorAssetLibrary.load_asset(asset_path)
    if bp is None:
        return None

    bel = getattr(unreal, "BlueprintEditorLibrary", None)

    result = {
        "path": asset_path,
        "name": str(bp.get_name()),
        "parent_class": "",
        "bp_class": str(bp.get_class().get_name()),
        "graphs": [],
        "variables": [],
        "components": [],
        "audio_relevant": False,
        "audio_nodes": [],
        "interaction_nodes": [],
    }

    # Parent class via BlueprintEditorLibrary.generated_class()
    gen_class = None
    try:
        if bel:
            gen_class = bel.generated_class(bp)
            if gen_class:
                # Walk up the class hierarchy to find the first non-generated parent
                parent = gen_class.get_class()
                parent_name = str(gen_class.get_name())
                # Strip _C suffix to get readable name
                if parent_name.endswith("_C"):
                    parent_name = parent_name[:-2]
                result["parent_class"] = parent_name
    except Exception:
        pass

    # Components via CDO (works in UE 5.7!)
    if gen_class:
        try:
            cdo = unreal.get_default_object(gen_class)
            if cdo:
                all_comps = cdo.get_components_by_class(unreal.ActorComponent)
                if all_comps:
                    for comp in all_comps:
                        comp_class = str(comp.get_class().get_name())
                        comp_info = {
                            "name": str(comp.get_name()),
                            "class": comp_class,
                        }
                        result["components"].append(comp_info)
                        if any(kw in comp_class for kw in ["Audio", "Sound", "MetaSound", "Ak"]):
                            result["audio_relevant"] = True
                            result["audio_nodes"].append({
                                "keyword": comp_class,
                                "node_title": comp_info["name"],
                                "node_class": comp_class,
                                "graph": "(component)",
                            })
        except Exception:
            pass

    # Graph names (can detect existence but not read nodes in UE 5.7)
    if bel:
        for graph_name in ["EventGraph", "UserConstructionScript"]:
            try:
                graph = bel.find_graph(bp, graph_name)
                if graph:
                    result["graphs"].append({
                        "name": str(graph.get_name()),
                        "type": "event" if graph_name == "EventGraph" else "function",
                        "nodes": [],
                        "note": "Graph nodes protected in UE 5.7 Python — use C++ plugin scan_blueprint for full node inspection",
                    })
            except Exception:
                pass

    return result



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
