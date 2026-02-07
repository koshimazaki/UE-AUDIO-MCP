#!/usr/bin/env python3
"""Verify blueprint_nodes entries against Epic's official Blueprint API Reference.

Two-pass approach:
  Pass 1: Scrape category index pages to discover all node names
  Pass 2: For each of OUR nodes, fetch the individual node page to get full specs
           (inputs, outputs, target class) -- e.g. /BlueprintAPI/Audio/PlaySound2D

Usage:
    python scripts/verify_blueprint_nodes.py                 # full run (scrape + verify)
    python scripts/verify_blueprint_nodes.py --cached        # reuse cached API data
    python scripts/verify_blueprint_nodes.py --report        # just print report from cache
    python scripts/verify_blueprint_nodes.py --deep          # also fetch per-node specs (slow)

Outputs:
    scripts/verify_cache.json          -- cached API scrape results (reusable)
    scripts/verify_report.txt          -- human-readable verification report
    scripts/node_specs.json            -- per-node input/output specs (from --deep)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

BASE_URL = "https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI"
CACHE_PATH = Path(__file__).parent / "verify_cache.json"
REPORT_PATH = Path(__file__).parent / "verify_report.txt"
SPECS_PATH = Path(__file__).parent / "node_specs.json"

REQUEST_DELAY = 0.5


CLASS_TO_CATEGORIES: dict[str, list[str]] = {
    "UKismetMathLibrary": [
        "Math", "Math/Float", "Math/Integer", "Math/Integer64",
        "Math/Vector", "Math/Vector2D", "Math/Vector4",
        "Math/Rotator", "Math/Transform", "Math/Quat",
        "Math/Color", "Math/DateTime", "Math/Timespan",
        "Math/Byte", "Math/Boolean",
        "Interpolation", "Random", "Noise",
    ],
    "UKismetSystemLibrary": [
        "Development", "Collision", "Timer", "Delay",
        "FileUtils", "Asserts", "Utilities", "System",
    ],
    "UKismetStringLibrary": ["String"],
    "UKismetArrayLibrary": ["Array", "Utilities"],
    "UGameplayStatics": [
        "Audio", "Game", "Gameplay", "Camera",
        "Effects", "Actor", "Spawning",
    ],
    "UAkGameplayStatics": ["Audio"],
    "UAkComponent": ["Audio"],
    "UEnhancedInputComponent": ["EnhancedInput"],
    "UEnhancedInputLocalPlayerSubsystem": ["EnhancedInput"],
    "UMaterialInstanceDynamic": ["Rendering", "Material"],
    "UDataTableFunctionLibrary": ["DataTable"],
}

EXTRA_CATEGORIES = [
    "Conversion", "FlowControl", "Macro", "Utilities",
    "Variables", "Components", "Physics", "General",
]


def fetch_page(url: str) -> str | None:
    """Fetch a URL, return text or None on failure."""
    try:
        import requests
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "UE-Audio-MCP-Verifier/1.0",
            "Accept": "text/html",
        })
        return resp.text if resp.status_code == 200 else None
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def extract_node_names(html: str) -> set[str]:
    """Extract function/node names from an API category page."""
    names: set[str] = set()
    for m in re.finditer(r'/BlueprintAPI/[^"]*?/([A-Z][A-Za-z0-9_]+)', html):
        name = m.group(1)
        if len(name) > 2:
            names.add(name)
    for m in re.finditer(r'>([A-Z][a-z]+(?:[A-Z][a-z]+)+(?:_[A-Za-z0-9]+)*)<', html):
        if len(m.group(1)) > 3:
            names.add(m.group(1))
    for m in re.finditer(r'>(K2_[A-Za-z0-9_]+)<', html):
        names.add(m.group(1))
    for m in re.finditer(r'>(Conv_[A-Za-z0-9_]+)<', html):
        names.add(m.group(1))
    return names


def _parse_table_rows(html_fragment: str) -> list[dict]:
    """Parse rows from a single table fragment into [{type, name}]."""
    pins: list[str, str] = []
    for m in re.finditer(
        r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>',
        html_fragment, re.DOTALL,
    ):
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        n = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if t and n and t.lower() != "type":  # skip header row
            pins.append({"type": t, "name": n})
    return pins


def extract_node_spec(html: str) -> dict | None:
    """Extract inputs/outputs/target from an individual node page.

    Epic node pages have separate <h2>Inputs</h2> and <h2>Outputs</h2>
    sections, each containing a table with Type | Name | Description columns.
    """
    spec: dict = {"inputs": [], "outputs": [], "target": "", "description": ""}

    # Target line: "Target is Gameplay Statics"
    for m in re.finditer(r'[Tt]arget\s+is\s+([A-Za-z0-9 ]+)', html):
        spec["target"] = m.group(1).strip()
        break

    # Split by Inputs/Outputs headings (h2 or h3)
    input_match = re.search(
        r'<h[23][^>]*>\s*Inputs?\s*</h[23]>(.*?)(?=<h[23]|$)',
        html, re.DOTALL | re.IGNORECASE,
    )
    output_match = re.search(
        r'<h[23][^>]*>\s*Outputs?\s*</h[23]>(.*?)(?=<h[23]|$)',
        html, re.DOTALL | re.IGNORECASE,
    )

    if input_match:
        spec["inputs"] = _parse_table_rows(input_match.group(1))
    if output_match:
        spec["outputs"] = _parse_table_rows(output_match.group(1))

    if spec["inputs"] or spec["outputs"] or spec["target"]:
        return spec
    return None


def scrape_categories(categories: list[str]) -> dict[str, list[str]]:
    """Scrape category index pages. Returns {cat: [names]}."""
    results: dict[str, list[str]] = {}
    total = len(categories)
    for i, cat in enumerate(categories, 1):
        url = f"{BASE_URL}/{cat}"
        print(f"  [{i:>3}/{total}] {cat:30s}", end=" ", flush=True)
        html = fetch_page(url)
        if html:
            names = extract_node_names(html)
            results[cat] = sorted(names)
            print(f"-> {len(names)} names")
        else:
            results[cat] = []
            print("-> FAILED")
        time.sleep(REQUEST_DELAY)
    return results


def scrape_node_specs(
    our_nodes: dict[str, dict],
    existing: dict | None = None,
) -> dict[str, dict | None]:
    """Pass 2: fetch individual node pages for full specs."""
    specs: dict[str, dict | None] = dict(existing or {})
    todo = [n for n in our_nodes if n not in specs]
    total = len(todo)
    found = 0

    print(f"\nPass 2: Fetching specs for {total} nodes "
          f"(skipping {len(specs)} cached)...")

    for i, name in enumerate(todo, 1):
        node = our_nodes[name]
        cls = node["class_name"]
        cats = CLASS_TO_CATEGORIES.get(cls, ["General"])

        hit = False
        for cat in cats:
            url = f"{BASE_URL}/{cat}/{name}"
            print(f"  [{i:>3}/{total}] {name:40s} {cat:20s}", end=" ", flush=True)
            html = fetch_page(url)
            if html:
                spec = extract_node_spec(html)
                if spec:
                    specs[name] = spec
                    n_in = len(spec.get("inputs", []))
                    n_out = len(spec.get("outputs", []))
                    print(f"OK ({n_in}in {n_out}out)")
                    found += 1
                    hit = True
                    break
                else:
                    print("page ok, no spec parsed")
            else:
                print("404")
            time.sleep(REQUEST_DELAY)

        if not hit:
            specs[name] = None

        if i % 50 == 0:
            with open(SPECS_PATH, "w") as f:
                json.dump(specs, f, indent=2)
            print(f"  --- checkpoint ({found} found) ---")

    return specs


def load_our_nodes() -> dict[str, dict]:
    """Load BLUEPRINT_NODES from our package."""
    src = str(Path(__file__).parent.parent / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from ue_audio_mcp.knowledge.blueprint_nodes import BLUEPRINT_NODES
    return dict(BLUEPRINT_NODES)


def find_duplicates() -> dict[str, list[str]]:
    """Find names registered in multiple .py files."""
    src = str(Path(__file__).parent.parent / "src")
    base = Path(src) / "ue_audio_mcp" / "knowledge" / "blueprint_nodes"
    name_to_files: dict[str, list[str]] = {}
    for py_file in sorted(base.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        for line in py_file.read_text().splitlines():
            s = line.strip()
            if s.startswith("_n("):
                try:
                    a = s.index('"') + 1
                    b = s.index('"', a)
                    name_to_files.setdefault(s[a:b], []).append(py_file.name)
                except ValueError:
                    pass
    return {k: v for k, v in name_to_files.items() if len(v) > 1}


def verify_nodes(our_nodes: dict[str, dict], official: set[str]) -> dict:
    """Cross-reference our nodes against official names."""
    def norm(n: str) -> str:
        return n.lower().replace("_", "").replace(" ", "")

    off_norm = {norm(n): n for n in official}
    verified, unverified, close = [], [], []

    for name in sorted(our_nodes):
        nn = norm(name)
        if nn in off_norm or name in official:
            verified.append(name)
        else:
            matches = [o for k, o in off_norm.items() if nn in k or k in nn]
            if matches:
                close.append((name, matches[:3]))
            else:
                unverified.append(name)

    return {
        "verified": verified,
        "unverified": unverified,
        "close_matches": close,
        "total_our": len(our_nodes),
        "total_official": len(official),
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "close_match_count": len(close),
    }


def generate_report(result, our_nodes, duplicates) -> str:
    """Generate the text report."""
    L = []
    L.append("=" * 70)
    L.append("BLUEPRINT NODE VERIFICATION REPORT")
    L.append("=" * 70)
    L.append(f"Our nodes:          {result['total_our']}")
    L.append(f"Official API names: {result['total_official']}")
    L.append(f"Verified:           {result['verified_count']}")
    L.append(f"Close matches:      {result['close_match_count']}")
    L.append(f"Unverified:         {result['unverified_count']}")
    L.append(f"Duplicates:         {len(duplicates)}")
    L.append("")

    if duplicates:
        L.append("-" * 70)
        L.append("DUPLICATES")
        L.append("-" * 70)
        for name, files in sorted(duplicates.items()):
            L.append(f"  {name}: {', '.join(files)}")
        L.append("")

    if result["unverified"]:
        L.append("-" * 70)
        L.append("UNVERIFIED (not found in API scrape)")
        L.append("-" * 70)
        L.append("NOTE: JS-rendered pages may cause false negatives.")
        L.append("")
        by_class: dict[str, list[str]] = {}
        for name in result["unverified"]:
            by_class.setdefault(our_nodes[name]["class_name"], []).append(name)
        for cls, names in sorted(by_class.items(), key=lambda x: -len(x[1])):
            L.append(f"  {cls} ({len(names)}):")
            for n in sorted(names):
                L.append(f"    - {n}")
            L.append("")

    if result["close_matches"]:
        L.append("-" * 70)
        L.append("CLOSE MATCHES (may need renaming)")
        L.append("-" * 70)
        for name, matches in result["close_matches"]:
            L.append(f"  {name} -> {', '.join(matches[:3])}")
        L.append("")

    L.append("-" * 70)
    L.append("BY CLASS")
    L.append("-" * 70)
    vset = set(result["verified"])
    cs: dict[str, dict] = {}
    for name, node in our_nodes.items():
        c = node["class_name"]
        s = cs.setdefault(c, {"total": 0, "ok": 0})
        s["total"] += 1
        if name in vset:
            s["ok"] += 1
    for c, s in sorted(cs.items(), key=lambda x: -x[1]["total"]):
        pct = s["ok"] / s["total"] * 100 if s["total"] else 0
        L.append(f"  {c:40s} {s['ok']:>4}/{s['total']:<4} ({pct:5.1f}%)")

    L.append("")
    L.append("=" * 70)
    return "\n".join(L)


def main():
    parser = argparse.ArgumentParser(
        description="Verify Blueprint nodes against Epic API docs")
    parser.add_argument("--cached", action="store_true",
                        help="Reuse cached category scrape")
    parser.add_argument("--report", action="store_true",
                        help="Only print report from existing cache")
    parser.add_argument("--deep", action="store_true",
                        help="Also fetch per-node specs (inputs/outputs)")
    args = parser.parse_args()

    print("Loading our Blueprint nodes...")
    our_nodes = load_our_nodes()
    print(f"  {len(our_nodes)} nodes loaded")

    print("Finding duplicates...")
    duplicates = find_duplicates()
    print(f"  {len(duplicates)} duplicates")

    all_cats: list[str] = []
    seen: set[str] = set()
    for cats in CLASS_TO_CATEGORIES.values():
        for c in cats:
            if c not in seen:
                all_cats.append(c)
                seen.add(c)
    for c in EXTRA_CATEGORIES:
        if c not in seen:
            all_cats.append(c)
            seen.add(c)

    if (args.cached or args.report) and CACHE_PATH.exists():
        print(f"Loading cache from {CACHE_PATH}...")
        with open(CACHE_PATH) as f:
            cache = json.load(f)
    elif args.report:
        print("No cache found. Run without --report first.")
        sys.exit(1)
    else:
        try:
            import requests  # noqa: F401
        except ImportError:
            print("Install: pip install requests")
            sys.exit(1)
        print(f"\nPass 1: Scraping {len(all_cats)} categories...")
        cache = scrape_categories(all_cats)
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2)

    official: set[str] = set()
    for names in cache.values():
        official.update(names)
    print(f"  {len(official)} unique official names")

    result = verify_nodes(our_nodes, official)
    report = generate_report(result, our_nodes, duplicates)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\nReport -> {REPORT_PATH}")

    if args.deep:
        try:
            import requests  # noqa: F401
        except ImportError:
            print("Install: pip install requests")
            sys.exit(1)
        existing = {}
        if SPECS_PATH.exists():
            with open(SPECS_PATH) as f:
                existing = json.load(f)
        specs = scrape_node_specs(our_nodes, existing)
        with open(SPECS_PATH, "w") as f:
            json.dump(specs, f, indent=2)
        found = sum(1 for v in specs.values() if v is not None)
        print(f"\nSpecs: {found}/{len(specs)} found -> {SPECS_PATH}")

    print()
    print(report)


if __name__ == "__main__":
    main()
