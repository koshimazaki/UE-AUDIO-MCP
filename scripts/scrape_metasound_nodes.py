#!/usr/bin/env python3
"""Scrape MetaSounds Function Nodes Reference from Epic docs.

Single-page scraper — all DSP nodes are on one page.
Uses Playwright to intercept document.json (same pattern as BP scraper).

Output:
    scripts/ms_node_specs.json — Complete MetaSounds node reference with
    category, inputs, outputs, and descriptions.

Usage:
    python scripts/scrape_metasound_nodes.py
    python scripts/scrape_metasound_nodes.py --raw  # also save raw HTML

Requirements:
    pip install playwright && playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

PAGE_URL = (
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/"
    "metasound-function-nodes-reference-guide-in-unreal-engine"
)
OUTPUT_PATH = Path(__file__).parent / "ms_node_specs.json"
RAW_HTML_PATH = Path(__file__).parent / "ms_raw_page.html"

BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
INIT_SCRIPT = "delete Object.getPrototypeOf(navigator).webdriver"

# --- Type inference from descriptions ---

TYPE_PATTERNS = [
    # Audio-rate signals
    (r"audio[- ]rate\b", "Audio"),
    (r"\baudio\s+(?:input|output|signal|buffer)", "Audio"),
    (r"\bchannel\s+output\b", "Audio"),
    (r"\bOut\s+[LRXY]", "Audio"),
    (r"\bIn\s+(?:Left|Right|Audio|L|R)\b", "Audio"),
    # Triggers
    (r"\btrigger", "Trigger"),
    (r"\bPlay\b.*\bStop\b", "Trigger"),
    (r"\bOn\s+\w+", "Trigger"),
    # Time
    (r"\bseconds\b", "Time"),
    (r"\bdelay\s+time\b", "Time"),
    (r"\bduration\b", "Time"),
    (r"\btime\b", "Time"),
    # Bool
    (r"\bwhether\b", "Bool"),
    (r"\btoggle\b", "Bool"),
    (r"\benabled?\b", "Bool"),
    (r"\blooping?\b", "Bool"),
    # Int32
    (r"\binteger\b", "Int32"),
    (r"\bcount\b", "Int32"),
    (r"\bindex\b", "Int32"),
    (r"\bnumber of\b", "Int32"),
    (r"\bID\b", "Int32"),
    # Enum
    (r"\btype\b.*\b(?:select|mode|shape)\b", "Enum"),
    (r"\bmode\b", "Enum"),
    # WaveAsset
    (r"\bSound Wave asset\b", "WaveAsset"),
    (r"\bWave(?:Table)?(?:\s+asset)?\b", "WaveAsset"),
    # String
    (r"\blabel\b", "String"),
    (r"\bfilename\b", "String"),
    (r"\bprefix\b", "String"),
]

# Pin-name-based type overrides (more reliable than description inference)
PIN_TYPE_MAP = {
    # Audio signals
    "Audio": "Audio", "In": "Audio", "Out": "Audio",
    "Audio L": "Audio", "Audio R": "Audio",
    "In Left": "Audio", "In Right": "Audio",
    "Out Left": "Audio", "Out Right": "Audio",
    "Out L": "Audio", "Out R": "Audio",
    "In Audio": "Audio", "Out Audio": "Audio",
    "In Carrier": "Audio", "In Modulator": "Audio",
    "Input Audio": "Audio", "Output Audio": "Audio",
    "In Mid": "Audio", "In Side": "Audio",
    "Out Mid": "Audio", "Out Side": "Audio",
    "Sidechain": "Audio",
    "Low Pass Filter": "Audio", "High Pass Filter": "Audio",
    "Band Pass": "Audio", "Band Stop": "Audio",
    "Mono Out": "Audio",
    # Triggers
    "Play": "Trigger", "Stop": "Trigger", "Sync": "Trigger",
    "Trigger": "Trigger", "Trigger In": "Trigger", "Trigger Out": "Trigger",
    "On Play": "Trigger", "On Finished": "Trigger",
    "On Nearly Finished": "Trigger", "On Looped": "Trigger",
    "On Cue Point": "Trigger", "On Done": "Trigger",
    "On Trigger": "Trigger", "On Reset": "Trigger",
    "On Next": "Trigger", "On Shuffle": "Trigger",
    "On Reset Seed": "Trigger", "On Sample And Hold": "Trigger",
    "Sample And Hold": "Trigger",
    "On Attack Triggered": "Trigger", "On Decay Triggered": "Trigger",
    "On Sustain Triggered": "Trigger", "On Release Triggered": "Trigger",
    "Trigger Attack": "Trigger", "Trigger Release": "Trigger",
    "RepeatOut": "Trigger",
    "Start": "Trigger", "Reset": "Trigger",
    "Next": "Trigger", "Grain Spawn": "Trigger",
    "Open": "Trigger", "Close": "Trigger", "Toggle": "Trigger",
    "Heads": "Trigger", "Tails": "Trigger",
    "True": "Trigger", "False": "Trigger",
    "Reset Seed": "Trigger", "Pause": "Trigger",
    # Time
    "Delay Time": "Time", "Attack Time": "Time", "Decay Time": "Time",
    "Release Time": "Time", "Duration": "Time", "Interp Time": "Time",
    "Grain Delay": "Time", "Grain Duration": "Time",
    "Grain Delay Range": "Time", "Grain Duration Range": "Time",
    "Start Time": "Time", "Loop Start": "Time", "Loop Duration": "Time",
    "Delay Length": "Time", "Max Delay Time": "Time",
    "Center Delay": "Time", "Period": "Time",
    "Lookahead Time": "Time", "PreDelay": "Time",
    # Bool
    "Loop": "Bool", "Enabled": "Bool", "Bi Polar": "Bool",
    "Clamped": "Bool", "Looping": "Bool", "Auto Shuffle": "Bool",
    "Phase Compensate": "Bool", "Equal Power": "Bool",
    "Start Closed": "Bool", "Auto Reset": "Bool",
    "Upwards Mode": "Bool", "Analog Mode": "Bool",
    "Limit Output": "Bool", "Peak Mode": "Bool",
    "Enabled Shared State": "Bool", "Chord Tones Only": "Bool",
    # Int32
    "No Repeats": "Int32", "Voices": "Int32",
    "Max Grain Count": "Int32", "Cue Point ID": "Int32",
    "Index": "Int32", "Start Index": "Int32", "End Index": "Int32",
    "Start Value": "Int32", "Step Size": "Int32", "Reset Count": "Int32",
    "Count": "Int32", "Seed": "Int32", "Filter Order": "Int32",
    "Layers": "Int32", "Table Index": "Int32",
    "Num": "Int32",
    # Float
    "Frequency": "Float", "Cutoff Frequency": "Float",
    "Bandwidth": "Float", "Resonance": "Float",
    "Pitch Shift": "Float", "Dry Level": "Float", "Wet Level": "Float",
    "Feedback": "Float", "Mix Level": "Float",
    "Gain": "Float", "Gain (dB)": "Float",
    "Ratio": "Float", "Threshold dB": "Float", "Knee": "Float",
    "Attack Curve": "Float", "Decay Curve": "Float", "Release Curve": "Float",
    "Sustain Level": "Float", "Crossfade Value": "Float",
    "Amount": "Float", "Bias": "Float", "OutputGain": "Float",
    "Detune": "Float", "Entropy": "Float", "Blend": "Float",
    "Pulse Width": "Float", "Width": "Float",
    "Phase Offset": "Float", "Glide": "Float",
    "Pan Amount": "Float", "Angle": "Float",
    "Distance Factor": "Float", "Head Width": "Float",
    "Spread Amount": "Float",
    "Depth": "Float", "Modulation Rate": "Float", "Modulation Depth": "Float",
    "Feedback Amount": "Float",
    "Band Stop Control": "Float",
    "Input Gain dB": "Float",
    "BPM": "Float", "Beat Multiplier": "Float",
    "Min Value": "Float", "Max Value": "Float",
    "Min": "Float", "Max": "Float",
    "Damping": "Float", "Decay": "Float", "DryWet": "Float",
    "Rate": "Float", "Rate Jitter": "Float", "Step Limit": "Float",
    "Density": "Float",
    "Probability": "Float", "Threshold": "Float",
    "Wet/Dry": "Float", "Delay Ratio": "Float",
    "Pitch Shift Range": "Float",
    "Sample Rate": "Float", "Bit Depth": "Float",
    "Q": "Float", "Range": "Float",
    "Value": "Float", "Target": "Float",
    "Seconds": "Float", "Linear Gain": "Float", "Decibels": "Float",
    "Frequency In": "Float", "Out Frequency": "Float",
    "MIDI In": "Float", "Out MIDI": "Float",
    "Loop Percent": "Float", "Playback Location": "Float",
    "Note In": "Int32", "Note Out": "Int32",
    "Root Note": "Int32",
    "X": "Float",
    "In Range A": "Float", "In Range B": "Float",
    "Out Range A": "Float", "Out Range B": "Float",
    "Out Value": "Float",
    "Normalized": "Float", "Output": "Float",
    # Audio-rate (overrides for specific modulation pins)
    "Modulation": "Audio",
    "Phase Modulator": "Audio",
    "Out Envelope": "Audio",
    "Audio Envelope": "Audio",
    "Gain Envelope": "Audio",
    "Envelope": "Float",
    # WaveAsset
    "Wave Asset": "WaveAsset", "WaveTable": "WaveAsset",
    "WaveTableBank": "WaveAsset", "Bank": "WaveAsset",
    "Audio Bus": "WaveAsset",
    # String
    "Cue Point Label": "String", "Filename Prefix": "String",
    "Label": "String", "Name": "String", "Path": "String",
    # Enum
    "Type": "Enum", "Shape": "Enum", "Envelope Mode": "Enum",
    "Panning Law": "Enum", "Interpolation": "Enum",
    "Mode": "Enum", "Delay Mode": "Enum",
    "Grain Envelope": "Enum", "FilterType": "Enum",
    "EnvelopeMode": "Enum", "AnalogMode": "Enum",
    "Division of Whole Note": "Enum",
}


def infer_type(pin_name: str, description: str, is_output: bool = False) -> str:
    """Infer pin data type from name and description."""
    # Direct name match first
    if pin_name in PIN_TYPE_MAP:
        return PIN_TYPE_MAP[pin_name]

    # Check for "Out X" pattern (channel outputs)
    if re.match(r"Out\s+[A-Z]$", pin_name) or re.match(r"Band\s+\d+", pin_name):
        return "Audio"

    # Check for "In X L/R" pattern (mixer inputs)
    if re.match(r"In\s+\d+\s+[LR]$", pin_name):
        return "Audio"

    # Check for "Crossover" pattern
    if pin_name.startswith("Crossover"):
        return "Float"

    # Array types
    if "Array" in pin_name or "array" in description.lower():
        return "Array"

    # Weights
    if pin_name == "Weights":
        return "Array"

    # Scale degrees
    if "Scale" in pin_name and "Array" not in pin_name:
        return "Array"

    # Pattern-based inference from description
    desc_lower = description.lower()
    for pattern, dtype in TYPE_PATTERNS:
        if re.search(pattern, desc_lower):
            return dtype

    # Output defaults
    if is_output and pin_name not in PIN_TYPE_MAP:
        if any(kw in desc_lower for kw in ["audio", "signal", "channel"]):
            return "Audio"

    return "Float"  # default


def parse_content_html(html: str) -> dict[str, dict]:
    """Parse the MetaSounds reference page HTML into structured node data."""
    nodes: dict[str, dict] = {}
    current_category = "Uncategorized"

    sections = re.split(r'(<h[23][^>]*>.*?</h[23]>)', html)

    current_node = None
    current_node_data = None

    for section in sections:
        # Check for category header (h2)
        h2_match = re.match(r'<h2[^>]*>(.*?)</h2>', section, re.DOTALL)
        if h2_match:
            cat_text = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
            if cat_text and cat_text not in ("Contents", ""):
                current_category = cat_text
            continue

        # Check for node header (h3)
        h3_match = re.match(r'<h3[^>]*>(.*?)</h3>', section, re.DOTALL)
        if h3_match:
            node_name = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
            if node_name:
                current_node = node_name
                current_node_data = {
                    "name": node_name,
                    "category": current_category,
                    "description": "",
                    "inputs": [],
                    "outputs": [],
                }
                nodes[node_name] = current_node_data
            continue

        # Process content between headers
        if current_node_data is None:
            continue

        # Extract description (first paragraph after node name)
        if not current_node_data["description"]:
            desc_match = re.search(r'<p>(.*?)</p>', section, re.DOTALL)
            if desc_match:
                desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                if desc and "Inputs" not in desc and "Outputs" not in desc:
                    current_node_data["description"] = desc

        # Extract input tables
        input_sections = re.finditer(
            r'(?:Inputs|Input)\s*</h4>(.*?)(?=<h[234]|$)',
            section, re.DOTALL | re.IGNORECASE,
        )
        for im in input_sections:
            pins = _parse_table(im.group(1), is_output=False)
            if pins:
                current_node_data["inputs"].extend(pins)

        # Extract output tables
        output_sections = re.finditer(
            r'(?:Outputs|Output)\s*</h4>(.*?)(?=<h[234]|$)',
            section, re.DOTALL | re.IGNORECASE,
        )
        for om in output_sections:
            pins = _parse_table(om.group(1), is_output=True)
            if pins:
                current_node_data["outputs"].extend(pins)

    return nodes


def _parse_table(html: str, is_output: bool = False) -> list[dict]:
    """Parse an HTML table into pin specs."""
    pins = []

    for row in re.finditer(
        r'<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>',
        html, re.DOTALL,
    ):
        name = re.sub(r'<[^>]+>', '', row.group(1)).strip()
        desc = re.sub(r'<[^>]+>', '', row.group(2)).strip()

        if not name or name.lower() in ("input", "output", "name", "type"):
            continue

        pin_type = infer_type(name, desc, is_output=is_output)
        pin: dict = {"name": name, "type": pin_type}
        if desc:
            pin["description"] = desc
        pins.append(pin)

    return pins


def parse_document_json(data: dict) -> str:
    """Extract content HTML from Epic's document.json response."""
    if isinstance(data, dict):
        for key in ("content_html", "contentHtml", "body", "content"):
            if key in data:
                return data[key]
        for val in data.values():
            if isinstance(val, str) and "<h2" in val and len(val) > 1000:
                return val
            if isinstance(val, dict):
                result = parse_document_json(val)
                if result:
                    return result
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        result = parse_document_json(item)
                        if result:
                            return result
    return ""


def post_process(nodes: dict[str, dict]) -> dict[str, dict]:
    """Clean up and enhance parsed nodes."""
    for name, node in list(nodes.items()):
        if not node["inputs"] and not node["outputs"] and not node["description"]:
            del nodes[name]
            continue

        seen_inputs = set()
        unique_inputs = []
        for pin in node["inputs"]:
            if pin["name"] not in seen_inputs:
                seen_inputs.add(pin["name"])
                unique_inputs.append(pin)
        node["inputs"] = unique_inputs

        seen_outputs = set()
        unique_outputs = []
        for pin in node["outputs"]:
            if pin["name"] not in seen_outputs:
                seen_outputs.add(pin["name"])
                unique_outputs.append(pin)
        node["outputs"] = unique_outputs

    return nodes


def print_summary(nodes: dict[str, dict]) -> None:
    """Print a summary of scraped nodes."""
    categories: dict[str, list[str]] = {}
    for name, node in sorted(nodes.items()):
        cat = node["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)

    total_pins = sum(
        len(n["inputs"]) + len(n["outputs"]) for n in nodes.values()
    )

    print(f"\n{'=' * 60}")
    print(f"MetaSounds Node Reference: {len(nodes)} nodes, {total_pins} pins")
    print(f"{'=' * 60}")

    for cat, cat_nodes in sorted(categories.items()):
        print(f"\n{cat} ({len(cat_nodes)} nodes):")
        for n in cat_nodes:
            node = nodes[n]
            in_count = len(node["inputs"])
            out_count = len(node["outputs"])
            print(f"  {n}: {in_count} in / {out_count} out")

    # Show oscillator pins specifically
    print(f"\n{'=' * 60}")
    print("Key FM Synthesis Pins:")
    for osc in ["Sine", "Saw", "Square", "Triangle"]:
        if osc in nodes:
            n = nodes[osc]
            print(f"\n  {osc}:")
            for pin in n["inputs"]:
                print(f"    IN  {pin['name']} ({pin['type']})")
            for pin in n["outputs"]:
                print(f"    OUT {pin['name']} ({pin['type']})")


async def fetch_page() -> str | None:
    """Fetch the MetaSounds reference page and return HTML content."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: pip install playwright && playwright install chromium")
        sys.exit(1)

    print(f"Fetching {PAGE_URL}")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True, args=BROWSER_ARGS,
        )
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        await page.add_init_script(INIT_SCRIPT)

        captured: dict = {}

        async def on_resp(response):
            if "document.json" in response.url and response.status == 200:
                try:
                    captured["data"] = await response.json()
                except Exception:
                    pass

        page.on("response", on_resp)

        try:
            await page.goto(PAGE_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Page load warning: {e}")

        if "data" in captured:
            html = parse_document_json(captured["data"])
            if html:
                print(f"Got {len(html):,} chars from document.json")
                await browser.close()
                return html

        print("document.json not captured, trying page.content()...")
        html = await page.content()
        await browser.close()
        return html

    return None


async def main():
    parser = argparse.ArgumentParser(description="Scrape MetaSounds node reference")
    parser.add_argument("--raw", action="store_true", help="Save raw HTML too")
    args = parser.parse_args()

    html = await fetch_page()
    if not html:
        print("ERROR: Could not fetch page content")
        sys.exit(1)

    if args.raw:
        RAW_HTML_PATH.write_text(html, encoding="utf-8")
        print(f"Raw HTML saved to {RAW_HTML_PATH} ({len(html):,} chars)")

    nodes = parse_content_html(html)
    nodes = post_process(nodes)

    if not nodes:
        print("ERROR: No nodes parsed! The page structure may have changed.")
        print("Try --raw to save the HTML for inspection.")
        sys.exit(1)

    OUTPUT_PATH.write_text(
        json.dumps(nodes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved {len(nodes)} nodes to {OUTPUT_PATH}")
    print_summary(nodes)


if __name__ == "__main__":
    asyncio.run(main())
