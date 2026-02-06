"""Flow control, timer, comparison, and conversion nodes. Source: UK2Node_* classes, UKismetSystemLibrary, UKismetMathLibrary."""
from __future__ import annotations

from ue_audio_mcp.knowledge.blueprint_nodes import _n

# --- FLOW CONTROL (39 nodes) ---
# Source: UK2Node_* classes -- core Blueprint execution nodes
_n("Branch", "UK2Node_IfThenElse", "flow_control", "Conditional branching based on bool", ["if", "condition", "branch"])
_n("Sequence", "UK2Node_ExecutionSequence", "flow_control", "Execute multiple outputs in order", ["sequence", "order", "sequential"])
_n("ForLoop", "UK2Node_ForLoop", "flow_control", "Loop from start to end index", ["loop", "for", "iterate", "index"])
_n("ForLoopWithBreak", "UK2Node_ForLoopWithBreak", "flow_control", "Loop with early exit capability", ["loop", "for", "break"])
_n("ForEachLoop", "UK2Node_ForEachLoop", "flow_control", "Iterate over array elements", ["loop", "array", "iterate", "foreach"])
_n("ForEachLoopWithBreak", "UK2Node_ForEachLoopWithBreak", "flow_control", "Iterate array with early exit", ["loop", "array", "break"])
_n("WhileLoop", "UK2Node_WhileLoop", "flow_control", "Loop while condition is true", ["loop", "while", "condition"])
_n("Delay", "UKismetSystemLibrary", "flow_control", "Latent delay by seconds", ["delay", "timer", "wait", "pause"])
_n("RetriggerableDelay", "UKismetSystemLibrary", "flow_control", "Retriggerable latent delay", ["delay", "retrigger", "reset"])
_n("MoveComponentTo", "UKismetSystemLibrary", "flow_control", "Latent move component to location/rotation", ["move", "component", "latent"])
_n("DoOnce", "UK2Node_DoOnce", "flow_control", "Execute only once until reset", ["once", "gate", "single"])
_n("DoN", "UK2Node_DoN", "flow_control", "Execute N times then stop", ["count", "limit", "repeat"])
_n("Gate", "UK2Node_Gate", "flow_control", "Open/close execution gate", ["gate", "control", "toggle"])
_n("FlipFlop", "UK2Node_FlipFlop", "flow_control", "Alternate between two outputs A and B", ["toggle", "alternate", "flip"])
_n("MultiGate", "UK2Node_MultiGate", "flow_control", "Route execution to multiple outputs sequentially or randomly", ["gate", "multi", "route", "random"])
_n("Select", "UK2Node_Select", "flow_control", "Select value based on index", ["select", "switch", "index", "mux"])
_n("SwitchOnInt", "UK2Node_SwitchInteger", "flow_control", "Branch execution based on integer value", ["switch", "integer", "branch"])
_n("SwitchOnString", "UK2Node_SwitchString", "flow_control", "Branch execution based on string value", ["switch", "string", "branch"])
_n("SwitchOnName", "UK2Node_SwitchName", "flow_control", "Branch execution based on FName value", ["switch", "name", "branch"])
_n("SwitchOnEnum", "UK2Node_SwitchEnum", "flow_control", "Branch execution based on enum value", ["switch", "enum", "branch"])
_n("SwitchOnClass", "UK2Node_SwitchClass", "flow_control", "Branch execution based on object class", ["switch", "class", "type"])
_n("IsValid", "UKismetSystemLibrary", "flow_control", "Check if object reference is valid", ["valid", "null", "check", "none"])
_n("CastToClass", "UK2Node_DynamicCast", "flow_control", "Cast object to specific class with success/fail branches", ["cast", "type", "class", "convert"])
_n("DoesImplementInterface", "UK2Node_DynamicCast", "flow_control", "Check if object implements a Blueprint interface", ["interface", "check", "implements"])
_n("Return", "UK2Node_FunctionResult", "flow_control", "Return value from function", ["return", "function", "result", "output"])
_n("LocalVariable", "UK2Node_TemporaryVariable", "flow_control", "Declare a local variable within function scope", ["variable", "local", "temp"])
_n("BreakExec", "UK2Node_BreakExec", "flow_control", "Break execution flow", ["break", "stop", "halt"])

# --- TIMER (13 nodes) ---
# Source: UKismetSystemLibrary -- official C++ names
_n("K2_SetTimer", "UKismetSystemLibrary", "timer", "Sets timer by delegate", ["timer", "set", "event", "schedule"])
_n("K2_SetTimerForNextTick", "UKismetSystemLibrary", "timer", "Fires delegate next tick", ["timer", "next", "tick"])
_n("K2_SetTimerByFunctionName", "UKismetSystemLibrary", "timer", "Sets timer by function name", ["timer", "function", "delay", "repeat"])
_n("K2_ClearTimer", "UKismetSystemLibrary", "timer", "Clears timer by function name", ["timer", "clear", "stop"])
_n("K2_ClearTimerHandle", "UKismetSystemLibrary", "timer", "Clears timer by handle", ["timer", "clear", "handle"])
_n("K2_ClearAndInvalidateTimerHandle", "UKismetSystemLibrary", "timer", "Clears and invalidates timer handle", ["timer", "clear", "invalidate"])
_n("K2_PauseTimer", "UKismetSystemLibrary", "timer", "Pauses timer", ["timer", "pause"])
_n("K2_UnPauseTimer", "UKismetSystemLibrary", "timer", "Unpauses timer", ["timer", "resume", "unpause"])
_n("K2_IsTimerActive", "UKismetSystemLibrary", "timer", "Checks if timer is running", ["timer", "active", "check"])
_n("K2_IsTimerPaused", "UKismetSystemLibrary", "timer", "Checks if timer is paused", ["timer", "paused", "check"])
_n("K2_TimerExists", "UKismetSystemLibrary", "timer", "Checks if timer exists", ["timer", "exists", "check"])
_n("K2_GetTimerElapsedTime", "UKismetSystemLibrary", "timer", "Returns elapsed time on timer", ["timer", "elapsed", "time"])
_n("K2_GetTimerRemainingTime", "UKismetSystemLibrary", "timer", "Returns remaining time on timer", ["timer", "remaining", "time"])

# --- COMPARISON (8 nodes) ---
_n("Equal_Int", "UKismetMathLibrary", "comparison", "Check if two integers are equal", ["equal", "compare", "int"])
_n("NotEqual_Int", "UKismetMathLibrary", "comparison", "Check if two integers differ", ["not equal", "compare", "int"])
_n("Less_Int", "UKismetMathLibrary", "comparison", "Check if int A < int B", ["less", "compare", "int"])
_n("Greater_Int", "UKismetMathLibrary", "comparison", "Check if int A > int B", ["greater", "compare", "int"])
_n("Equal_Float", "UKismetMathLibrary", "comparison", "Check if two floats are equal", ["equal", "compare", "float"])
_n("Less_Float", "UKismetMathLibrary", "comparison", "Check if float A < float B", ["less", "compare", "float"])
_n("Greater_Float", "UKismetMathLibrary", "comparison", "Check if float A > float B", ["greater", "compare", "float"])
_n("Equal_String", "UKismetStringLibrary", "comparison", "Check if two strings are equal", ["equal", "compare", "string"])

# --- CONVERSION (11 nodes) ---
_n("Conv_IntToFloat", "UKismetMathLibrary", "conversion", "Convert integer to float", ["convert", "int", "float"])
_n("Conv_FloatToInt", "UKismetMathLibrary", "conversion", "Convert float to integer (truncate)", ["convert", "float", "int"])
_n("Conv_IntToText", "UKismetTextLibrary", "conversion", "Convert integer to FText", ["convert", "int", "text"])
_n("Conv_FloatToText", "UKismetTextLibrary", "conversion", "Convert float to FText", ["convert", "float", "text"])
_n("Conv_IntToBool", "UKismetMathLibrary", "conversion", "Convert integer to bool (0=false)", ["convert", "int", "bool"])
_n("Conv_IntToByte", "UKismetMathLibrary", "conversion", "Convert integer to byte", ["convert", "int", "byte"])
_n("Conv_ByteToInt", "UKismetMathLibrary", "conversion", "Convert byte to integer", ["convert", "byte", "int"])
_n("MakeStruct", "UK2Node_MakeStruct", "conversion", "Create struct from individual values", ["struct", "make", "create"])
_n("BreakStruct", "UK2Node_BreakStruct", "conversion", "Split struct into individual values", ["struct", "break", "split"])
_n("MakeArray", "UK2Node_MakeArray", "conversion", "Create array from individual values", ["array", "make", "create"])
_n("Conv_StringToText", "UKismetTextLibrary", "conversion", "Convert string to FText", ["convert", "string", "text"])
