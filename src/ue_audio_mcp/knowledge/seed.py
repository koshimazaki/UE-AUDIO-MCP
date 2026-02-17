"""Seed the knowledge database from static Python data.

Called on first run (when metasound_nodes table is empty).
Populates 14 table groups from existing knowledge modules and research data.
Schema v2 also backfills class_name, variant_group, source, mcp_note columns
and populates the node_aliases table.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ue_audio_mcp.knowledge.db import KnowledgeDB

log = logging.getLogger(__name__)


def seed_database(db: KnowledgeDB) -> dict[str, int]:
    """Populate all tables from static data. Returns counts per table."""
    counts: dict[str, int] = {}

    counts["metasound_nodes"] = _seed_metasound_nodes(db)
    counts["wwise_types"] = _seed_wwise_types(db)
    counts["waapi_functions"] = _seed_waapi_functions(db)
    counts["audio_patterns"] = _seed_audio_patterns(db)
    counts["ue_game_examples"] = _seed_game_examples(db)
    counts["blueprint_audio"] = _seed_blueprint_audio(db)
    counts["blueprint_nodes_scraped"] = _seed_blueprint_scraped(db)
    counts["builder_api_functions"] = _seed_builder_api(db)
    counts["tutorial_workflows"] = _seed_tutorial_workflows(db)
    counts["audio_console_commands"] = _seed_console_commands(db)
    counts["spatialization_methods"] = _seed_spatialization(db)
    counts["attenuation_subsystems"] = _seed_attenuation(db)
    counts["pin_mappings"] = _seed_pin_mappings(db)
    counts["node_aliases"] = _seed_node_aliases(db)
    counts["engine_plugins"] = _seed_engine_plugins(db)

    total = sum(counts.values())
    log.info("Seeded knowledge DB: %d total entries %s", total, counts)
    return counts


def _infer_variant_group(name: str) -> str:
    """Infer variant group from node name.

    'Audio Mixer (Stereo, 3)' -> 'Audio Mixer (Stereo)'
    'Trigger Any (4)'         -> 'Trigger Any'
    'Clamp (Float)'           -> 'Clamp'
    'Sine'                    -> ''  (no variant)
    """
    import re
    # Pattern: "Name (Type, N)" -> "Name (Type)"
    m = re.match(r'^(.+?)\s*\(([^,]+),\s*\d+\)$', name)
    if m:
        return f"{m.group(1)} ({m.group(2).strip()})"
    # Pattern: "Name (N)" where N is a digit -> "Name"
    m = re.match(r'^(.+?)\s*\(\d+\)$', name)
    if m:
        return m.group(1).strip()
    # Pattern: "Name (Type)" -> "Name"  (e.g. Clamp (Float) -> Clamp)
    m = re.match(r'^(.+?)\s*\([^)]+\)$', name)
    if m:
        base = m.group(1).strip()
        # Only group if there are other variants with same base
        return base
    return ""


def _seed_metasound_nodes(db: KnowledgeDB) -> int:
    from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES

    for node in METASOUND_NODES.values():
        enriched = dict(node)
        if not enriched.get("variant_group"):
            enriched["variant_group"] = _infer_variant_group(enriched["name"])
        if not enriched.get("source"):
            enriched["source"] = "catalogue"
        db.insert_node(enriched)
    return len(METASOUND_NODES)


def _seed_wwise_types(db: KnowledgeDB) -> int:
    from ue_audio_mcp.knowledge.wwise_types import (
        OBJECT_TYPES,
        COMMON_PROPERTIES,
        WWISE_TYPE_DESCRIPTIONS,
    )

    count = 0
    type_categories = {
        "Sound": "audio_object",
        "RandomSequenceContainer": "container",
        "SwitchContainer": "container",
        "BlendContainer": "container",
        "ActorMixer": "container",
        "Event": "event",
        "Action": "event",
        "Bus": "bus",
        "AuxBus": "bus",
        "WorkUnit": "structure",
        "Folder": "structure",
        "Attenuation": "shareset",
        "SoundBank": "output",
        "GameParameter": "game_sync",
        "SwitchGroup": "game_sync",
        "Switch": "game_sync",
        "StateGroup": "game_sync",
        "State": "game_sync",
        "Trigger": "game_sync",
    }
    for type_name in OBJECT_TYPES:
        cat = type_categories.get(type_name, "other")
        db.insert_wwise_type({
            "type_name": type_name,
            "category": cat,
            "description": WWISE_TYPE_DESCRIPTIONS.get(
                type_name, "Wwise {} object".format(type_name)
            ),
            "properties": list(COMMON_PROPERTIES.keys()),
        })
        count += 1
    return count


def _seed_waapi_functions(db: KnowledgeDB) -> int:
    """Seed WAAPI functions from the waapi_functions catalogue."""
    from ue_audio_mcp.knowledge.waapi_functions import WAAPI_FUNCTIONS

    for uri, func in WAAPI_FUNCTIONS.items():
        operation = uri.rsplit(".", 1)[-1]
        db.insert_waapi({
            "uri": uri,
            "namespace": func["namespace"],
            "operation": operation,
            "description": func["description"],
            "params": func.get("params", []),
            "returns": func.get("returns"),
        })
    return len(WAAPI_FUNCTIONS)


def _seed_audio_patterns(db: KnowledgeDB) -> int:
    """Seed the 6 game audio patterns."""
    patterns = [
        {
            "name": "gunshot",
            "pattern_type": "weapon",
            "description": "Non-repetitive weapon fire with layered components and pitch randomization",
            "complexity": 3,
            "key_nodes": ["Random Get", "Wave Player (Mono)", "ADSR Envelope (Audio)", "Stereo Mixer", "Random Float"],
        },
        {
            "name": "footsteps",
            "pattern_type": "movement",
            "description": "Surface-aware randomized footstep audio with per-surface filtering",
            "complexity": 3,
            "key_nodes": ["Trigger Route", "Array Random Get", "Wave Player (Mono)", "AD Envelope (Audio)", "One-Pole Low Pass Filter"],
        },
        {
            "name": "ambient",
            "pattern_type": "environment",
            "description": "Looping layered environmental audio with natural variation",
            "complexity": 4,
            "key_nodes": ["Wave Player (Stereo)", "Trigger Repeat", "Random Get", "Stereo Panner", "LFO"],
        },
        {
            "name": "spatial",
            "pattern_type": "spatialization",
            "description": "3D positioned audio with binaural rendering",
            "complexity": 2,
            "key_nodes": ["ITD Panner", "Stereo Panner", "Mid-Side Encode/Decode"],
        },
        {
            "name": "ui_sound",
            "pattern_type": "interface",
            "description": "Non-spatial UI feedback sounds with procedural synthesis option",
            "complexity": 2,
            "key_nodes": ["Sine", "AD Envelope (Audio)", "Trigger Route", "Wave Player (Mono)"],
        },
        {
            "name": "weather_states",
            "pattern_type": "state_switch",
            "description": "Game state driven audio transitions between weather profiles",
            "complexity": 4,
            "key_nodes": ["Trigger Route", "Crossfade", "InterpTo", "Dynamic Filter", "Wave Player (Stereo)"],
        },
    ]
    for p in patterns:
        db.insert_pattern(p)
    return len(patterns)


def _seed_game_examples(db: KnowledgeDB) -> int:
    """Seed UE game reference implementations."""
    examples = [
        {
            "name": "lyra_whizby",
            "game": "Lyra",
            "system_type": "weapon",
            "description": "Bullet flyby with incoming/receding phases and reflection system",
            "details": {"patch": "lib_Whizby", "features": ["8-tap delay", "frequency clamping", "convolution reverb"]},
        },
        {
            "name": "lyra_dovetail",
            "game": "Lyra",
            "system_type": "transition",
            "description": "Blends previous audio with new results using stereo balance",
            "details": {"patch": "lib_DovetailClip"},
        },
        {
            "name": "lyra_ambient",
            "game": "Lyra",
            "system_type": "ambient",
            "description": "Randomized ambient sounds with initial delays",
            "details": {"patch": "mx_PlayAmbientElement", "features": ["random delays", "environmental variation"]},
        },
        {
            "name": "lyra_music",
            "game": "Lyra",
            "system_type": "music",
            "description": "5-layer vertical music remixing with intensity tracking",
            "details": {"patch": "mx_Stingers", "layers": ["bass", "percussion-deep", "percussion-light", "pad", "lead"]},
        },
        {
            "name": "lyra_submix",
            "game": "Lyra",
            "system_type": "routing",
            "description": "Submix architecture: Master > UI/SFX/Music/Voice/Reverb",
            "details": {"buses": ["UISubmix", "SFXSubmix", "MusicSubmix", "VoiceSubmix", "ReverbSubmix"]},
        },
    ]
    for ex in examples:
        db.insert_example(ex)
    return len(examples)


def _seed_blueprint_audio(db: KnowledgeDB) -> int:
    """Seed Blueprint audio functions from the blueprint_audio catalogue."""
    from ue_audio_mcp.knowledge.blueprint_audio import BLUEPRINT_AUDIO_FUNCTIONS

    # Source uses 'category' for class name (GameplayStatics, AudioComponent, etc.)
    # Map to UE5 class prefixes for the class_name DB column
    _CLASS_MAP = {
        "GameplayStatics": "UGameplayStatics",
        "AudioComponent": "UAudioComponent",
        "AudioVolume": "AAudioVolume",
        "Quartz": "UQuartzSubsystem",
    }
    for name, func in BLUEPRINT_AUDIO_FUNCTIONS.items():
        source_cat = func["category"]
        db.insert_blueprint_audio({
            "name": name,
            "class_name": _CLASS_MAP.get(source_cat, source_cat),
            "category": source_cat.lower(),
            "description": func["description"],
            "params": func.get("params", []),
            "returns": func.get("returns"),
            "tags": func.get("tags", []),
        })
    return len(BLUEPRINT_AUDIO_FUNCTIONS)



def _seed_blueprint_scraped(db: KnowledgeDB) -> int:
    """Seed Blueprint audio functions from the verified catalogue.

    Loads curated functions from blueprint_audio_catalogue.json (55 entries)
    instead of the old 26K-node scraped bp_node_specs.json.
    """
    from ue_audio_mcp.knowledge.blueprint_scraped import load_scraped_nodes

    nodes = load_scraped_nodes()
    if not nodes:
        return 0
    rows = [
        {
            "name": name,
            "target": spec.get("target", ""),
            "category": spec.get("category", ""),
            "description": spec.get("description", ""),
            "inputs": spec.get("inputs", []),
            "outputs": spec.get("outputs", []),
            "slug": spec.get("slug", ""),
            "ue_version": spec.get("ue_version", ""),
            "path": spec.get("path", ""),
        }
        for name, spec in nodes.items()
    ]
    db.insert_blueprint_scraped_batch(rows)
    return len(rows)


def _seed_builder_api(db: KnowledgeDB) -> int:
    """Seed MetaSound Builder API functions from tutorials catalogue."""
    from ue_audio_mcp.knowledge.tutorials import BUILDER_API_FUNCTIONS

    for func in BUILDER_API_FUNCTIONS:
        db.insert_builder_api(func)
    return len(BUILDER_API_FUNCTIONS)


def _seed_tutorial_workflows(db: KnowledgeDB) -> int:
    """Seed tutorial workflow references."""
    from ue_audio_mcp.knowledge.tutorials import TUTORIAL_WORKFLOWS

    for wf in TUTORIAL_WORKFLOWS:
        db.insert_tutorial_workflow(wf)
    return len(TUTORIAL_WORKFLOWS)


def _seed_console_commands(db: KnowledgeDB) -> int:
    """Seed audio console commands from tutorials catalogue."""
    from ue_audio_mcp.knowledge.tutorials import AUDIO_CONSOLE_COMMANDS

    count = 0
    for category, cmds in AUDIO_CONSOLE_COMMANDS.items():
        for cmd in cmds:
            row = {**cmd, "category": category}
            db.insert_console_command(row)
            count += 1
    return count


def _seed_spatialization(db: KnowledgeDB) -> int:
    """Seed spatialization methods."""
    from ue_audio_mcp.knowledge.tutorials import SPATIALIZATION_METHODS

    for name, data in SPATIALIZATION_METHODS.items():
        db.insert_spatialization({
            "name": name,
            "description": data["description"],
            "details": {k: v for k, v in data.items() if k != "description"},
        })
    return len(SPATIALIZATION_METHODS)


def _seed_attenuation(db: KnowledgeDB) -> int:
    """Seed attenuation subsystems."""
    from ue_audio_mcp.knowledge.tutorials import ATTENUATION_SUBSYSTEMS

    for name, data in ATTENUATION_SUBSYSTEMS.items():
        db.insert_attenuation({
            "name": name,
            "description": data["description"],
            "params": data.get("params", []),
            "details": {k: v for k, v in data.items()
                        if k not in ("description", "params")},
        })
    return len(ATTENUATION_SUBSYSTEMS)


def _seed_pin_mappings(db: KnowledgeDB) -> int:
    """Seed cross-system pin mappings (BP <-> MetaSounds <-> Wwise)."""
    from ue_audio_mcp.knowledge.bp_ms_pin_mappings import PIN_MAPPINGS

    return db.insert_pin_mappings_batch(PIN_MAPPINGS)


def _seed_node_aliases(db: KnowledgeDB) -> int:
    """Populate node_aliases from CLASS_NAME_TO_DISPLAY + DISPLAY_TO_CLASS.

    Creates aliases of types: 'display', 'class_name', 'short'.
    """
    from ue_audio_mcp.knowledge.metasound_nodes import (
        CLASS_NAME_TO_DISPLAY,
        DISPLAY_TO_CLASS,
        METASOUND_NODES,
    )

    aliases: list[tuple[str, str, str]] = []  # (alias, canonical, alias_type)

    # 1. Display name -> canonical (identity, for completeness)
    for name in METASOUND_NODES:
        aliases.append((name, name, "display"))

    # 2. Class name -> canonical
    for class_name, display_name in CLASS_NAME_TO_DISPLAY.items():
        if display_name in METASOUND_NODES:
            aliases.append((class_name, display_name, "class_name"))

    # 3. Short names (strip parenthetical suffixes)
    import re
    seen_shorts: set[str] = set()
    for name in METASOUND_NODES:
        m = re.match(r'^(.+?)\s*\(', name)
        if m:
            short = m.group(1).strip()
            # Only add if the short name is unambiguous (maps to one node)
            # or if it's already been added as an extra alias
            if short not in METASOUND_NODES and short not in seen_shorts:
                aliases.append((short, name, "short"))
                seen_shorts.add(short)

    # 4. Extra display->class aliases
    for display_name, class_name in DISPLAY_TO_CLASS.items():
        canonical = CLASS_NAME_TO_DISPLAY.get(class_name, display_name)
        if canonical in METASOUND_NODES and display_name != canonical:
            aliases.append((display_name, canonical, "display"))

    return db.insert_node_aliases_batch(aliases)


def _seed_engine_plugins(db: KnowledgeDB) -> int:
    """Seed always-available engine plugin assets (TechAudioTools etc.).

    These are in Engine/Plugins/ and available in every project — no migration needed.
    Stored with project='__engine__' so agents can discover them.
    """
    assets = [
        # --- SFX Generator: main source ---
        {
            "name": "MSS_SFXGenerator",
            "category": "MetaSoundSource",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/MSS_SFXGenerator",
            "properties": ["7-stage procedural SFX", "oscillator→FM→AM→effects→output",
                           "UI widget with knobs and toggles"],
        },
        # --- Generators (oscillator patches) ---
        {
            "name": "MSP_SG_Generator_Sine",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_Generator_Sine",
            "properties": ["sine oscillator", "generator stage"],
        },
        {
            "name": "MSP_SG_Generator_Saw",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_Generator_Saw",
            "properties": ["sawtooth oscillator", "generator stage"],
        },
        {
            "name": "MSP_SG_Generator_Square",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_Generator_Square",
            "properties": ["square wave oscillator", "generator stage"],
        },
        {
            "name": "MSP_SG_Generator_Triangle",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_Generator_Triangle",
            "properties": ["triangle wave oscillator", "generator stage"],
        },
        {
            "name": "MSP_SG_Generator_Noise",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_Generator_Noise",
            "properties": ["noise generator", "generator stage"],
        },
        # --- FM modulation ---
        {
            "name": "MSP_SG_FM_Vibrato",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FM_Vibrato",
            "properties": ["FM vibrato", "modulation stage"],
        },
        {
            "name": "MSP_SG_FM_PitchSlide",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FM_PitchSlide",
            "properties": ["FM pitch slide", "modulation stage"],
        },
        # --- AM modulation ---
        {
            "name": "MSP_SG_AM_LFO",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_AM_LFO",
            "properties": ["AM LFO modulation", "modulation stage"],
        },
        # --- Inline effects (serial chain) ---
        {
            "name": "MSP_SG_FX_InlineFilter",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_InlineFilter",
            "properties": ["inline filter", "effect stage"],
        },
        {
            "name": "MSP_SG_FX_InlineBitcrusher",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_InlineBitcrusher",
            "properties": ["inline bitcrusher", "effect stage"],
        },
        {
            "name": "MSP_SG_FX_InlineRingmod",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_InlineRingmod",
            "properties": ["inline ring modulation", "effect stage"],
        },
        {
            "name": "MSP_SG_FX_InlineWaveShaper",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_InlineWaveShaper",
            "properties": ["inline wave shaper distortion", "effect stage"],
        },
        # --- Send effects (parallel) ---
        {
            "name": "MSP_SG_FX_SendDelay",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_SendDelay",
            "properties": ["send delay", "effect stage"],
        },
        {
            "name": "MSP_SG_FX_SendReverb",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_SendReverb",
            "properties": ["send reverb", "effect stage"],
        },
        {
            "name": "MSP_SG_FX_SendFlanger",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_FX_SendFlanger",
            "properties": ["send flanger", "effect stage"],
        },
        # --- Game SFX ---
        {
            "name": "MSP_SG_MultiStageJump",
            "category": "MetaSoundPatch",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/Patches/MSP_SG_MultiStageJump",
            "properties": ["multi-stage jump SFX", "attack→sustain→release"],
        },
        # --- Audio buses ---
        {
            "name": "AB_SFXG_Osc",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_Osc",
            "properties": ["oscillator bus"],
        },
        {
            "name": "AB_SFXG_Filter",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_Filter",
            "properties": ["filter bus"],
        },
        {
            "name": "AB_SFXG_BitCrusher",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_BitCrusher",
            "properties": ["bitcrusher bus"],
        },
        {
            "name": "AB_SFXG_RingMod",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_RingMod",
            "properties": ["ring mod bus"],
        },
        {
            "name": "AB_SFXG_WaveShaper",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_WaveShaper",
            "properties": ["wave shaper bus"],
        },
        {
            "name": "AB_SFXG_Delay",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_Delay",
            "properties": ["delay bus"],
        },
        {
            "name": "AB_SFXG_Reverb",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_Reverb",
            "properties": ["reverb bus"],
        },
        {
            "name": "AB_SFXG_Vibrato",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_Vibrato",
            "properties": ["vibrato bus"],
        },
        {
            "name": "AB_SFXG_PitchBend",
            "category": "AudioBus",
            "path": "/TechAudioToolsContent/Tools/SoundGenerator/AudioBuses/AB_SFXG_PitchBend",
            "properties": ["pitch bend bus"],
        },
    ]

    count = 0
    for asset in assets:
        db.insert_project_asset(asset, project="__engine__", source="TechAudioTools")
        count += 1
    db._conn.commit()
    return count
