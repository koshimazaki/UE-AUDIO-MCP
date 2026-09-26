# UE5 plugin (C++)

Applies to everything under `ue5_plugin/`. The plugin needs Unreal Engine 5.7.2+ and builds with Clang (macOS) and MSVC (Windows), so keep code portable. Follow Unreal's C++ coding standard (type prefixes, `UCLASS`/`UPROPERTY` reflection).

## Layout

- `UEAudioMCP/UEAudioMCP.uplugin` has two modules:
  - `UEAudioMCP` (Editor, `PostEngineInit`) — the TCP server on 127.0.0.1:9877 and its commands
  - `SIDMetaSoundNodes` (Runtime, `Default`) — five SID chip MetaSound nodes; it ships in games
- `Source/UEAudioMCP/Private/UEAudioMCPModule.cpp` — `RegisterCommand` calls, the authoritative command list
- `Source/UEAudioMCP/Private/Commands/` — one `Execute()` per command, reading params with `Params->TryGet*Field`
- `Source/UEAudioMCP/Private/AudioMCPBuilderManager.cpp` — MetaSound builder state, `__graph__` pins, node-type resolution
- `Source/ThirdParty/ReSID/` — vendored reSID emulator; keep changes to it minimal

To add a command, follow the `ue5-plugin-dev` skill; the full command reference is in the `ue5-audio-mcp` skill.

## Building

```bash
./scripts/build_plugin.sh              # sync source + compile
./scripts/build_plugin.sh --clean      # force recompile (removes Intermediate/)
./scripts/build_plugin.sh --sync-only  # sync only; UE recompiles on open
./scripts/build_plugin.sh --build-only # compile only, skip the source sync
```

Set `UE_ENGINE_ROOT` and `UE_PROJECT_DIR`; the script's defaults are the maintainer's machine. Close the editor first (dylibs are locked). Use `--clean` for "Action graph is invalid" or a stale PCH.

## Breaking changes by UE version

Check these first when an engine upgrade breaks the build:

- **`Document.RootGraph.Interface`** → `Document.RootGraph.GetDefaultInterface()` (inputs/outputs access)
- **`ClassInput.Default`** (removed) → `ClassInput.FindConstDefault(FGuid())` returns `FMetasoundFrontendLiteral*` (null if no default). `FGuid()` = default page.
- **`FNodeFacade`** → `TNodeFacade<Op>` (templated in 5.7)
- **`GetOrConstructDataReadReference`** → `GetOrCreateDefaultDataReadReference` (deprecated 5.6)
- **`bEnableUndefinedIdentifierWarnings`** → `CppCompileWarningSettings.UndefinedIdentifierWarningLevel = WarningLevel.Off` (deprecated 5.5; moved under `CppCompileWarningSettings` in 5.6, old path emits CS0618)
- **`__attribute__((optimize))`** — Clang doesn't support it, wrap with `#if !defined(__clang__)`
- **`__attribute__((always_inline))`** — MSVC has no `__attribute__`; use `RESID_FORCE_INLINE` from `siddefs.h`
- **MetaSound node registration (5.7+)** — nodes and enums register only via a per-module list: `METASOUND_PLUGIN`/`METASOUND_MODULE` private definitions in Build.cs, `METASOUND_IMPLEMENT_MODULE_REGISTRATION_LIST` in the module .cpp, `METASOUND_REGISTER_ITEMS_IN_MODULE`/`METASOUND_UNREGISTER_ITEMS_IN_MODULE` in Startup/Shutdown. Without them the module compiles and loads, but the nodes silently never appear.
- **`SIDMetaSoundNodes` stays non-unity** (`bUseUnity = false`) — node .cpp files define `RESID_HEADER_ONLY`; in a unity blob that stops `ReSIDLib.cpp` compiling the reSID implementations (unresolved externals, clean checkout only)
