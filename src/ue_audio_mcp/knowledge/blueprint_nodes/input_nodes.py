"""Enhanced Input nodes. Source: dev.epicgames.com Enhanced Input docs."""
from __future__ import annotations
from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ===================================================================
# ENHANCED INPUT (15 nodes) -- Category: enhanced_input
# ===================================================================

_n("AddMappingContext", "UEnhancedInputLocalPlayerSubsystem", "enhanced_input",
   "Register input mapping context for player",
   ["input", "mapping", "context"])
_n("RemoveMappingContext", "UEnhancedInputLocalPlayerSubsystem", "enhanced_input",
   "Unregister input mapping context",
   ["input", "mapping", "remove"])
_n("ClearAllMappings", "UEnhancedInputLocalPlayerSubsystem", "enhanced_input",
   "Reset all input key mappings",
   ["input", "clear", "reset"])
_n("RequestRebuildControlMappings", "UEnhancedInputLocalPlayerSubsystem", "enhanced_input",
   "Refresh input mappings after changes",
   ["input", "rebuild", "refresh"])
_n("EnableInput", "APlayerController", "enhanced_input",
   "Activate player input processing",
   ["input", "enable"])
_n("DisableInput", "APlayerController", "enhanced_input",
   "Deactivate player input processing",
   ["input", "disable"])
_n("SetInputModeGameOnly", "APlayerController", "enhanced_input",
   "Enable game input exclusively",
   ["input", "mode", "game"])
_n("SetInputModeUIOnly", "APlayerController", "enhanced_input",
   "Enable UI input exclusively",
   ["input", "mode", "ui"])
_n("SetInputModeGameAndUI", "APlayerController", "enhanced_input",
   "Enable game and UI input together",
   ["input", "mode", "game", "ui"])
_n("InjectInputForAction", "UEnhancedInputLocalPlayerSubsystem", "enhanced_input",
   "Simulate input action programmatically",
   ["input", "inject", "simulate"])
_n("GetActionValue", "UEnhancedInputComponent", "enhanced_input",
   "Get current value of input action",
   ["input", "action", "value"])
_n("BindAction", "UEnhancedInputComponent", "enhanced_input",
   "Bind callback to input action event",
   ["input", "action", "bind"])
_n("SetIgnoreLookInput", "APlayerController", "enhanced_input",
   "Disable camera/look input",
   ["input", "ignore", "look"])
_n("SetIgnoreMoveInput", "APlayerController", "enhanced_input",
   "Disable movement input",
   ["input", "ignore", "move"])
_n("IsInputKeyDown", "APlayerController", "enhanced_input",
   "Check if specific key is pressed",
   ["input", "key", "check"])
