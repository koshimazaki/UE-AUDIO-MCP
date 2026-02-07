# UE5 Blueprint Node Database -- Research Summary

_Generated: 2026-02-07 | Sources: 30+ | Search rounds: 6_

## Quick Answer

**No one has built a comprehensive, structured database of ALL Blueprint nodes with full pin specifications (inputs, outputs, pin types, descriptions).** This would be a first-of-its-kind dataset.

What exists today:
- Epic's own BlueprintAPI web docs (300+ categories, "early work in progress", incomplete)
- Several documentation scrapers that mirror HTML pages (no structured extraction)
- MCP servers with hardcoded support for 23 node types (tiny fraction)
- HuggingFace datasets of scraped docs (general text, not structured node specs)
- Plugins that export *specific* Blueprints to JSON (not the node registry itself)
- Nobody has enumerated FBlueprintActionDatabase to dump the full node registry

---

## What Exists Today

### 1. Epic's Official BlueprintAPI Documentation

**URL**: https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI

- 300+ top-level categories (AI, Animation, Audio, Camera, Chaos Physics, Components, Control Rig, DMX, Enhanced Input, Gameplay Abilities, Geometry Script, etc.)
- Each node gets its own page with inputs/outputs documented in HTML
- Epic themselves state: *"The Blueprint API reference is an early work in progress, and some information may be missing or out of date. It strives to reflect all available nodes, but is not guaranteed to be an exhaustive list."*
- **Not machine-readable** -- pure HTML, no JSON/XML API, no download option
- Total node count is undocumented; community estimates suggest 15,000-25,000+ nodes depending on enabled plugins

### 2. Documentation Scrapers (HTML mirrors, not structured data)

| Project | What It Does | Node Data? |
|---------|-------------|------------|
| [UE4DocScraper](https://github.com/Olliebrown/UE4DocScraper) | HTTrack-based mirror of UE4 docs including BlueprintAPI | HTML only, no structured extraction |
| [UnrealGPT](https://github.com/416rehman/UnrealGPT) | BeautifulSoup scrape of 1,700+ UE5.1 pages into FAISS | Text chunks for RAG, no node specs |
| [unreal-engine-docset](https://github.com/KelSolaar/unreal-engine-docset) | Dash docsets from Epic's .tgz docs (C++ API + Blueprint API) | SQLite index for search, but just doc page titles/types, not pin-level data |

None of these extract structured node metadata (pin names, types, directions, defaults).

### 3. MCP Servers (Hardcoded node support, tiny coverage)

| Project | Blueprint Node Coverage |
|---------|------------------------|
| [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) | 23 hardcoded node types (Branch, Switch, VariableGet, etc.) |
| [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) | Blueprint analysis tool (reads existing graphs), no node registry |
| [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) | Blueprint manipulation, no comprehensive node database |
| [CreateLex AI](https://createlex.com) | 56+ tools, "understands Blueprint system deeply" -- commercial, closed |
| [ayeletstudioindia/unreal-analyzer-mcp](https://github.com/ayeletstudioindia/unreal-analyzer-mcp) | C++ source code analysis (tree-sitter), no Blueprint node registry |

**Key gap**: Every MCP server either hardcodes a tiny subset of node types or relies on the running UE Editor to look up nodes dynamically. None ship a static database.

### 4. HuggingFace / ML Datasets

| Dataset | Content | Blueprint Nodes? |
|---------|---------|-----------------|
| [AdamCodd/Unreal-engine-5.5](https://huggingface.co/datasets/AdamCodd/Unreal-engine-5.5) | 413K files from UE docs, Q&A format | General docs, not structured node specs |
| [AdamCodd/unreal-engine-5-raw](https://huggingface.co/datasets/AdamCodd/unreal-engine-5-raw) | Raw scraped docs up to UE 5.3 | Text, no structured extraction |
| [blueprintninja/Unreal-Blueprint-Assistant](https://huggingface.co/blueprintninja/Unreal-Blueprint-Assistant) | T5 model for Blueprint Q&A | Custom Q&A pairs, not node database |

None contain structured node-level data with pin types.

### 5. Blueprint Export Plugins (Export *specific* graphs, not the registry)

| Plugin | What It Does | Useful For Us? |
|--------|-------------|----------------|
| [Blueprint Exporter](https://www.fab.com/listings/05dd8c47-4ca5-4f14-b139-5073b0007074) (Fab) | Exports execution flow of a specific Blueprint to .txt/.json | No -- exports one BP at a time, not the node catalogue |
| [BPtoJSON(toBP)](https://www.fab.com/ru/listings/a4e7348c-708a-43fe-82e8-5353d0cd2863) (Fab, free) | Compresses selected BP nodes to JSON for AI chatbots | No -- serializes existing graphs, not node definitions |
| [BP2AI Translator](https://www.fab.com/listings/6ccff7cf-f752-4b98-85d0-2c9d8a071792) (Fab) | Converts BP logic to AI-readable structured text | No -- reads flow/data, not the node type registry |
| [NodeToCode](https://github.com/protospatial/NodeToCode) | Translates BP graphs to C++ via AI | Has bespoke JSON serialization of graphs, no static node DB |

**Critical distinction**: These export *instances* of nodes used in a specific Blueprint, not the *definitions* of all available node types.

### 6. Related Reference Projects

| Project | Relevance |
|---------|-----------|
| [marcohenning/ue5-cheatsheet](https://github.com/marcohenning/ue5-cheatsheet) | Manual mapping of "important" BP nodes to C++ equivalents |
| [barsdeveloper/ueblueprint](https://github.com/barsdeveloper/ueblueprint) | Web-based Blueprint visualization library |
| [rbetik12/UE4 Blueprint Internal Structure](https://gist.github.com/rbetik12/21201e3c40201e8f8aed16c4bcf0e75e) | Gist describing internal binary format of Blueprint assets |

---

## Why It Has Not Been Done

### Technical Barriers

1. **Dynamic Registration**: Blueprint nodes are not a static list. They are registered at runtime via `FBlueprintActionDatabase` and `FBlueprintActionDatabaseRegistrar`. Each UK2Node subclass calls `GetMenuActions()` to register itself. The available nodes depend on:
   - Which engine modules are loaded
   - Which plugins are enabled
   - Which project-specific C++ classes expose UFUNCTION(BlueprintCallable)
   - Which third-party plugins are installed

2. **No Public API**: There is no Unreal Engine API that outputs "give me all registered Blueprint nodes as JSON." The `UEdGraphSchema_K2::GetGraphContextActions()` method builds the context menu dynamically but does not expose a bulk export.

3. **Scale**: With all default plugins enabled, the BlueprintAPI docs show 300+ categories. The actual node count (including all class-specific function nodes) could be 15,000-25,000+.

4. **Pin Complexity**: Many nodes have dynamic pins that change based on context (e.g., a "Cast To" node generates pins based on the target class). Static extraction cannot capture all possible pin configurations.

5. **Epic's Docs Are Incomplete**: Epic themselves acknowledge their BlueprintAPI reference is "early work in progress" -- they have not completed their own database.

### Community Interest (Unfulfilled)

The Epic Developer Community Forums show repeated requests dating back to 2014:
- ["Blueprint node master list or a way to learn each blueprint?"](https://forums.unrealengine.com/t/blueprint-node-master-list-or-a-way-to-learn-each-blueprint/292701) (2014)
- ["[request] master blueprint node list"](https://forums.unrealengine.com/t/request-master-blueprint-node-list/276168) (2014)
- ["All blueprint node functions"](https://forums.unrealengine.com/t/all-blueprint-node-functions/44438) (2015)
- ["Is there any place to learn all the blueprint nodes"](https://forums.unrealengine.com/t/is-there-any-place-to-learn-all-the-blueprint-nodes/317131)
- ["Export the entire Blueprint as AI-processable text"](https://forums.unrealengine.com/t/suggestion-export-the-entire-blueprint-as-ai-processable-text-and-import-blueprint-from-text/2655401) (2025)

None of these were fulfilled with a comprehensive dataset.

---

## How It Could Be Done

### Approach A: Scrape Epic's BlueprintAPI Documentation

- **Source**: https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI
- **Method**: Recursive crawler starting from the root, parsing each node page's HTML to extract: node name, category, description, inputs (name, type, default), outputs (name, type)
- **Pros**: No Unreal Editor required; covers Epic's documented nodes
- **Cons**: Epic warns it is incomplete; HTML structure may change; slow (100K+ pages); no pin defaults or dynamic pin info; no node class names
- **Estimated yield**: Several thousand nodes with partial pin data

### Approach B: C++ Plugin Using FBlueprintActionDatabase (Best)

- **Source**: Running Unreal Editor with target plugins enabled
- **Method**: Write a UE5 C++ Editor Utility that:
  1. Iterates `FBlueprintActionDatabase::Get().GetAllActions()`
  2. For each action, spawns a temporary node via `UBlueprintNodeSpawner`
  3. Calls `AllocateDefaultPins()` on the spawned node
  4. Serializes: node class, display name, category, tooltip, all pins (name, type/PinCategory, direction, defaults, container type)
  5. Outputs to JSON
- **Pros**: Comprehensive; captures runtime-registered nodes; gets actual pin data; includes plugin nodes
- **Cons**: Requires running UE Editor; output varies by enabled plugins; dynamic pins need special handling
- **Estimated yield**: 15,000-25,000+ nodes with complete pin specifications

### Approach C: Parse UE Source (Engine/Source/Editor/BlueprintGraph)

- **Source**: Epic's GitHub source (requires access)
- **Method**: Static analysis of UK2Node subclasses and UFUNCTION macros
- **Pros**: Does not require running the editor
- **Cons**: Cannot capture runtime registration; misses plugin nodes; extremely complex parsing
- **Estimated yield**: Core engine nodes only (subset)

### Approach D: Hybrid (Recommended)

1. **Approach B** for the definitive dataset (run in a clean UE5.5 project with all official plugins enabled)
2. **Approach A** to supplement with descriptions from Epic's docs (many nodes in the editor lack good tooltips)
3. Cross-reference and merge

---

## Conclusion

**This has NOT been done before.** A comprehensive, structured database of all UE5 Blueprint nodes with full pin specifications would be a first-of-its-kind dataset. The closest things that exist are:
- Epic's own incomplete HTML documentation (not machine-readable)
- MCP servers with 23 hardcoded node types (0.1% coverage)
- Documentation scrapers that preserve HTML without structured extraction

Building this dataset via **Approach B** (C++ plugin using FBlueprintActionDatabase) would be the most technically sound approach and would create significant value for the UE audio MCP project and the broader Unreal Engine AI tooling ecosystem.

---

## Key Sources

### Official
- [Blueprint API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI) -- Epic's official (incomplete) reference
- [FBlueprintActionDatabase API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/BlueprintGraph/FBlueprintActionDatabase) -- The internal node registry
- [UEdGraphSchema_K2 API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/BlueprintGraph/UEdGraphSchema_K2) -- Schema that builds context menus
- [UK2Node API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/BlueprintGraph/UK2Node) -- Base class for all Blueprint nodes

### Scrapers & Datasets
- [UE4DocScraper](https://github.com/Olliebrown/UE4DocScraper) -- HTTrack UE4 doc mirror
- [UnrealGPT](https://github.com/416rehman/UnrealGPT) -- 1,700+ page RAG over UE5.1 docs
- [unreal-engine-docset](https://github.com/KelSolaar/unreal-engine-docset) -- Dash docset generator
- [AdamCodd/Unreal-engine-5.5](https://huggingface.co/datasets/AdamCodd/Unreal-engine-5.5) -- 413K file HuggingFace dataset

### MCP Servers
- [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) -- 23 node types
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) -- Blueprint analysis
- [CreateLex AI](https://createlex.com) -- Commercial MCP, 56+ tools

### Blueprint Export Plugins
- [Blueprint Exporter](https://www.fab.com/listings/05dd8c47-4ca5-4f14-b139-5073b0007074) -- Execution flow export
- [BPtoJSON(toBP)](https://www.fab.com/ru/listings/a4e7348c-708a-43fe-82e8-5353d0cd2863) -- BP-to-JSON for AI
- [BP2AI Translator](https://www.fab.com/listings/6ccff7cf-f752-4b98-85d0-2c9d8a071792) -- BP-to-text for AI
- [NodeToCode](https://github.com/protospatial/NodeToCode) -- BP graph to C++ translation

### Community Knowledge
- [Improving UE API Doc Discoverability](https://thomasmansencal.substack.com/p/improving-unreal-engine-api-documentation) -- Dash docset creation from Epic's tgz
- [K2Node Introduction](https://olssondev.github.io/2023-02-13-K2Nodes/) -- How Blueprint nodes register themselves
- [Custom Blueprint Nodes Reference](https://unrealist.org/custom-blueprint-nodes/) -- Deep dive into node internals
- [A Not-So-Brief Intro to K2Nodes](https://s1t2.com/blog/brief-intro-k2nodes) -- Node spawner/registrar architecture

### Forum Threads (Unfulfilled Requests)
- [Blueprint node master list](https://forums.unrealengine.com/t/blueprint-node-master-list-or-a-way-to-learn-each-blueprint/292701) (2014)
- [All blueprint node functions](https://forums.unrealengine.com/t/all-blueprint-node-functions/44438) (2015)
- [Export Blueprint as AI text](https://forums.unrealengine.com/t/suggestion-export-the-entire-blueprint-as-ai-processable-text-and-import-blueprint-from-text/2655401) (2025)

---

_Research confidence: HIGH -- Comprehensive search across GitHub, HuggingFace, Epic Forums, Fab Marketplace, Substack, and web. No comprehensive Blueprint node database was found._
