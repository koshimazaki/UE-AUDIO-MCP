#!/usr/bin/env bash
# Build UEAudioMCP plugin from git source and deploy to UE project.
#
# Usage:
#   ./scripts/build_plugin.sh              # sync source + build
#   ./scripts/build_plugin.sh --clean      # sync + clean intermediates + build
#   ./scripts/build_plugin.sh --sync-only  # just copy source, no build
#   ./scripts/build_plugin.sh --build-only # just build, no source copy
#
set -euo pipefail

# --- Paths ---
ENGINE_ROOT="/Volumes/Koshi_T7/UN5.3/UE_5.7"
PROJECT_DIR="/Users/radek/Documents/Unreal Projects/UEIntroProject"
PROJECT_FILE="${PROJECT_DIR}/UEIntroProject.uproject"

GIT_PLUGIN_DIR="/Users/radek/Documents/GIthub/UE5-WWISE/ue5_plugin/UEAudioMCP"
DEPLOY_PLUGIN_DIR="${PROJECT_DIR}/Plugins/UEAudioMCP"

UBT="${ENGINE_ROOT}/Engine/Build/BatchFiles/Mac/Build.sh"

# --- Parse args ---
SYNC=true
BUILD=true
CLEAN=false
for arg in "$@"; do
    case "$arg" in
        --sync-only)  BUILD=false ;;
        --build-only) SYNC=false ;;
        --clean)      CLEAN=true ;;
        --help|-h)
            echo "Usage: $0 [--sync-only|--build-only]"
            echo "  (default) sync source + build"
            echo "  --sync-only   copy source files only"
            echo "  --build-only  compile only (no source copy)"
            exit 0 ;;
    esac
done

# --- Verify paths ---
if [ ! -d "$ENGINE_ROOT" ]; then
    echo "ERROR: Engine not found at $ENGINE_ROOT"
    echo "  Is the external drive mounted?"
    exit 1
fi
if [ ! -f "$PROJECT_FILE" ]; then
    echo "ERROR: Project not found at $PROJECT_FILE"
    exit 1
fi
if [ ! -d "$GIT_PLUGIN_DIR" ]; then
    echo "ERROR: Plugin source not found at $GIT_PLUGIN_DIR"
    exit 1
fi

# --- Sync source ---
if $SYNC; then
    echo "=== Syncing source: git -> project ==="

    # Copy Source/ directory
    rsync -av --delete \
        "${GIT_PLUGIN_DIR}/Source/" \
        "${DEPLOY_PLUGIN_DIR}/Source/"

    # Copy .uplugin
    cp "${GIT_PLUGIN_DIR}/UEAudioMCP.uplugin" \
       "${DEPLOY_PLUGIN_DIR}/UEAudioMCP.uplugin"

    echo "Source synced."
    echo ""
fi

# --- Clean intermediates ---
if $CLEAN; then
    echo "=== Cleaning plugin intermediates ==="
    rm -rf "${DEPLOY_PLUGIN_DIR}/Intermediate"
    echo "Cleaned."
    echo ""
fi

# --- Build ---
if $BUILD; then
    echo "=== Building UnrealEditor (Mac Development) ==="
    echo "  Engine:  $ENGINE_ROOT"
    echo "  Project: $PROJECT_FILE"
    echo ""

    # Build project-specific editor target (NOT generic UnrealEditor).
    # UE 5.7 UBT has action graph conflicts when building generic UnrealEditor
    # with a project — both UnrealEditor and ProjectEditor targets compile
    # plugin modules to the same output dir with different PCH prerequisites.
    PROJECT_NAME=$(basename "$PROJECT_FILE" .uproject)
    "$UBT" "${PROJECT_NAME}Editor" Mac Development \
        -Project="$PROJECT_FILE" \
        2>&1 | tee /tmp/ue_plugin_build.log

    BUILD_EXIT=$?

    echo ""
    if [ $BUILD_EXIT -eq 0 ]; then
        echo "=== BUILD SUCCEEDED ==="
        # Show the dylibs
        echo "Binaries:"
        ls -lh "${DEPLOY_PLUGIN_DIR}/Binaries/Mac/"*.dylib 2>/dev/null || echo "  (no dylibs found)"
    else
        echo "=== BUILD FAILED (exit $BUILD_EXIT) ==="
        echo "Full log: /tmp/ue_plugin_build.log"
        exit $BUILD_EXIT
    fi
fi

echo ""
echo "Done. Restart UE5 Editor to load the updated plugin."
