"""String, string conversion, string build, and array nodes.
Source: UKismetStringLibrary, UKismetArrayLibrary -- official Epic C++ API.
"""
from __future__ import annotations

from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ===================================================================
# UKismetStringLibrary -- String Operations  (38 nodes)
# Category: string
# Header: Kismet/KismetStringLibrary.h
# ===================================================================

_STR_CLS = "UKismetStringLibrary"
_STR_TAGS = ["string", "text", "parse"]

_n("Len", _STR_CLS, "string", "Returns number of characters in the string", _STR_TAGS)
_n("IsEmpty", _STR_CLS, "string", "Returns true if the string is empty", _STR_TAGS)
_n("Contains", _STR_CLS, "string", "Returns true if string contains specified substring", _STR_TAGS)
_n("StartsWith", _STR_CLS, "string", "Tests whether string starts with given prefix", _STR_TAGS)
_n("EndsWith", _STR_CLS, "string", "Tests whether string ends with given suffix", _STR_TAGS)
_n("MatchesWildcard", _STR_CLS, "string", "Tests against wildcard pattern (* and ?)", _STR_TAGS)
_n("FindSubstring", _STR_CLS, "string", "Returns index of first occurrence of substring (-1 if not found)", _STR_TAGS)
_n("GetSubstring", _STR_CLS, "string", "Returns substring starting at index for given length", _STR_TAGS)
_n("Left", _STR_CLS, "string", "Returns leftmost N characters", _STR_TAGS)
_n("Right", _STR_CLS, "string", "Returns rightmost N characters", _STR_TAGS)
_n("Mid", _STR_CLS, "string", "Returns substring from start index", _STR_TAGS)
_n("LeftPad", _STR_CLS, "string", "Pads string on left to specified length", _STR_TAGS)
_n("RightPad", _STR_CLS, "string", "Pads string on right to specified length", _STR_TAGS)
_n("LeftChop", _STR_CLS, "string", "Removes N characters from the end", _STR_TAGS)
_n("RightChop", _STR_CLS, "string", "Removes N characters from the beginning", _STR_TAGS)
_n("Replace", _STR_CLS, "string", "Replaces all occurrences of From with To", _STR_TAGS)
_n("Reverse", _STR_CLS, "string", "Returns reversed string", _STR_TAGS)
_n("ToUpper", _STR_CLS, "string", "Converts to upper case", _STR_TAGS)
_n("ToLower", _STR_CLS, "string", "Converts to lower case", _STR_TAGS)
_n("Trim", _STR_CLS, "string", "Removes leading whitespace", _STR_TAGS)
_n("TrimTrailing", _STR_CLS, "string", "Removes trailing whitespace", _STR_TAGS)
_n("TrimWhitespace", _STR_CLS, "string", "Removes both leading and trailing whitespace", _STR_TAGS)
_n("GetCharacterAsNumber", _STR_CLS, "string", "Returns numeric value of character at index", _STR_TAGS)
_n("IsNumeric", _STR_CLS, "string", "Returns true if string represents a numeric value", _STR_TAGS)
_n("IsAlpha", _STR_CLS, "string", "Returns true if all characters are alphabetic", _STR_TAGS)
_n("Crc32", _STR_CLS, "string", "Returns CRC32 hash of the string", _STR_TAGS)
_n("ParseIntoArray", _STR_CLS, "string", "Splits string by delimiter into array", _STR_TAGS)
_n("JoinStringArray", _STR_CLS, "string", "Concatenates string array with separator", _STR_TAGS)
_n("EqualEqual_StriStri", _STR_CLS, "string", "Case-insensitive equality", _STR_TAGS)
_n("NotEqual_StriStri", _STR_CLS, "string", "Case-insensitive inequality", _STR_TAGS)
_n("EqualEqual_StrStr", _STR_CLS, "string", "Case-sensitive equality", _STR_TAGS)
_n("NotEqual_StrStr", _STR_CLS, "string", "Case-sensitive inequality", _STR_TAGS)
_n("Less_StrStr", _STR_CLS, "string", "Lexicographic less-than", _STR_TAGS)
_n("Greater_StrStr", _STR_CLS, "string", "Lexicographic greater-than", _STR_TAGS)
_n("LessEqual_StrStr", _STR_CLS, "string", "Lexicographic less-or-equal", _STR_TAGS)
_n("GreaterEqual_StrStr", _STR_CLS, "string", "Lexicographic greater-or-equal", _STR_TAGS)
_n("Concat_StrStr", _STR_CLS, "string", "Concatenates two strings", _STR_TAGS)
_n("TimeSecondsToString", _STR_CLS, "string", "Converts seconds to formatted time string", _STR_TAGS)

# ===================================================================
# UKismetStringLibrary -- String Conversions  (20 nodes)
# Category: string_conversion
# ===================================================================

_CONV_TAGS = ["string", "conversion", "format"]

_n("Conv_IntToString", _STR_CLS, "string_conversion", "Integer to string", _CONV_TAGS)
_n("Conv_Int64ToString", _STR_CLS, "string_conversion", "Int64 to string", _CONV_TAGS)
_n("Conv_FloatToString", _STR_CLS, "string_conversion", "Float to string", _CONV_TAGS)
_n("Conv_ByteToString", _STR_CLS, "string_conversion", "Byte to string", _CONV_TAGS)
_n("Conv_BoolToString", _STR_CLS, "string_conversion", "Bool to string (\"true\"/\"false\")", _CONV_TAGS)
_n("Conv_VectorToString", _STR_CLS, "string_conversion", "Vector to string \"X=... Y=... Z=...\"", _CONV_TAGS)
_n("Conv_Vector2DToString", _STR_CLS, "string_conversion", "Vector2D to string", _CONV_TAGS)
_n("Conv_IntVectorToString", _STR_CLS, "string_conversion", "IntVector to string", _CONV_TAGS)
_n("Conv_RotatorToString", _STR_CLS, "string_conversion", "Rotator to string", _CONV_TAGS)
_n("Conv_TransformToString", _STR_CLS, "string_conversion", "Transform to string", _CONV_TAGS)
_n("Conv_ObjectToString", _STR_CLS, "string_conversion", "Object to string (path name)", _CONV_TAGS)
_n("Conv_ColorToString", _STR_CLS, "string_conversion", "Color to string", _CONV_TAGS)
_n("Conv_NameToString", _STR_CLS, "string_conversion", "FName to FString", _CONV_TAGS)
_n("Conv_StringToName", _STR_CLS, "string_conversion", "FString to FName", _CONV_TAGS)
_n("Conv_StringToInt", _STR_CLS, "string_conversion", "String to integer", _CONV_TAGS)
_n("Conv_StringToFloat", _STR_CLS, "string_conversion", "String to float", _CONV_TAGS)
_n("Conv_StringToVector", _STR_CLS, "string_conversion", "Parses \"X=... Y=... Z=...\" to vector", _CONV_TAGS)
_n("Conv_StringToVector2D", _STR_CLS, "string_conversion", "Parses to Vector2D", _CONV_TAGS)
_n("Conv_StringToRotator", _STR_CLS, "string_conversion", "Parses to rotator", _CONV_TAGS)
_n("Conv_StringToColor", _STR_CLS, "string_conversion", "Parses to color", _CONV_TAGS)

# ===================================================================
# UKismetStringLibrary -- Build String Helpers  (10 nodes)
# Category: string_build
# ===================================================================

_BUILD_TAGS = ["string", "build", "format"]

_n("BuildString_Float", _STR_CLS, "string_build", "Constructs string from prefix + float + suffix", _BUILD_TAGS)
_n("BuildString_Int", _STR_CLS, "string_build", "Constructs string from prefix + int + suffix", _BUILD_TAGS)
_n("BuildString_Bool", _STR_CLS, "string_build", "Constructs string from prefix + bool + suffix", _BUILD_TAGS)
_n("BuildString_Vector", _STR_CLS, "string_build", "Constructs string from prefix + vector + suffix", _BUILD_TAGS)
_n("BuildString_Vector2D", _STR_CLS, "string_build", "Constructs string from prefix + vec2d + suffix", _BUILD_TAGS)
_n("BuildString_Rotator", _STR_CLS, "string_build", "Constructs string from prefix + rotator + suffix", _BUILD_TAGS)
_n("BuildString_Object", _STR_CLS, "string_build", "Constructs string from prefix + object + suffix", _BUILD_TAGS)
_n("BuildString_Name", _STR_CLS, "string_build", "Constructs string from prefix + name + suffix", _BUILD_TAGS)
_n("BuildString_Color", _STR_CLS, "string_build", "Constructs string from prefix + color + suffix", _BUILD_TAGS)
_n("BuildString_IntVector", _STR_CLS, "string_build", "Constructs string from prefix + intvec + suffix", _BUILD_TAGS)

# ===================================================================
# UKismetArrayLibrary -- Array Operations  (24 nodes)
# Category: array
# Header: Kismet/KismetArrayLibrary.h
# NOTE: Most functions use CustomThunk (wildcard generic arrays).
# ===================================================================

_ARR_CLS = "UKismetArrayLibrary"
_ARR_TAGS = ["array", "collection", "list"]

_n("Array_Add", _ARR_CLS, "array", "Adds item to end of array, returns new index", _ARR_TAGS)
_n("Array_AddUnique", _ARR_CLS, "array", "Adds item only if not already present", _ARR_TAGS)
_n("Array_Append", _ARR_CLS, "array", "Appends second array to first", _ARR_TAGS)
_n("Array_Insert", _ARR_CLS, "array", "Inserts item at given index", _ARR_TAGS)
_n("Array_Remove", _ARR_CLS, "array", "Removes item at given index", _ARR_TAGS)
_n("Array_RemoveItem", _ARR_CLS, "array", "Removes first occurrence of item", _ARR_TAGS)
_n("Array_Clear", _ARR_CLS, "array", "Removes all items from array", _ARR_TAGS)
_n("Array_Resize", _ARR_CLS, "array", "Resizes array to given length", _ARR_TAGS)
_n("Array_Get", _ARR_CLS, "array", "Returns copy of item at index", _ARR_TAGS)
_n("Array_Set", _ARR_CLS, "array", "Sets item at index", _ARR_TAGS)
_n("Array_Find", _ARR_CLS, "array", "Returns index of first occurrence (-1 if not found)", _ARR_TAGS)
_n("Array_Contains", _ARR_CLS, "array", "Returns true if array contains item", _ARR_TAGS)
_n("Array_Length", _ARR_CLS, "array", "Returns number of items in array", _ARR_TAGS)
_n("Array_LastIndex", _ARR_CLS, "array", "Returns last valid index (length - 1)", _ARR_TAGS)
_n("GetLastIndex", _ARR_CLS, "array", "Alternative name for last valid index", _ARR_TAGS)
_n("Array_IsValidIndex", _ARR_CLS, "array", "Checks if index is within bounds", _ARR_TAGS)
_n("Array_Shuffle", _ARR_CLS, "array", "Randomizes element order", _ARR_TAGS)
_n("Array_Random", _ARR_CLS, "array", "Returns random element and its index", _ARR_TAGS)
_n("Array_RandomFromStream", _ARR_CLS, "array", "Random element using RandomStream", _ARR_TAGS)
_n("Array_Reverse", _ARR_CLS, "array", "Reverses element order", _ARR_TAGS)
_n("Array_Swap", _ARR_CLS, "array", "Swaps elements at two indices", _ARR_TAGS)
_n("Array_Identical", _ARR_CLS, "array", "Checks if two arrays have identical contents", _ARR_TAGS)
_n("FilterArray", _ARR_CLS, "array", "Filters actor array by class type", _ARR_TAGS)
_n("SetArrayPropertyByName", _ARR_CLS, "array", "Sets array property by name via reflection", _ARR_TAGS)
