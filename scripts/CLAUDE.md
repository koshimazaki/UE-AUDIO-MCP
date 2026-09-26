# Scripts

Maintenance scripts; run them from the repo root. Engine-sync scripts need the editor running with the plugin loaded. Their output goes to `exports/`, which is gitignored.

## Engine sync (editor running)

```bash
python scripts/sync_nodes_from_engine.py            # all MetaSound nodes → exports/all_metasound_nodes.json
python scripts/sync_bp_from_engine.py --audio-only  # Blueprint audio functions → exports/blueprint_functions_audio.json
python scripts/scan_project.py --full-export -o exports/project_scan.json  # BPs + MetaSound graphs + audio assets + cross-refs
```

## Pin update pipeline (engine → catalogue)

```bash
python scripts/update_catalogue_pins.py                          # dry run: show pin mismatches
python scripts/update_catalogue_pins.py --apply                  # patch the catalogue JSON with engine pins
python scripts/update_catalogue_pins.py --apply --export         # patch + regenerate the JSON catalogues
python scripts/update_catalogue_pins.py --apply --update-source  # also patch metasound_nodes.py
```

## Verification

```bash
python scripts/verify_templates.py       # class-name map, MetaSound templates, engine pins, Blueprint templates
python scripts/cross_reference.py --all  # engine exports vs catalogue (finds pin mismatches)
```

## Catalogue management

```bash
python scripts/export_catalogues.py            # regenerate the JSON catalogues from Python source
python scripts/export_catalogues.py --ms-only  # MetaSounds only
python scripts/export_catalogues.py --bp-only  # Blueprints only
```

## Other

| Script | Purpose |
|--------|---------|
| `test_plugin_live.py` | Live TCP smoke test against a running editor |
| `convert_export_to_template.py` | MetaSound graph export → template JSON |
| `parse_metasound_export.py` | Parse raw MetaSound export data |
| `verify_blueprint_nodes.py` | Blueprint node catalogue verification |
| `build_plugin.sh` | Build the plugin; see `ue5_plugin/CLAUDE.md` |
