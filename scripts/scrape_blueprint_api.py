#!/usr/bin/env python3
"""Scrape Epic Blueprint API using Playwright (fresh context per request).

Strategy: Epic's SPA blocks document.json after 1st request per session.
Fix: create a fresh browser context for each request.

Recursive discovery: each category page is checked for subcategories.
A page with ONLY links to deeper paths (no Input/Output tables) is a category.
A page with Input/Output tables is a leaf node.

Usage:
    python scripts/scrape_blueprint_api.py                       # full run
    python scripts/scrape_blueprint_api.py --phase2-only         # skip discovery
    python scripts/scrape_blueprint_api.py --our-nodes-only      # only our DB nodes
    python scripts/scrape_blueprint_api.py --categories Audio,Math
    python scripts/scrape_blueprint_api.py --limit 50
    python scripts/scrape_blueprint_api.py --workers 3

Outputs:
    scripts/bp_categories.json   -- path -> [child_names] (recursive)
    scripts/bp_node_specs.json   -- node_name -> {inputs, outputs, target, ...}

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

BASE_URL = "https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI"
CATEGORIES_PATH = Path(__file__).parent / "bp_categories.json"
SPECS_PATH = Path(__file__).parent / "bp_node_specs.json"
ROOT_PATHS_PATH = Path(__file__).parent / "bp_all_paths.json"
LEAF_NODES_PATH = Path(__file__).parent / "bp_leaf_nodes.json"

BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
INIT_SCRIPT = "delete Object.getPrototypeOf(navigator).webdriver"


def parse_node_spec_from_html(html: str) -> dict | None:
    """Parse inputs/outputs/target from content_html."""
    spec: dict = {
        "inputs": [], "outputs": [], "target": "",
        "description": "", "category": "",
    }

    m = re.search(r'[Tt]arget\s+is\s+([A-Za-z0-9 ]+)', html)
    if m:
        spec["target"] = m.group(1).strip()

    m = re.search(r'</a>\s*</p>\s*<p>(.*?)</p>', html, re.DOTALL)
    if m:
        desc = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if desc and "Target is" not in desc:
            spec["description"] = desc

    cats = re.findall(r'BlueprintAPI/([^"<]+)</a>', html)
    if cats:
        spec["category"] = cats[-1].strip()

    def parse_section(section_html: str) -> list[dict]:
        pins = []
        for row in re.finditer(
            r'<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>',
            section_html, re.DOTALL,
        ):
            pt = re.sub(r'<[^>]+>', '', row.group(1)).strip()
            pn = re.sub(r'<[^>]+>', '', row.group(2)).strip()
            pd = re.sub(r'<[^>]+>', '', row.group(3)).strip()
            if pt and pn and pt.lower() != "type":
                pin = {"type": pt, "name": pn}
                if pd and pd != "\xa0":
                    pin["description"] = pd
                pins.append(pin)
        return pins

    im = re.search(r'<h2>\s*Inputs?\s*</h2>(.*?)(?=<h2>|$)', html, re.DOTALL | re.IGNORECASE)
    om = re.search(r'<h2>\s*Outputs?\s*</h2>(.*?)(?=<h2>|$)', html, re.DOTALL | re.IGNORECASE)
    if im:
        spec["inputs"] = parse_section(im.group(1))
    if om:
        spec["outputs"] = parse_section(om.group(1))

    if spec["inputs"] or spec["outputs"] or spec["target"]:
        return spec
    return None


def is_node_page(html: str) -> bool:
    """Check if HTML content has Input/Output tables (= leaf node, not category)."""
    return bool(re.search(r'<h2>\s*(?:Inputs?|Outputs?)\s*</h2>', html, re.IGNORECASE))


def extract_children(html: str, parent_path: str) -> list[str]:
    """Extract child link names from a page."""
    pattern = rf'BlueprintAPI/{re.escape(parent_path)}/([^"/?]+)'
    return sorted(set(re.findall(pattern, html)))


async def fetch_one(browser, url_path: str) -> dict | None:
    """Fetch one page using a fresh browser context."""
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()
    await page.add_init_script(INIT_SCRIPT)
    captured = {}

    async def on_resp(response):
        if "document.json" in response.url and response.status == 200:
            try:
                captured["data"] = await response.json()
            except Exception:
                pass

    page.on("response", on_resp)
    try:
        full_url = f"{BASE_URL}/{url_path}" if url_path else BASE_URL
        await page.goto(full_url, wait_until="networkidle", timeout=20000)
        await asyncio.sleep(0.3)
    except Exception:
        pass
    finally:
        await context.close()
    return captured.get("data")


async def fetch_batch(browser, paths: list[str], workers: int) -> dict[str, dict]:
    """Fetch multiple paths with controlled concurrency."""
    sem = asyncio.Semaphore(workers)
    results: dict[str, dict] = {}

    async def go(path: str):
        async with sem:
            data = await fetch_one(browser, path)
            if data:
                results[path] = data
            await asyncio.sleep(0.3)

    await asyncio.gather(*(go(p) for p in paths))
    return results


async def run_scraper(args):
    from playwright.async_api import async_playwright

    workers = args.workers or 3
    batch_size = workers * 2

    # Load caches
    categories: dict[str, list[str]] = {}
    if CATEGORIES_PATH.exists():
        with open(CATEGORIES_PATH) as f:
            categories = json.load(f)

    specs: dict[str, dict] = {}
    if SPECS_PATH.exists():
        with open(SPECS_PATH) as f:
            specs = json.load(f)

    leaf_nodes: list[str] = []  # full paths to leaf nodes
    if LEAF_NODES_PATH.exists():
        with open(LEAF_NODES_PATH) as f:
            leaf_nodes = json.load(f)

    root_cats: list[str] = []
    if ROOT_PATHS_PATH.exists():
        with open(ROOT_PATHS_PATH) as f:
            root_cats = json.load(f)

    if args.categories:
        initial_cats = args.categories.split(",")
    elif root_cats:
        initial_cats = root_cats
    else:
        initial_cats = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)

        # Phase 0: Get root categories if needed
        if not initial_cats and not args.phase2_only:
            print("Phase 0: Getting root categories...")
            data = await fetch_one(browser, "")
            if data and "blocks" in data:
                html = data["blocks"][0].get("content_html", "")
                initial_cats = sorted(set(re.findall(r'BlueprintAPI/([^"/?]+)', html)))
                with open(ROOT_PATHS_PATH, "w") as f:
                    json.dump(initial_cats, f, indent=2)
                print(f"  Found {len(initial_cats)} root categories")
            else:
                print("  FAILED"); await browser.close(); return

        # Phase 1: Recursive category discovery
        if not args.phase2_only:
            # BFS queue: paths to explore
            queue = [c for c in initial_cats if c not in categories]
            explored = set(categories.keys())
            leaf_set = set(leaf_nodes)

            print(f"\nPhase 1: Recursive discovery ({len(queue)} to explore, "
                  f"{len(explored)} cached, {workers} workers)...")

            depth = 0
            while queue:
                depth += 1
                total_in_level = len(queue)
                print(f"\n  --- Depth {depth}: {total_in_level} paths to explore ---")

                new_queue = []
                for batch_start in range(0, len(queue), batch_size):
                    batch = queue[batch_start : batch_start + batch_size]
                    results = await fetch_batch(browser, batch, workers)

                    for path in batch:
                        idx = batch_start + batch.index(path) + 1
                        if path in results:
                            data = results[path]
                            html = data.get("blocks", [{}])[0].get("content_html", "")
                            children = extract_children(html, path)

                            if is_node_page(html):
                                # This is a leaf node, not a category
                                leaf_set.add(path)
                                print(f"  [{idx:>4}/{total_in_level}] NODE {path}")
                            elif children:
                                # This is a category with children
                                categories[path] = children
                                explored.add(path)
                                # Queue children for exploration
                                for child in children:
                                    child_path = f"{path}/{child}"
                                    if child_path not in explored and child_path not in leaf_set:
                                        new_queue.append(child_path)
                                print(f"  [{idx:>4}/{total_in_level}] CAT  {path:50s} -> {len(children)} children")
                            else:
                                # Empty or failed
                                categories[path] = []
                                print(f"  [{idx:>4}/{total_in_level}] EMPTY {path}")
                        else:
                            print(f"  [{idx:>4}/{total_in_level}] FAIL {path}")

                    # Checkpoint
                    with open(CATEGORIES_PATH, "w") as f:
                        json.dump(categories, f, indent=2)
                    leaf_nodes = sorted(leaf_set)
                    with open(LEAF_NODES_PATH, "w") as f:
                        json.dump(leaf_nodes, f, indent=2)

                queue = new_queue
                if depth > 5:
                    print("  Max depth reached, stopping recursion")
                    break

            # Collect all leaf node paths
            # Leaf = child of a category that is not itself a category
            for cat_path, children in categories.items():
                for child in children:
                    full = f"{cat_path}/{child}"
                    if full not in categories:
                        leaf_set.add(full)

            leaf_nodes = sorted(leaf_set)
            with open(LEAF_NODES_PATH, "w") as f:
                json.dump(leaf_nodes, f, indent=2)

            print(f"\nPhase 1 complete:")
            print(f"  Categories: {len(categories)}")
            print(f"  Leaf nodes: {len(leaf_nodes)}")

        # Phase 2: Fetch node specs
        if args.our_nodes_only:
            src = str(Path(__file__).parent.parent / "src")
            if src not in sys.path:
                sys.path.insert(0, src)
            from ue_audio_mcp.knowledge.blueprint_nodes import BLUEPRINT_NODES

            name_to_path = {}
            for lp in leaf_nodes:
                name = lp.rsplit("/", 1)[-1]
                name_to_path[name] = lp

            target = [name_to_path[n] for n in BLUEPRINT_NODES
                      if n in name_to_path and n not in specs]
            print(f"\nPhase 2: Fetching {len(target)} of our nodes...")
        else:
            target = [lp for lp in leaf_nodes if lp.rsplit("/", 1)[-1] not in specs]
            print(f"\nPhase 2: Fetching {len(target)} nodes ({len(specs)} cached)...")

        if args.limit:
            target = target[:args.limit]
            print(f"  (limited to {args.limit})")

        found = 0
        total_t = len(target)
        for batch_start in range(0, total_t, batch_size):
            batch = target[batch_start : batch_start + batch_size]
            results = await fetch_batch(browser, batch, workers)

            for node_path in batch:
                node_name = node_path.rsplit("/", 1)[-1]
                idx = batch_start + batch.index(node_path) + 1

                if node_path in results:
                    data = results[node_path]
                    html = data.get("blocks", [{}])[0].get("content_html", "")
                    spec = parse_node_spec_from_html(html)
                    if spec:
                        spec["slug"] = data.get("slug", "")
                        spec["ue_version"] = data.get("applications", [{}])[0].get("version", "")
                        spec["path"] = node_path
                        specs[node_name] = spec
                        found += 1
                        ni = len(spec["inputs"])
                        no = len(spec["outputs"])
                        print(f"  [{idx:>4}/{total_t}] OK  {node_name:40s} ({ni}in {no}out)")
                    else:
                        print(f"  [{idx:>4}/{total_t}] --  {node_name:40s} (no spec)")
                else:
                    print(f"  [{idx:>4}/{total_t}] FAIL {node_name}")

            with open(SPECS_PATH, "w") as f:
                json.dump(specs, f, indent=2)

        await browser.close()

    print(f"\n{'='*60}")
    print(f"Categories:  {len(categories)}")
    print(f"Leaf nodes:  {len(leaf_nodes)}")
    print(f"Specs:       {len(specs)}")
    print(f"{'='*60}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase2-only", action="store_true")
    ap.add_argument("--our-nodes-only", action="store_true")
    ap.add_argument("--categories", type=str)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    asyncio.run(run_scraper(args))


if __name__ == "__main__":
    main()
