# UE5 Blueprint Function Libraries - Complete API Reference

_Generated: 2026-02-06 | Sources: 15+ (Epic official docs, Python API, source mirrors, community wiki)_

<key-points>
- 5 major Kismet libraries: Math (300+), String (40+), System (120+), Array (15+), GameplayStatics (100+)
- All functions are BlueprintPure or BlueprintCallable UFUNCTION-decorated static methods
- C++ header: `#include "Kismet/KismetMathLibrary.h"` (pattern for all)
- Python API mirrors C++ names with snake_case (e.g., `RandomFloatInRange` -> `random_float_in_range`)
- Categories match Blueprint editor palette organization
</key-points>

---

## 1. UKismetMathLibrary

**Header**: `Kismet/KismetMathLibrary.h`
**Module**: Engine
**Parent**: UBlueprintFunctionLibrary (BlueprintThreadSafe)
**Blueprint Palette**: Math

### Boolean (Category: Math|Boolean)

| Function | Type | Description |
|----------|------|-------------|
| `Not_PreBool` | BlueprintPure | Logical NOT of a boolean |
| `EqualEqual_BoolBool` | BlueprintPure | Returns true if A equals B |
| `NotEqual_BoolBool` | BlueprintPure | Returns true if A does not equal B |
| `BooleanAND` | BlueprintPure | Logical AND of two booleans |
| `BooleanNAND` | BlueprintPure | Logical NAND of two booleans |
| `BooleanOR` | BlueprintPure | Logical OR of two booleans |
| `BooleanXOR` | BlueprintPure | Logical XOR of two booleans |
| `BooleanNOR` | BlueprintPure | Logical NOR of two booleans |
| `RandomBool` | BlueprintPure | Returns a random boolean value |
| `RandomBoolWithWeight` | BlueprintPure | Returns random bool with weighted probability |
| `RandomBoolWithWeightFromStream` | BlueprintPure | Random bool with weight from RandomStream |

### Byte (Category: Math|Byte)

| Function | Type | Description |
|----------|------|-------------|
| `Multiply_ByteByte` | BlueprintPure | Multiplication (A * B) |
| `Divide_ByteByte` | BlueprintPure | Division (A / B) |
| `Percent_ByteByte` | BlueprintPure | Modulo (A % B) |
| `Add_ByteByte` | BlueprintPure | Addition (A + B) |
| `Subtract_ByteByte` | BlueprintPure | Subtraction (A - B) |
| `BMin` | BlueprintPure | Returns minimum of two bytes |
| `BMax` | BlueprintPure | Returns maximum of two bytes |
| `Less_ByteByte` | BlueprintPure | A < B |
| `Greater_ByteByte` | BlueprintPure | A > B |
| `LessEqual_ByteByte` | BlueprintPure | A <= B |
| `GreaterEqual_ByteByte` | BlueprintPure | A >= B |
| `EqualEqual_ByteByte` | BlueprintPure | A == B |
| `NotEqual_ByteByte` | BlueprintPure | A != B |
| `MaxOfByteArray` | BlueprintPure | Returns max value in byte array |
| `MinOfByteArray` | BlueprintPure | Returns min value in byte array |

### Integer (Category: Math|Integer)

| Function | Type | Description |
|----------|------|-------------|
| `Multiply_IntInt` | BlueprintPure | Multiplication (A * B) |
| `Divide_IntInt` | BlueprintPure | Division (A / B) |
| `Percent_IntInt` | BlueprintPure | Modulo (A % B) |
| `Add_IntInt` | BlueprintPure | Addition (A + B) |
| `Subtract_IntInt` | BlueprintPure | Subtraction (A - B) |
| `Less_IntInt` | BlueprintPure | A < B |
| `Greater_IntInt` | BlueprintPure | A > B |
| `LessEqual_IntInt` | BlueprintPure | A <= B |
| `GreaterEqual_IntInt` | BlueprintPure | A >= B |
| `EqualEqual_IntInt` | BlueprintPure | A == B |
| `NotEqual_IntInt` | BlueprintPure | A != B |
| `InRange_IntInt` | BlueprintPure | Returns true if value is within range [Min, Max] |
| `And_IntInt` | BlueprintPure | Bitwise AND |
| `Xor_IntInt` | BlueprintPure | Bitwise XOR |
| `Or_IntInt` | BlueprintPure | Bitwise OR |
| `Not_Int` | BlueprintPure | Bitwise NOT |
| `SignOfInteger` | BlueprintPure | Returns sign of integer (-1, 0, or 1) |
| `RandomInteger` | BlueprintPure | Returns random int in [0, Max) |
| `RandomIntegerInRange` | BlueprintPure | Returns random int in [Min, Max] |
| `Min` | BlueprintPure | Returns smaller of two ints |
| `Max` | BlueprintPure | Returns larger of two ints |
| `Clamp` | BlueprintPure | Clamps int to [Min, Max] range |
| `Wrap` | BlueprintPure | Wraps int to range |
| `Abs_Int` | BlueprintPure | Returns absolute value |
| `MaxOfIntArray` | BlueprintPure | Returns max value in int array |
| `MinOfIntArray` | BlueprintPure | Returns min value in int array |

### Integer64 (Category: Math|Integer64)

| Function | Type | Description |
|----------|------|-------------|
| `Multiply_Int64Int64` | BlueprintPure | Multiplication |
| `Divide_Int64Int64` | BlueprintPure | Division |
| `Add_Int64Int64` | BlueprintPure | Addition |
| `Subtract_Int64Int64` | BlueprintPure | Subtraction |
| `Less_Int64Int64` | BlueprintPure | A < B |
| `Greater_Int64Int64` | BlueprintPure | A > B |
| `LessEqual_Int64Int64` | BlueprintPure | A <= B |
| `GreaterEqual_Int64Int64` | BlueprintPure | A >= B |
| `EqualEqual_Int64Int64` | BlueprintPure | A == B |
| `NotEqual_Int64Int64` | BlueprintPure | A != B |
| `InRange_Int64Int64` | BlueprintPure | Value within range check |
| `And_Int64Int64` | BlueprintPure | Bitwise AND |
| `Xor_Int64Int64` | BlueprintPure | Bitwise XOR |
| `Or_Int64Int64` | BlueprintPure | Bitwise OR |
| `Not_Int64` | BlueprintPure | Bitwise NOT |
| `SignOfInteger64` | BlueprintPure | Returns sign (-1, 0, or 1) |
| `RandomInteger64` | BlueprintPure | Random int64 |
| `RandomInteger64InRange` | BlueprintPure | Random int64 in range |
| `MinInt64` | BlueprintPure | Returns smaller of two int64s |
| `MaxInt64` | BlueprintPure | Returns larger of two int64s |
| `ClampInt64` | BlueprintPure | Clamps int64 to range |
| `Abs_Int64` | BlueprintPure | Absolute value |

### Float (Category: Math|Float)

| Function | Type | Description |
|----------|------|-------------|
| `MultiplyMultiply_FloatFloat` | BlueprintPure | Power (A ^ B) |
| `Multiply_FloatFloat` | BlueprintPure | Multiplication (A * B) |
| `Multiply_IntFloat` | BlueprintPure | Int * Float |
| `Divide_FloatFloat` | BlueprintPure | Division (A / B) |
| `Percent_FloatFloat` | BlueprintPure | Modulo |
| `Fraction` | BlueprintPure | Returns fractional part of float |
| `Add_FloatFloat` | BlueprintPure | Addition |
| `Subtract_FloatFloat` | BlueprintPure | Subtraction |
| `Less_FloatFloat` | BlueprintPure | A < B |
| `Greater_FloatFloat` | BlueprintPure | A > B |
| `LessEqual_FloatFloat` | BlueprintPure | A <= B |
| `GreaterEqual_FloatFloat` | BlueprintPure | A >= B |
| `EqualEqual_FloatFloat` | BlueprintPure | A == B |
| `NearlyEqual_FloatFloat` | BlueprintPure | Approximate equality within tolerance |
| `NotEqual_FloatFloat` | BlueprintPure | A != B |
| `InRange_FloatFloat` | BlueprintPure | Value within range check |
| `Hypotenuse` | BlueprintPure | Returns hypotenuse from width and height |
| `GridSnap_Float` | BlueprintPure | Snaps value to nearest grid increment |
| `Abs` | BlueprintPure | Absolute value of float |
| `Exp` | BlueprintPure | Exponential (e^A) |
| `Log` | BlueprintPure | Logarithm base 10 |
| `Loge` | BlueprintPure | Natural logarithm (ln) |
| `Sqrt` | BlueprintPure | Square root |
| `Square` | BlueprintPure | Square (A * A) |
| `RandomFloat` | BlueprintPure | Random float in [0, 1) |
| `RandomFloatInRange` | BlueprintPure | Random float in [Min, Max] |
| `FMin` | BlueprintPure | Returns smaller of two floats |
| `FMax` | BlueprintPure | Returns larger of two floats |
| `FClamp` | BlueprintPure | Clamps float to [Min, Max] |
| `FWrap` | BlueprintPure | Wraps float to range |
| `SafeDivide` | BlueprintPure | Division that returns 0 on divide-by-zero |
| `MaxOfFloatArray` | BlueprintPure | Returns max value in float array |
| `MinOfFloatArray` | BlueprintPure | Returns min value in float array |
| `ClampAngle` | BlueprintPure | Clamps angle to range |
| `Round` | BlueprintPure | Rounds to nearest int |
| `FFloor` | BlueprintPure | Rounds down to nearest int |
| `FTrunc` | BlueprintPure | Truncates toward zero |
| `FCeil` | BlueprintPure | Rounds up to nearest int |
| `Round64` | BlueprintPure | Rounds to nearest int64 |
| `FFloor64` | BlueprintPure | Rounds down to int64 |
| `FTrunc64` | BlueprintPure | Truncates to int64 |
| `FCeil64` | BlueprintPure | Rounds up to int64 |
| `FMod` | BlueprintPure | Floating-point modulo |
| `SignOfFloat` | BlueprintPure | Returns sign (-1.0, 0.0, or 1.0) |
| `NormalizeToRange` | BlueprintPure | Normalizes value to [0, 1] range given min/max |
| `MapRangeUnclamped` | BlueprintPure | Maps value from one range to another (no clamping) |
| `MapRangeClamped` | BlueprintPure | Maps value from one range to another (clamped) |
| `MultiplyByPi` | BlueprintPure | Multiplies value by PI |
| `FInterpEaseInOut` | BlueprintPure | Ease-in-out interpolation |
| `MakePulsatingValue` | BlueprintPure | Creates pulsating value from time input |
| `FixedTurn` | BlueprintPure | Returns angle clamped by max turn rate |

### Trigonometry (Category: Math|Trig)

| Function | Type | Description |
|----------|------|-------------|
| `Sin` | BlueprintPure | Sine (radians input) |
| `Asin` | BlueprintPure | Arc sine (returns radians) |
| `Cos` | BlueprintPure | Cosine (radians input) |
| `Acos` | BlueprintPure | Arc cosine (returns radians) |
| `Tan` | BlueprintPure | Tangent (radians input) |
| `Atan` | BlueprintPure | Arc tangent (returns radians) |
| `Atan2` | BlueprintPure | Arc tangent of Y/X (returns radians) |
| `GetPI` | BlueprintPure | Returns PI constant |
| `GetTAU` | BlueprintPure | Returns TAU constant (2*PI) |
| `DegreesToRadians` | BlueprintPure | Converts degrees to radians |
| `RadiansToDegrees` | BlueprintPure | Converts radians to degrees |
| `DegSin` | BlueprintPure | Sine (degrees input) |
| `DegAsin` | BlueprintPure | Arc sine (returns degrees) |
| `DegCos` | BlueprintPure | Cosine (degrees input) |
| `DegAcos` | BlueprintPure | Arc cosine (returns degrees) |
| `DegTan` | BlueprintPure | Tangent (degrees input) |
| `DegAtan` | BlueprintPure | Arc tangent (returns degrees) |
| `DegAtan2` | BlueprintPure | Arc tangent of Y/X (returns degrees) |

### Interpolation (Category: Math|Interpolation)

| Function | Type | Description |
|----------|------|-------------|
| `Lerp` | BlueprintPure | Linear interpolation between A and B by Alpha |
| `Ease` | BlueprintPure | Eased interpolation with configurable function |
| `VLerp` | BlueprintPure | Vector linear interpolation |
| `VEase` | BlueprintPure | Vector eased interpolation |
| `VInterpTo` | BlueprintPure | Interpolates vector toward target at given speed |
| `VInterpTo_Constant` | BlueprintPure | Constant-speed vector interpolation |
| `VectorSpringInterp` | BlueprintPure | Spring-based vector interpolation |
| `Vector2DInterpTo` | BlueprintPure | 2D vector interpolation toward target |
| `Vector2DInterpTo_Constant` | BlueprintPure | Constant-speed 2D vector interpolation |
| `RInterpTo` | BlueprintPure | Rotator interpolation toward target |
| `RInterpTo_Constant` | BlueprintPure | Constant-speed rotator interpolation |
| `TInterpTo` | BlueprintPure | Transform interpolation toward target |
| `CInterpTo` | BlueprintPure | LinearColor interpolation toward target |
| `FInterpTo` | BlueprintPure | Float interpolation toward target at given speed |
| `FInterpTo_Constant` | BlueprintPure | Constant-speed float interpolation |

### IntPoint (Category: Math|IntPoint)

| Function | Type | Description |
|----------|------|-------------|
| `IntPoint_Zero` | BlueprintPure | Returns (0,0) IntPoint constant |
| `IntPoint_One` | BlueprintPure | Returns (1,1) IntPoint constant |
| `IntPoint_Up` | BlueprintPure | Returns up direction IntPoint |
| `IntPoint_Left` | BlueprintPure | Returns left direction IntPoint |
| `IntPoint_Right` | BlueprintPure | Returns right direction IntPoint |
| `IntPoint_Down` | BlueprintPure | Returns down direction IntPoint |
| `Conv_IntPointToVector2D` | BlueprintPure | Converts IntPoint to Vector2D |
| `Add_IntPointIntPoint` | BlueprintPure | IntPoint addition |
| `Add_IntPointInt` | BlueprintPure | Add scalar to IntPoint |
| `Subtract_IntPointIntPoint` | BlueprintPure | IntPoint subtraction |
| `Subtract_IntPointInt` | BlueprintPure | Subtract scalar from IntPoint |
| `Multiply_IntPointIntPoint` | BlueprintPure | IntPoint multiplication |
| `Multiply_IntPointInt` | BlueprintPure | Multiply IntPoint by scalar |
| `Divide_IntPointIntPoint` | BlueprintPure | IntPoint division |
| `Divide_IntPointInt` | BlueprintPure | Divide IntPoint by scalar |
| `Equal_IntPointIntPoint` | BlueprintPure | IntPoint equality check |
| `NotEqual_IntPointIntPoint` | BlueprintPure | IntPoint inequality check |

### Vector2D (Category: Math|Vector2D)

| Function | Type | Description |
|----------|------|-------------|
| `Vector2D_One` | BlueprintPure | Returns (1,1) constant |
| `Vector2D_Unit45Deg` | BlueprintPure | Returns unit vector at 45 degrees |
| `Vector2D_Zero` | BlueprintPure | Returns (0,0) constant |
| `MakeVector2D` | BlueprintPure | Creates Vector2D from X, Y components |
| `BreakVector2D` | BlueprintPure | Breaks Vector2D into X, Y components |
| `Conv_Vector2DToVector` | BlueprintPure | Converts 2D to 3D vector (Z=0) |
| `Conv_Vector2DToIntPoint` | BlueprintPure | Converts Vector2D to IntPoint |
| `Add_Vector2DVector2D` | BlueprintPure | Vector2D addition |
| `Add_Vector2DFloat` | BlueprintPure | Add scalar to Vector2D |
| `Subtract_Vector2DVector2D` | BlueprintPure | Vector2D subtraction |
| `Subtract_Vector2DFloat` | BlueprintPure | Subtract scalar from Vector2D |
| `Multiply_Vector2DVector2D` | BlueprintPure | Component-wise multiplication |
| `Multiply_Vector2DFloat` | BlueprintPure | Scalar multiplication |
| `Divide_Vector2DVector2D` | BlueprintPure | Component-wise division |
| `Divide_Vector2DFloat` | BlueprintPure | Scalar division |
| `EqualExactly_Vector2DVector2D` | BlueprintPure | Exact equality check |
| `EqualEqual_Vector2DVector2D` | BlueprintPure | Approximate equality check |
| `NotEqualExactly_Vector2DVector2D` | BlueprintPure | Exact inequality check |
| `NotEqual_Vector2DVector2D` | BlueprintPure | Approximate inequality check |
| `Negated2D` | BlueprintPure | Returns negated vector |
| `Set2D` | BlueprintCallable | Sets vector components |
| `ClampAxes2D` | BlueprintPure | Clamps each axis to range |
| `CrossProduct2D` | BlueprintPure | 2D cross product |
| `Distance2D` | BlueprintPure | Distance between two 2D points |
| `DistanceSquared2D` | BlueprintPure | Squared distance (faster, no sqrt) |
| `DotProduct2D` | BlueprintPure | 2D dot product |
| `GetAbs2D` | BlueprintPure | Absolute value of each component |
| `GetAbsMax2D` | BlueprintPure | Max of absolute component values |
| `GetMax2D` | BlueprintPure | Max component value |
| `GetMin2D` | BlueprintPure | Min component value |
| `GetRotated2D` | BlueprintPure | Rotates vector by angle in degrees |
| `IsNearlyZero2D` | BlueprintPure | Near-zero check with tolerance |
| `IsZero2D` | BlueprintPure | Exact zero check |
| `NormalSafe2D` | BlueprintPure | Safe normalization (handles zero) |
| `Normal2D` | BlueprintPure | Returns normalized vector |
| `Normalize2D` | BlueprintCallable | Normalizes vector in-place |
| `Spherical2DToUnitCartesian` | BlueprintPure | Spherical to cartesian conversion |
| `ToDirectionAndLength2D` | BlueprintPure | Splits into direction + magnitude |
| `ToRounded2D` | BlueprintPure | Rounds each component |
| `ToSign2D` | BlueprintPure | Returns sign of each component |
| `VSize2D` | BlueprintPure | Vector magnitude (length) |
| `VSize2DSquared` | BlueprintPure | Squared magnitude (faster) |

### Vector 3D Constants (Category: Math|Vector)

| Function | Type | Description |
|----------|------|-------------|
| `Vector_Zero` | BlueprintPure | Returns (0,0,0) |
| `Vector_One` | BlueprintPure | Returns (1,1,1) |
| `Vector_Forward` | BlueprintPure | Returns forward direction (1,0,0) |
| `Vector_Backward` | BlueprintPure | Returns backward direction (-1,0,0) |
| `Vector_Up` | BlueprintPure | Returns up direction (0,0,1) |
| `Vector_Down` | BlueprintPure | Returns down direction (0,0,-1) |
| `Vector_Right` | BlueprintPure | Returns right direction (0,1,0) |
| `Vector_Left` | BlueprintPure | Returns left direction (0,-1,0) |

### Vector 3D Operations (Category: Math|Vector)

| Function | Type | Description |
|----------|------|-------------|
| `MakeVector` | BlueprintPure | Creates vector from X, Y, Z components |
| `CreateVectorFromYawPitch` | BlueprintPure | Creates direction vector from yaw/pitch angles |
| `Vector_Assign` | BlueprintCallable | Assigns one vector to another |
| `Vector_Set` | BlueprintCallable | Sets vector X, Y, Z values |
| `BreakVector` | BlueprintPure | Breaks vector into X, Y, Z |
| `Conv_VectorToLinearColor` | BlueprintPure | Vector to LinearColor conversion |
| `Conv_VectorToTransform` | BlueprintPure | Vector to Transform (as location) |
| `Conv_VectorToVector2D` | BlueprintPure | 3D to 2D (drops Z) |
| `Conv_VectorToRotator` | BlueprintPure | Direction vector to rotator |
| `Conv_VectorToQuaternion` | BlueprintPure | Euler angles to quaternion |
| `RotatorFromAxisAndAngle` | BlueprintPure | Creates rotator from axis and angle |
| `Add_VectorVector` | BlueprintPure | Vector addition |
| `Add_VectorFloat` | BlueprintPure | Add scalar to all components |
| `Add_VectorInt` | BlueprintPure | Add int to all components |
| `Subtract_VectorVector` | BlueprintPure | Vector subtraction |
| `Subtract_VectorFloat` | BlueprintPure | Subtract scalar from components |
| `Subtract_VectorInt` | BlueprintPure | Subtract int from components |
| `Multiply_VectorVector` | BlueprintPure | Component-wise multiply |
| `Multiply_VectorFloat` | BlueprintPure | Scalar multiply |
| `Multiply_VectorInt` | BlueprintPure | Int multiply |
| `Divide_VectorVector` | BlueprintPure | Component-wise divide |
| `Divide_VectorFloat` | BlueprintPure | Scalar divide |
| `Divide_VectorInt` | BlueprintPure | Int divide |
| `NegateVector` | BlueprintPure | Returns negated vector |
| `EqualExactly_VectorVector` | BlueprintPure | Exact equality |
| `EqualEqual_VectorVector` | BlueprintPure | Approximate equality |
| `NotEqualExactly_VectorVector` | BlueprintPure | Exact inequality |
| `NotEqual_VectorVector` | BlueprintPure | Approximate inequality |
| `Dot_VectorVector` | BlueprintPure | Dot product |
| `Cross_VectorVector` | BlueprintPure | Cross product |
| `GreaterGreater_VectorRotator` | BlueprintPure | Rotate vector by rotator (>>) |
| `RotateAngleAxis` | BlueprintPure | Rotates vector around axis by angle |
| `LessLess_VectorRotator` | BlueprintPure | Unrotate vector by rotator (<<) |
| `Vector_UnwindEuler` | BlueprintCallable | Unwinds Euler angles to [-180, 180] |
| `ClampVectorSize` | BlueprintPure | Clamps vector magnitude to range |
| `Vector_ClampSize2D` | BlueprintPure | Clamps 2D magnitude |
| `Vector_ClampSizeMax` | BlueprintPure | Clamps to maximum magnitude |
| `Vector_ClampSizeMax2D` | BlueprintPure | Clamps 2D to maximum magnitude |
| `GetMinElement` | BlueprintPure | Returns smallest component |
| `GetMaxElement` | BlueprintPure | Returns largest component |
| `Vector_GetAbsMax` | BlueprintPure | Max of absolute components |
| `Vector_GetAbsMin` | BlueprintPure | Min of absolute components |
| `Vector_GetAbs` | BlueprintPure | Absolute value of each component |
| `Vector_ComponentMin` | BlueprintPure | Per-component min of two vectors |
| `Vector_ComponentMax` | BlueprintPure | Per-component max of two vectors |
| `Vector_GetSignVector` | BlueprintPure | Sign of each component |
| `Vector_GetProjection` | BlueprintPure | Projects vector onto plane |
| `Vector_HeadingAngle` | BlueprintPure | Returns heading angle in radians |
| `Vector_CosineAngle2D` | BlueprintPure | Cosine of 2D angle between vectors |
| `Vector_ToRadians` | BlueprintPure | Converts degree components to radians |
| `Vector_ToDegrees` | BlueprintPure | Converts radian components to degrees |
| `Vector_UnitCartesianToSpherical` | BlueprintPure | Cartesian to spherical coordinates |
| `GetDirectionUnitVector` | BlueprintPure | Unit direction from A to B |
| `GetYawPitchFromVector` | BlueprintPure | Extracts yaw/pitch from direction |
| `GetAzimuthAndElevation` | BlueprintPure | Direction to azimuth + elevation |
| `GetVectorArrayAverage` | BlueprintPure | Average of vector array |
| `FTruncVector` | BlueprintPure | Truncates each component to int |
| `Vector_Distance` | BlueprintPure | 3D distance between points |
| `Vector_DistanceSquared` | BlueprintPure | Squared 3D distance (faster) |
| `Vector_Distance2D` | BlueprintPure | 2D distance (ignoring Z) |
| `Vector_Distance2DSquared` | BlueprintPure | Squared 2D distance |
| `VSize` | BlueprintPure | Vector magnitude |
| `VSizeSquared` | BlueprintPure | Squared magnitude |
| `VSizeXY` | BlueprintPure | XY plane magnitude |
| `VSizeXYSquared` | BlueprintPure | Squared XY magnitude |
| `Vector_IsNearlyZero` | BlueprintPure | Near-zero check with tolerance |
| `Vector_IsZero` | BlueprintPure | Exact zero check |
| `Vector_IsNAN` | BlueprintPure | Checks for NaN values |
| `Vector_IsUniform` | BlueprintPure | All components nearly equal |
| `Vector_IsUnit` | BlueprintPure | Is unit length |
| `Vector_IsNormal` | BlueprintPure | Is normalized |
| `Normal` | BlueprintPure | Returns normalized vector |
| `Vector_Normal2D` | BlueprintPure | Returns 2D-normalized vector |
| `Vector_NormalUnsafe` | BlueprintPure | Normalize without zero check |
| `Vector_Normalize` | BlueprintCallable | Normalizes in-place |
| `Vector_Reciprocal` | BlueprintPure | Returns 1/component for each |
| `GetReflectionVector` | BlueprintPure | Reflects direction off surface |
| `MirrorVectorByNormal` | BlueprintPure | Mirrors vector by normal |
| `Vector_MirrorByPlane` | BlueprintPure | Mirrors vector by plane |
| `Vector_SnappedToGrid` | BlueprintPure | Snaps components to grid |
| `ProjectVectorOnToVector` | BlueprintPure | Projects one vector onto another |
| `ProjectPointOnToPlane` | BlueprintPure | Projects point onto plane |
| `ProjectVectorOnToPlane` | BlueprintPure | Projects vector onto plane |
| `FindLookAtRotation` | BlueprintPure | Rotation needed to look from start to target |
| `FindClosestPointOnSegment` | BlueprintPure | Nearest point on line segment |
| `FindClosestPointOnLine` | BlueprintPure | Nearest point on infinite line |
| `FindNearestPointsOnLineSegments` | BlueprintPure | Closest points between two segments |
| `GetPointDistanceToSegment` | BlueprintPure | Distance from point to segment |
| `GetPointDistanceToLine` | BlueprintPure | Distance from point to infinite line |

### Rotator (Category: Math|Rotator)

| Function | Type | Description |
|----------|------|-------------|
| `MakeRotator` | BlueprintPure | Creates rotator from Roll, Pitch, Yaw |
| `MakeRotFromX` | BlueprintPure | Creates rotation aligning X with direction |
| `MakeRotFromY` | BlueprintPure | Creates rotation aligning Y with direction |
| `MakeRotFromZ` | BlueprintPure | Creates rotation aligning Z with direction |
| `MakeRotFromXY` | BlueprintPure | Creates rotation from X and Y directions |
| `MakeRotFromXZ` | BlueprintPure | Creates rotation from X and Z directions |
| `MakeRotFromYX` | BlueprintPure | Creates rotation from Y and X directions |
| `MakeRotFromYZ` | BlueprintPure | Creates rotation from Y and Z directions |
| `MakeRotFromZX` | BlueprintPure | Creates rotation from Z and X directions |
| `MakeRotFromZY` | BlueprintPure | Creates rotation from Z and Y directions |
| `BreakRotator` | BlueprintPure | Breaks rotator into Roll, Pitch, Yaw |
| `BreakRotIntoAxes` | BlueprintPure | Breaks rotator into forward/right/up axes |
| `ComposeRotators` | BlueprintPure | Combines two rotations (A * B) |
| `NegateRotator` | BlueprintPure | Returns negated rotator |
| `GetForwardVector` | BlueprintPure | Forward direction from rotator |
| `GetRightVector` | BlueprintPure | Right direction from rotator |
| `GetUpVector` | BlueprintPure | Up direction from rotator |
| `Conv_RotatorToVector` | BlueprintPure | Gets X direction after rotation |
| `Conv_RotatorToTransform` | BlueprintPure | Rotator to transform conversion |
| `NormalizeAxis` | BlueprintPure | Normalizes angle to [-180, 180] |
| `ClampAngle` | BlueprintPure | Clamps angle to [Min, Max] |
| `RLerp` | BlueprintPure | Rotator linear interpolation |
| `REase` | BlueprintPure | Rotator eased interpolation |
| `RInterpTo` | BlueprintPure | Rotator interpolation toward target |
| `RInterpTo_Constant` | BlueprintPure | Constant-speed rotator interpolation |
| `RotatorFromAxisAndAngle` | BlueprintPure | Creates rotator from axis + angle |
| `InvertRotator` | BlueprintPure | Inverts the rotator (reverse rotation) |
| `SelectRotator` | BlueprintPure | Selects A or B based on boolean |
| `Delta_Rotator` | BlueprintPure | Shortest path delta between two rotators |
| `EqualEqual_RotatorRotator` | BlueprintPure | Approximate equality |
| `NotEqual_RotatorRotator` | BlueprintPure | Approximate inequality |

### Quaternion (Category: Math|Quat)

| Function | Type | Description |
|----------|------|-------------|
| `MakeQuat` | BlueprintPure | Creates quaternion from X, Y, Z, W |
| `Quat_MakeFromEuler` | BlueprintPure | Quaternion from Euler angles |
| `BreakQuat` | BlueprintPure | Breaks quaternion into components |
| `Quat_IsIdentity` | BlueprintPure | Checks if identity quaternion |
| `Quat_IsNonFinite` | BlueprintPure | Checks for NaN/Inf values |
| `Quat_Exp` | BlueprintPure | Quaternion exponential |
| `Quat_Log` | BlueprintPure | Quaternion logarithm |
| `Quat_Inversed` | BlueprintPure | Returns inverse quaternion |
| `Quat_Normalized` | BlueprintPure | Returns normalized quaternion |
| `Quat_RotateVector` | BlueprintPure | Rotates vector by quaternion |
| `Quat_UnrotateVector` | BlueprintPure | Inverse-rotates vector |
| `Quat_VectorForward` | BlueprintPure | Forward direction from quat |
| `Quat_VectorRight` | BlueprintPure | Right direction from quat |
| `Quat_VectorUp` | BlueprintPure | Up direction from quat |
| `Quat_Rotator` | BlueprintPure | Converts quaternion to rotator |
| `Quat_Euler` | BlueprintPure | Converts quaternion to Euler angles |
| `Quat_SetFromEuler` | BlueprintCallable | Sets quaternion from Euler angles |
| `Quat_SetComponents` | BlueprintCallable | Sets XYZW components |
| `Quat_AngularDistance` | BlueprintPure | Angular distance between two quats |
| `Quat_EnforceShortestArcWith` | BlueprintCallable | Ensures shortest arc interpolation |
| `Quat_Slerp` | BlueprintPure | Spherical interpolation between quats |

### Transform (Category: Math|Transform)

| Function | Type | Description |
|----------|------|-------------|
| `MakeTransform` | BlueprintPure | Creates from location, rotation, scale |
| `BreakTransform` | BlueprintPure | Breaks into location, rotation, scale |
| `ComposeTransforms` | BlueprintPure | Composes A * B |
| `InvertTransform` | BlueprintPure | Returns inverted transform |
| `ConvertTransformToRelative` | BlueprintPure | Converts to relative space |
| `TransformLocation` | BlueprintPure | Transforms a position |
| `TransformDirection` | BlueprintPure | Transforms a direction (ignores translation) |
| `InverseTransformLocation` | BlueprintPure | Inverse-transforms a position |
| `InverseTransformDirection` | BlueprintPure | Inverse-transforms a direction |
| `InverseTransformRotation` | BlueprintPure | Inverse-transforms a rotation |
| `TLerp` | BlueprintPure | Transform linear interpolation |
| `TEase` | BlueprintPure | Transform eased interpolation |
| `TInterpTo` | BlueprintPure | Transform interpolation toward target |
| `SelectTransform` | BlueprintPure | Selects A or B based on boolean |
| `EqualEqual_TransformTransform` | BlueprintPure | Transform equality check |
| `Transform_Identity` | BlueprintPure | Returns identity transform |
| `Conv_VectorToTransform` | BlueprintPure | Vector to transform (as location) |
| `Conv_RotatorToTransform` | BlueprintPure | Rotator to transform |
| `Conv_MatrixToTransform` | BlueprintPure | Matrix to transform |

### DateTime (Category: Math|DateTime)

| Function | Type | Description |
|----------|------|-------------|
| `MakeDateTime` | BlueprintPure | Creates DateTime from year/month/day/etc. |
| `BreakDateTime` | BlueprintPure | Breaks DateTime into components |
| `Now` | BlueprintPure | Returns current local date and time |
| `UtcNow` | BlueprintPure | Returns current UTC date and time |
| `Today` | BlueprintPure | Returns today's date (midnight) |
| `DateTimeFromString` | BlueprintPure | Parses date string |
| `DateTimeFromIsoString` | BlueprintPure | Parses ISO-8601 date string |
| `DateTimeMaxValue` | BlueprintPure | Maximum representable DateTime |
| `DateTimeMinValue` | BlueprintPure | Minimum representable DateTime |
| `DaysInMonth` | BlueprintPure | Days in given year/month |
| `DaysInYear` | BlueprintPure | Days in given year |
| `IsLeapYear` | BlueprintPure | Leap year check |
| `GetYear` | BlueprintPure | Extract year from DateTime |
| `GetMonth` | BlueprintPure | Extract month from DateTime |
| `GetDay` | BlueprintPure | Extract day from DateTime |
| `GetHour` | BlueprintPure | Extract hour from DateTime |
| `GetMinute` | BlueprintPure | Extract minute from DateTime |
| `GetSecond` | BlueprintPure | Extract second from DateTime |
| `GetMillisecond` | BlueprintPure | Extract millisecond from DateTime |
| `GetDayOfYear` | BlueprintPure | Day number within the year |

### Timespan (Category: Math|Timespan)

| Function | Type | Description |
|----------|------|-------------|
| `MakeTimespan` | BlueprintPure | Creates from days/hours/minutes/seconds |
| `MakeTimespan2` | BlueprintPure | Creates with milliseconds parameter |
| `BreakTimespan` | BlueprintPure | Breaks into components |
| `BreakTimespan2` | BlueprintPure | Breaks with milliseconds |
| `Add_TimespanTimespan` | BlueprintPure | Timespan addition |
| `Subtract_TimespanTimespan` | BlueprintPure | Timespan subtraction |
| `Multiply_TimespanFloat` | BlueprintPure | Scalar multiplication |
| `Divide_TimespanFloat` | BlueprintPure | Scalar division |
| `Add_DateTimeTimespan` | BlueprintPure | DateTime + Timespan |
| `Subtract_DateTimeTimespan` | BlueprintPure | DateTime - Timespan |
| `FromDays` | BlueprintPure | Creates Timespan from days |
| `FromHours` | BlueprintPure | Creates Timespan from hours |
| `FromMinutes` | BlueprintPure | Creates Timespan from minutes |
| `FromSeconds` | BlueprintPure | Creates Timespan from seconds |
| `FromMilliseconds` | BlueprintPure | Creates Timespan from milliseconds |
| `GetTotalDays` | BlueprintPure | Total days in timespan |
| `GetTotalHours` | BlueprintPure | Total hours |
| `GetTotalMinutes` | BlueprintPure | Total minutes |
| `GetTotalSeconds` | BlueprintPure | Total seconds |
| `GetTotalMilliseconds` | BlueprintPure | Total milliseconds |

### LinearColor (Category: Math|Color)

| Function | Type | Description |
|----------|------|-------------|
| `MakeColor` | BlueprintPure | Creates LinearColor from RGBA |
| `BreakColor` | BlueprintPure | Breaks LinearColor into R, G, B, A |
| `HSVToRGB` | BlueprintPure | HSV to RGB conversion |
| `RGBToHSV` | BlueprintPure | RGB to HSV conversion |
| `HSVToRGB_Vector` | BlueprintPure | HSV to RGB (vector form) |
| `RGBToHSV_Vector` | BlueprintPure | RGB to HSV (vector form) |
| `Conv_ColorToLinearColor` | BlueprintPure | FColor to LinearColor |
| `Conv_LinearColorToColor` | BlueprintPure | LinearColor to FColor |
| `Conv_FloatToLinearColor` | BlueprintPure | Float to grayscale LinearColor |
| `Conv_VectorToLinearColor` | BlueprintPure | Vector (RGB) to LinearColor |
| `Conv_LinearColorToVector` | BlueprintPure | LinearColor to Vector (RGB) |
| `CInterpTo` | BlueprintPure | Color interpolation toward target |
| `LinearColor_Red` | BlueprintPure | Returns red constant |
| `LinearColor_Green` | BlueprintPure | Returns green constant |
| `LinearColor_Blue` | BlueprintPure | Returns blue constant |
| `LinearColor_White` | BlueprintPure | Returns white constant |
| `LinearColor_Black` | BlueprintPure | Returns black constant |
| `LinearColor_Yellow` | BlueprintPure | Returns yellow constant |
| `LinearColor_Transparent` | BlueprintPure | Returns transparent constant |
| `LinearColor_Gray` | BlueprintPure | Returns gray constant |
| `LinearColorLerp` | BlueprintPure | Linear color interpolation |
| `LinearColorLerpUsingHSV` | BlueprintPure | Interpolation through HSV space |
| `LinearColor_Desaturated` | BlueprintPure | Returns desaturated color |
| `LinearColor_Distance` | BlueprintPure | Euclidean distance between colors |
| `LinearColor_GetLuminance` | BlueprintPure | Returns luminance value |
| `LinearColor_GetMax` | BlueprintPure | Returns max component value |
| `LinearColor_GetMin` | BlueprintPure | Returns min component value |
| `LinearColor_IsNearEqual` | BlueprintPure | Near-equality check |
| `LinearColor_Quantize` | BlueprintPure | Quantizes to FColor |
| `LinearColor_QuantizeRound` | BlueprintPure | Quantizes with rounding |
| `LinearColor_Set` | BlueprintCallable | Sets RGBA components |
| `LinearColor_SetFromHSV` | BlueprintCallable | Sets from HSV values |
| `LinearColor_SetFromPow22` | BlueprintCallable | Sets from gamma 2.2 encoded |
| `LinearColor_SetFromSRGB` | BlueprintCallable | Sets from sRGB encoded |
| `LinearColor_SetRandomHue` | BlueprintCallable | Sets random hue, full saturation |
| `LinearColor_SetTemperature` | BlueprintCallable | Sets from color temperature (Kelvin) |
| `LinearColor_ToNewOpacity` | BlueprintPure | Returns color with new alpha |
| `LinearColor_ToRGBE` | BlueprintPure | Converts to RGBE color |

### Random with Streams (Category: Math|Random)

| Function | Type | Description |
|----------|------|-------------|
| `MakeRandomStream` | BlueprintPure | Creates RandomStream from seed |
| `BreakRandomStream` | BlueprintPure | Extracts seed from RandomStream |
| `SeedRandomStream` | BlueprintCallable | Seeds an existing stream |
| `ResetRandomStream` | BlueprintCallable | Resets stream to initial seed |
| `RandomBoolFromStream` | BlueprintPure | Random bool from stream |
| `RandomIntegerFromStream` | BlueprintPure | Random int from stream |
| `RandomIntegerInRangeFromStream` | BlueprintPure | Random int in range from stream |
| `RandomFloatFromStream` | BlueprintPure | Random float from stream |
| `RandomFloatInRangeFromStream` | BlueprintPure | Random float in range from stream |
| `RandomUnitVectorFromStream` | BlueprintPure | Random unit vector from stream |
| `RandomRotatorFromStream` | BlueprintPure | Random rotator from stream |
| `RandomPointInBoundingBox` | BlueprintPure | Random point within AABB |
| `RandomUnitVector` | BlueprintPure | Random unit direction vector |
| `RandomRotator` | BlueprintPure | Random rotator (optionally roll) |

### Noise (Category: Math|Random)

| Function | Type | Description |
|----------|------|-------------|
| `PerlinNoise1D` | BlueprintPure | 1D Perlin noise from value |
| `WeightedMovingAverage_Float` | BlueprintPure | Weighted moving average (float) |
| `WeightedMovingAverage_FVector` | BlueprintPure | Weighted moving average (vector) |
| `WeightedMovingAverage_FRotator` | BlueprintPure | Weighted moving average (rotator) |
| `DynamicWeightedMovingAverage_Float` | BlueprintPure | Dynamic weighted moving average |
| `DynamicWeightedMovingAverage_FVector` | BlueprintPure | Dynamic weighted moving average (vec) |
| `DynamicWeightedMovingAverage_FRotator` | BlueprintPure | Dynamic weighted moving average (rot) |

---

## 2. UKismetStringLibrary

**Header**: `Kismet/KismetStringLibrary.h`
**Module**: Engine
**Parent**: UBlueprintFunctionLibrary (BlueprintThreadSafe)
**Blueprint Palette**: Utilities|String

### String Operations

| Function | Type | Description |
|----------|------|-------------|
| `Len` | BlueprintPure | Returns number of characters in the string |
| `IsEmpty` | BlueprintPure | Returns true if the string is empty |
| `Contains` | BlueprintPure | Returns true if string contains specified substring |
| `StartsWith` | BlueprintPure | Tests whether string starts with given prefix |
| `EndsWith` | BlueprintPure | Tests whether string ends with given suffix |
| `MatchesWildcard` | BlueprintPure | Tests against wildcard pattern (* and ?) |
| `FindSubstring` | BlueprintPure | Returns index of first occurrence of substring (-1 if not found) |
| `GetSubstring` | BlueprintPure | Returns substring starting at index for given length |
| `Left` | BlueprintPure | Returns leftmost N characters |
| `Right` | BlueprintPure | Returns rightmost N characters |
| `Mid` | BlueprintPure | Returns substring from start index |
| `LeftPad` | BlueprintPure | Pads string on left to specified length |
| `RightPad` | BlueprintPure | Pads string on right to specified length |
| `LeftChop` | BlueprintPure | Removes N characters from the end |
| `RightChop` | BlueprintPure | Removes N characters from the beginning |
| `Replace` | BlueprintPure | Replaces all occurrences of From with To |
| `Reverse` | BlueprintPure | Returns reversed string |
| `ToUpper` | BlueprintPure | Converts to upper case |
| `ToLower` | BlueprintPure | Converts to lower case |
| `Trim` | BlueprintPure | Removes leading whitespace |
| `TrimTrailing` | BlueprintPure | Removes trailing whitespace |
| `TrimWhitespace` | BlueprintPure | Removes both leading and trailing whitespace |
| `GetCharacterAsNumber` | BlueprintPure | Returns numeric value of character at index |
| `IsNumeric` | BlueprintPure | Returns true if string represents a numeric value |
| `IsAlpha` | BlueprintPure | Returns true if all characters are alphabetic |
| `Crc32` | BlueprintPure | Returns CRC32 hash of the string |
| `ParseIntoArray` | BlueprintPure | Splits string by delimiter into array |
| `JoinStringArray` | BlueprintPure | Concatenates string array with separator |
| `EqualEqual_StriStri` | BlueprintPure | Case-insensitive equality |
| `NotEqual_StriStri` | BlueprintPure | Case-insensitive inequality |
| `EqualEqual_StrStr` | BlueprintPure | Case-sensitive equality |
| `NotEqual_StrStr` | BlueprintPure | Case-sensitive inequality |
| `Less_StrStr` | BlueprintPure | Lexicographic less-than |
| `Greater_StrStr` | BlueprintPure | Lexicographic greater-than |
| `LessEqual_StrStr` | BlueprintPure | Lexicographic less-or-equal |
| `GreaterEqual_StrStr` | BlueprintPure | Lexicographic greater-or-equal |
| `Concat_StrStr` | BlueprintPure | Concatenates two strings |
| `TimeSecondsToString` | BlueprintPure | Converts seconds to formatted time string |

### String Conversions

| Function | Type | Description |
|----------|------|-------------|
| `Conv_IntToString` | BlueprintPure | Integer to string |
| `Conv_Int64ToString` | BlueprintPure | Int64 to string |
| `Conv_FloatToString` | BlueprintPure | Float to string |
| `Conv_ByteToString` | BlueprintPure | Byte to string |
| `Conv_BoolToString` | BlueprintPure | Bool to string ("true"/"false") |
| `Conv_VectorToString` | BlueprintPure | Vector to string "X=... Y=... Z=..." |
| `Conv_Vector2DToString` | BlueprintPure | Vector2D to string |
| `Conv_IntVectorToString` | BlueprintPure | IntVector to string |
| `Conv_RotatorToString` | BlueprintPure | Rotator to string |
| `Conv_TransformToString` | BlueprintPure | Transform to string |
| `Conv_ObjectToString` | BlueprintPure | Object to string (path name) |
| `Conv_ColorToString` | BlueprintPure | Color to string |
| `Conv_NameToString` | BlueprintPure | FName to FString |
| `Conv_StringToName` | BlueprintPure | FString to FName |
| `Conv_StringToInt` | BlueprintPure | String to integer |
| `Conv_StringToFloat` | BlueprintPure | String to float |
| `Conv_StringToVector` | BlueprintPure | Parses "X=... Y=... Z=..." to vector |
| `Conv_StringToVector2D` | BlueprintPure | Parses to Vector2D |
| `Conv_StringToRotator` | BlueprintPure | Parses to rotator |
| `Conv_StringToColor` | BlueprintPure | Parses to color |

### Build String Helpers

| Function | Type | Description |
|----------|------|-------------|
| `BuildString_Float` | BlueprintPure | Constructs string from prefix + float + suffix |
| `BuildString_Int` | BlueprintPure | Constructs string from prefix + int + suffix |
| `BuildString_Bool` | BlueprintPure | Constructs string from prefix + bool + suffix |
| `BuildString_Vector` | BlueprintPure | Constructs string from prefix + vector + suffix |
| `BuildString_Vector2D` | BlueprintPure | Constructs string from prefix + vec2d + suffix |
| `BuildString_Rotator` | BlueprintPure | Constructs string from prefix + rotator + suffix |
| `BuildString_Object` | BlueprintPure | Constructs string from prefix + object + suffix |
| `BuildString_Name` | BlueprintPure | Constructs string from prefix + name + suffix |
| `BuildString_Color` | BlueprintPure | Constructs string from prefix + color + suffix |
| `BuildString_IntVector` | BlueprintPure | Constructs string from prefix + intvec + suffix |

---

## 3. UKismetSystemLibrary

**Header**: `Kismet/KismetSystemLibrary.h`
**Module**: Engine
**Parent**: UBlueprintFunctionLibrary
**Blueprint Palette**: Utilities (various sub-categories)

### Debug Drawing (Category: Rendering|Debug)

| Function | Type | Description |
|----------|------|-------------|
| `DrawDebugLine` | BlueprintCallable | Draws a debug line in world space |
| `DrawDebugCircle` | BlueprintCallable | Draws a debug circle |
| `DrawDebugArrow` | BlueprintCallable | Draws a debug arrow |
| `DrawDebugBox` | BlueprintCallable | Draws a debug box |
| `DrawDebugSphere` | BlueprintCallable | Draws a debug sphere |
| `DrawDebugCapsule` | BlueprintCallable | Draws a debug capsule |
| `DrawDebugCylinder` | BlueprintCallable | Draws a debug cylinder |
| `DrawDebugCone` | BlueprintCallable | Draws a debug cone (radians) |
| `DrawDebugConeInDegrees` | BlueprintCallable | Draws a debug cone (degrees) |
| `DrawDebugPoint` | BlueprintCallable | Draws a debug point |
| `DrawDebugString` | BlueprintCallable | Draws debug text at 3D location |
| `DrawDebugPlane` | BlueprintCallable | Draws a debug plane |
| `DrawDebugCamera` | BlueprintCallable | Draws a debug camera shape |
| `DrawDebugFrustum` | BlueprintCallable | Draws a debug camera frustum |
| `DrawDebugCoordinateSystem` | BlueprintCallable | Draws XYZ coordinate axes |
| `DrawDebugFloatHistoryLocation` | BlueprintCallable | Draws 2D histogram at world location |
| `DrawDebugFloatHistoryTransform` | BlueprintCallable | Draws 2D histogram with transform |
| `FlushDebugStrings` | BlueprintCallable | Removes all active debug strings |
| `FlushPersistentDebugLines` | BlueprintCallable | Clears all persistent debug lines/shapes |

### Line Traces (Category: Collision)

| Function | Type | Description |
|----------|------|-------------|
| `LineTraceSingle` | BlueprintCallable | Single line trace by trace channel |
| `LineTraceMulti` | BlueprintCallable | Multi-hit line trace by trace channel |
| `LineTraceSingleByProfile` | BlueprintCallable | Single line trace by collision profile |
| `LineTraceMultiByProfile` | BlueprintCallable | Multi-hit line trace by profile |
| `LineTraceSingleForObjects` | BlueprintCallable | Single line trace for object types |
| `LineTraceMultiForObjects` | BlueprintCallable | Multi-hit line trace for objects |

### Box Traces (Category: Collision)

| Function | Type | Description |
|----------|------|-------------|
| `BoxTraceSingle` | BlueprintCallable | Single box sweep by trace channel |
| `BoxTraceMulti` | BlueprintCallable | Multi-hit box sweep |
| `BoxTraceSingleByProfile` | BlueprintCallable | Single box sweep by collision profile |
| `BoxTraceMultiByProfile` | BlueprintCallable | Multi-hit box sweep by profile |
| `BoxTraceSingleForObjects` | BlueprintCallable | Single box sweep for object types |
| `BoxTraceMultiForObjects` | BlueprintCallable | Multi-hit box sweep for objects |

### Sphere Traces (Category: Collision)

| Function | Type | Description |
|----------|------|-------------|
| `SphereTraceSingle` | BlueprintCallable | Single sphere sweep |
| `SphereTraceMulti` | BlueprintCallable | Multi-hit sphere sweep |
| `SphereTraceSingleByProfile` | BlueprintCallable | Single sphere sweep by profile |
| `SphereTraceMultiByProfile` | BlueprintCallable | Multi-hit sphere sweep by profile |
| `SphereTraceSingleForObjects` | BlueprintCallable | Single sphere sweep for objects |
| `SphereTraceMultiForObjects` | BlueprintCallable | Multi-hit sphere sweep for objects |

### Capsule Traces (Category: Collision)

| Function | Type | Description |
|----------|------|-------------|
| `CapsuleTraceSingle` | BlueprintCallable | Single capsule sweep |
| `CapsuleTraceMulti` | BlueprintCallable | Multi-hit capsule sweep |
| `CapsuleTraceSingleByProfile` | BlueprintCallable | Single capsule sweep by profile |
| `CapsuleTraceMultiByProfile` | BlueprintCallable | Multi-hit capsule sweep by profile |
| `CapsuleTraceSingleForObjects` | BlueprintCallable | Single capsule sweep for objects |
| `CapsuleTraceMultiForObjects` | BlueprintCallable | Multi-hit capsule sweep for objects |

### Overlap Tests (Category: Collision)

| Function | Type | Description |
|----------|------|-------------|
| `BoxOverlapActors` | BlueprintCallable | Returns actors overlapping box |
| `BoxOverlapComponents` | BlueprintCallable | Returns components overlapping box |
| `SphereOverlapActors` | BlueprintCallable | Returns actors overlapping sphere |
| `SphereOverlapComponents` | BlueprintCallable | Returns components overlapping sphere |
| `CapsuleOverlapActors` | BlueprintCallable | Returns actors overlapping capsule |
| `CapsuleOverlapComponents` | BlueprintCallable | Returns components overlapping capsule |
| `ComponentOverlapActors` | BlueprintCallable | Returns actors overlapping component |
| `ComponentOverlapComponents` | BlueprintCallable | Returns components overlapping component |

### Print/Log (Category: Development)

| Function | Type | Description |
|----------|------|-------------|
| `PrintString` | BlueprintCallable | Prints string to log and/or screen |
| `PrintText` | BlueprintCallable | Prints FText to log and/or screen |
| `PrintWarning` | BlueprintCallable | Prints warning to log |

### Timer Functions (Category: Utilities|Time)

| Function | Type | Description |
|----------|------|-------------|
| `K2_SetTimer` | BlueprintCallable | Sets timer by delegate (Blueprint: "Set Timer by Event") |
| `K2_SetTimerForNextTick` | BlueprintCallable | Fires delegate next tick |
| `K2_SetTimerByFunctionName` | BlueprintCallable | Sets timer by function name |
| `K2_ClearTimer` | BlueprintCallable | Clears timer by function name |
| `K2_ClearTimerHandle` | BlueprintCallable | Clears timer by handle |
| `K2_ClearAndInvalidateTimerHandle` | BlueprintCallable | Clears and invalidates timer handle |
| `K2_PauseTimer` | BlueprintCallable | Pauses timer |
| `K2_UnPauseTimer` | BlueprintCallable | Unpauses timer |
| `K2_IsTimerActive` | BlueprintPure | Checks if timer is running |
| `K2_IsTimerPaused` | BlueprintPure | Checks if timer is paused |
| `K2_TimerExists` | BlueprintPure | Checks if timer exists |
| `K2_GetTimerElapsedTime` | BlueprintPure | Returns elapsed time on timer |
| `K2_GetTimerRemainingTime` | BlueprintPure | Returns remaining time on timer |

### Latent Actions (Category: Utilities|FlowControl)

| Function | Type | Description |
|----------|------|-------------|
| `Delay` | BlueprintCallable | Latent delay by seconds |
| `RetriggerableDelay` | BlueprintCallable | Retriggerable latent delay |
| `MoveComponentTo` | BlueprintCallable | Latent move component to location/rotation |

### System Info (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `GetPlatformName` | BlueprintPure | Returns platform name ("Windows", "Mac", etc.) |
| `GetEngineVersion` | BlueprintPure | Returns engine version string |
| `GetGameBundleId` | BlueprintPure | Returns application bundle identifier |
| `GetProjectDirectory` | BlueprintPure | Returns project root directory |
| `GetProjectContentDirectory` | BlueprintPure | Returns Content folder path |
| `GetProjectSavedDirectory` | BlueprintPure | Returns Saved folder path |
| `GetDeviceId` | BlueprintPure | Returns platform-specific device ID |
| `GetUniqueDeviceId` | BlueprintPure | Returns globally unique device ID |
| `GetCommandLine` | BlueprintPure | Returns process command line |
| `HasLaunchOption` | BlueprintPure | Checks if launch option was specified |
| `GetDefaultLanguage` | BlueprintPure | Returns default language |
| `GetDefaultLocale` | BlueprintPure | Returns default locale |
| `IsStandalone` | BlueprintPure | Returns true if running standalone |
| `IsDedicatedServer` | BlueprintPure | Returns true if dedicated server |
| `IsServer` | BlueprintPure | Returns true if server (listen or dedicated) |
| `IsPackagedForDistribution` | BlueprintPure | True if packaged build |

### Console Variables (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `GetConsoleVariableBoolValue` | BlueprintCallable | Gets bool console variable value |
| `GetConsoleVariableIntValue` | BlueprintCallable | Gets int console variable value |
| `GetConsoleVariableFloatValue` | BlueprintCallable | Gets float console variable value |
| `SetConsoleVariableBool` | BlueprintCallable | Sets bool console variable |
| `SetConsoleVariableInt` | BlueprintCallable | Sets int console variable |
| `SetConsoleVariableFloat` | BlueprintCallable | Sets float console variable |
| `ExecuteConsoleCommand` | BlueprintCallable | Executes console command string |

### Object/Class Utilities (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `IsValid` | BlueprintPure | Returns true if object reference is valid |
| `IsValidClass` | BlueprintPure | Returns true if class reference is valid |
| `GetObjectName` | BlueprintPure | Returns object name |
| `GetDisplayName` | BlueprintPure | Returns display name |
| `GetClassDisplayName` | BlueprintPure | Returns class display name |
| `GetPathName` | BlueprintPure | Returns full path name |
| `GetObjectClass` | BlueprintPure | Returns class of object |
| `DoesImplementInterface` | BlueprintCallable | Checks if object implements interface |
| `GetOuterObject` | BlueprintPure | Returns outer object |

### File/Path Utilities (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `ConvertToAbsolutePath` | BlueprintPure | Converts to absolute file path |
| `ConvertToRelativePath` | BlueprintPure | Converts to relative file path |
| `NormalizeFilename` | BlueprintPure | Normalizes file path |
| `CanLaunchURL` | BlueprintPure | Checks if URL can be opened |
| `LaunchURL` | BlueprintCallable | Opens URL in default browser |

### Rendering (Category: Rendering)

| Function | Type | Description |
|----------|------|-------------|
| `GetConvenientWindowedResolutions` | BlueprintCallable | Returns available windowed resolutions |
| `GetSupportedFullscreenResolutions` | BlueprintCallable | Returns supported fullscreen resolutions |
| `SetEnableWorldRendering` | BlueprintCallable | Enables/disables world rendering |
| `GetEnableWorldRendering` | BlueprintPure | Returns world rendering state |

### Primary Asset ID (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `MakePrimaryAssetIdFromString` | BlueprintPure | Creates PrimaryAssetId from string |
| `Conv_PrimaryAssetIdToString` | BlueprintPure | PrimaryAssetId to string |
| `Conv_PrimaryAssetTypeToString` | BlueprintPure | PrimaryAssetType to string |
| `GetPrimaryAssetIdFromObject` | BlueprintPure | Gets PrimaryAssetId from object |
| `GetClassFromPrimaryAssetId` | BlueprintCallable | Gets class from asset ID |
| `GetSoftClassReferenceFromPrimaryAssetId` | BlueprintCallable | Gets soft class ref from ID |
| `GetSoftObjectReferenceFromPrimaryAssetId` | BlueprintCallable | Gets soft object ref from ID |
| `EqualEqual_PrimaryAssetId` | BlueprintPure | Compares asset IDs |
| `EqualEqual_PrimaryAssetType` | BlueprintPure | Compares asset types |
| `IsValidPrimaryAssetId` | BlueprintPure | Validates asset ID |
| `IsValidPrimaryAssetType` | BlueprintPure | Validates asset type |

### Soft References (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `Conv_SoftObjectReferenceToString` | BlueprintPure | Soft reference to string path |
| `Conv_SoftObjectReferenceToObject` | BlueprintPure | Resolves soft reference to object |
| `Conv_SoftClassReferenceToString` | BlueprintPure | Soft class ref to string |
| `Conv_SoftClassReferenceToClass` | BlueprintPure | Resolves soft class reference |
| `Conv_ObjectToSoftObjectReference` | BlueprintPure | Object to soft reference |
| `Conv_ClassToSoftClassReference` | BlueprintPure | Class to soft class reference |
| `EqualEqual_SoftObjectReference` | BlueprintPure | Soft reference equality |
| `EqualEqual_SoftClassReference` | BlueprintPure | Soft class reference equality |
| `IsValidSoftObjectReference` | BlueprintPure | Validates soft reference |
| `IsValidSoftClassReference` | BlueprintPure | Validates soft class reference |
| `LoadAsset` | BlueprintCallable | Latent async load of soft object ref |
| `LoadClassAsset` | BlueprintCallable | Latent async load of soft class ref |

### Garbage Collection (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `CollectGarbage` | BlueprintCallable | Forces garbage collection |

### Undo/Transactions (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `BeginTransaction` | BlueprintCallable | Begins undo transaction |
| `EndTransaction` | BlueprintCallable | Ends undo transaction |
| `CancelTransaction` | BlueprintCallable | Cancels undo transaction |
| `TransactObject` | BlueprintCallable | Records object for undo |
| `CreateCopyForUndoBuffer` | BlueprintCallable | Copies to undo buffer |

---

## 4. UKismetArrayLibrary

**Header**: `Kismet/KismetArrayLibrary.h`
**Module**: Engine
**Parent**: UBlueprintFunctionLibrary (BlueprintThreadSafe)
**Blueprint Palette**: Utilities|Array

NOTE: Most functions use CustomThunk (wildcard generic arrays). The Blueprint node names differ from C++ names.

| Function | Type | Description |
|----------|------|-------------|
| `Array_Add` | BlueprintCallable | Adds item to end of array, returns new index |
| `Array_AddUnique` | BlueprintCallable | Adds item only if not already present |
| `Array_Append` | BlueprintCallable | Appends second array to first |
| `Array_Insert` | BlueprintCallable | Inserts item at given index |
| `Array_Remove` | BlueprintCallable | Removes item at given index |
| `Array_RemoveItem` | BlueprintCallable | Removes first occurrence of item |
| `Array_Clear` | BlueprintCallable | Removes all items from array |
| `Array_Resize` | BlueprintCallable | Resizes array to given length |
| `Array_Get` | BlueprintPure | Returns copy of item at index |
| `Array_Set` | BlueprintCallable | Sets item at index |
| `Array_Find` | BlueprintPure | Returns index of first occurrence (-1 if not found) |
| `Array_Contains` | BlueprintPure | Returns true if array contains item |
| `Array_Length` | BlueprintPure | Returns number of items in array |
| `Array_LastIndex` | BlueprintPure | Returns last valid index (length - 1) |
| `GetLastIndex` | BlueprintPure | Alternative name for last valid index |
| `Array_IsValidIndex` | BlueprintPure | Checks if index is within bounds |
| `Array_Shuffle` | BlueprintCallable | Randomizes element order |
| `Array_Random` | BlueprintPure | Returns random element and its index |
| `Array_RandomFromStream` | BlueprintPure | Random element using RandomStream |
| `Array_Reverse` | BlueprintCallable | Reverses element order |
| `Array_Swap` | BlueprintCallable | Swaps elements at two indices |
| `Array_Identical` | BlueprintPure | Checks if two arrays have identical contents |
| `FilterArray` | BlueprintCallable | Filters actor array by class type |
| `SetArrayPropertyByName` | BlueprintCallable | Sets array property by name via reflection |

---

## 5. UGameplayStatics

**Header**: `Kismet/GameplayStatics.h`
**Module**: Engine
**Parent**: UBlueprintFunctionLibrary
**Blueprint Palette**: Game (various sub-categories)

### Audio -- Sound Playback (Category: Audio)

| Function | Type | Description |
|----------|------|-------------|
| `PlaySound2D` | BlueprintCallable | Plays non-spatial audio (UI sounds) |
| `PlaySoundAtLocation` | BlueprintCallable | Plays sound at world position |
| `SpawnSoundAtLocation` | BlueprintCallable | Spawns audio component at location (returns component) |
| `SpawnSoundAttached` | BlueprintCallable | Spawns audio component attached to component |
| `CreateSound2D` | BlueprintCallable | Creates 2D audio component without auto-play |
| `PlayDialogue2D` | BlueprintCallable | Plays dialogue without spatial attenuation |
| `PlayDialogueAtLocation` | BlueprintCallable | Plays dialogue at world location |
| `SpawnDialogue2D` | BlueprintCallable | Spawns 2D dialogue component |
| `SpawnDialogueAtLocation` | BlueprintCallable | Spawns dialogue at location |
| `SpawnDialogueAttached` | BlueprintCallable | Spawns dialogue attached to component |
| `PrimeSound` | BlueprintCallable | Caches initial streamed audio chunk |
| `PrimeAllSoundsInSoundClass` | BlueprintCallable | Primes all sounds in a sound class |

### Audio -- Sound Mix & Modulation (Category: Audio)

| Function | Type | Description |
|----------|------|-------------|
| `SetBaseSoundMix` | BlueprintCallable | Sets base sound mix for EQ |
| `PushSoundMixModifier` | BlueprintCallable | Pushes sound mix modifier onto stack |
| `PopSoundMixModifier` | BlueprintCallable | Pops sound mix modifier from stack |
| `ClearSoundMixModifiers` | BlueprintCallable | Clears all sound mix modifiers |
| `SetSoundMixClassOverride` | BlueprintCallable | Overrides sound class in a mix |
| `ClearSoundMixClassOverride` | BlueprintCallable | Clears sound class override |
| `SetGlobalPitchModulation` | BlueprintCallable | Global pitch scalar for non-UI sounds |
| `SetGlobalListenerFocusParameters` | BlueprintCallable | Scales focus behavior by azimuth |
| `GetMaxAudioChannelCount` | BlueprintPure | Returns current audio voice count |
| `AreSubtitlesEnabled` | BlueprintPure | Returns subtitle enabled state |

### Audio -- Reverb (Category: Audio)

| Function | Type | Description |
|----------|------|-------------|
| `ActivateReverbEffect` | BlueprintCallable | Activates reverb without audio volume |
| `DeactivateReverbEffect` | BlueprintCallable | Deactivates reverb effect |
| `GetCurrentReverbEffect` | BlueprintCallable | Returns highest priority active reverb |

### Audio -- Listener (Category: Audio)

| Function | Type | Description |
|----------|------|-------------|
| `AreAnyListenersWithinRange` | BlueprintCallable | Checks if any listeners within distance |
| `GetClosestListenerLocation` | BlueprintCallable | Finds nearest listener position |
| `SetSubtitlesEnabled` | BlueprintCallable | Enables/disables subtitles |

### Damage (Category: Game|Damage)

| Function | Type | Description |
|----------|------|-------------|
| `ApplyDamage` | BlueprintCallable | Applies generic damage to actor |
| `ApplyPointDamage` | BlueprintCallable | Applies damage with hit direction/location |
| `ApplyRadialDamage` | BlueprintCallable | Applies damage to all actors in sphere |
| `ApplyRadialDamageWithFalloff` | BlueprintCallable | Radial damage with inner/outer radius falloff |

### Player & Controller (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `GetPlayerController` | BlueprintPure | Returns player controller at index |
| `GetPlayerControllerFromID` | BlueprintPure | Gets controller by physical controller ID |
| `GetPlayerControllerID` | BlueprintPure | Gets physical ID from controller |
| `SetPlayerControllerID` | BlueprintCallable | Assigns physical controller ID |
| `GetNumPlayerControllers` | BlueprintPure | Total player controllers |
| `GetNumLocalPlayerControllers` | BlueprintPure | Local player controller count |
| `GetPlayerPawn` | BlueprintPure | Returns player's pawn |
| `GetPlayerCharacter` | BlueprintPure | Returns player's character |
| `GetPlayerCameraManager` | BlueprintPure | Returns camera manager |
| `GetPlayerState` | BlueprintPure | Returns player state by index |
| `GetPlayerStateFromUniqueNetId` | BlueprintPure | Player state by network ID |
| `GetNumPlayerStates` | BlueprintPure | Active player state count |
| `CreatePlayer` | BlueprintCallable | Creates new local player |
| `RemovePlayer` | BlueprintCallable | Removes local player |

### Actor Queries (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `GetActorOfClass` | BlueprintCallable | Finds first actor of class (SLOW) |
| `GetAllActorsOfClass` | BlueprintCallable | Finds all actors of class |
| `GetAllActorsWithTag` | BlueprintCallable | Finds all actors with tag |
| `GetAllActorsOfClassWithTag` | BlueprintCallable | Finds actors matching class AND tag |
| `GetAllActorsWithInterface` | BlueprintCallable | Finds actors implementing interface |
| `FindNearestActor` | BlueprintPure | Returns closest actor from array |
| `GetActorArrayAverageLocation` | BlueprintPure | Centroid of actor array |
| `GetActorArrayBounds` | BlueprintCallable | Bounding box of actor collection |

### Projectile Prediction (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `BlueprintPredictProjectilePath_Advanced` | BlueprintCallable | Full projectile prediction with collision |
| `BlueprintPredictProjectilePath_ByObjectType` | BlueprintCallable | Prediction by object types |
| `BlueprintPredictProjectilePath_ByTraceChannel` | BlueprintCallable | Prediction by trace channel |
| `Blueprint_PredictProjectilePath_ByTraceChannel` | BlueprintCallable | Prediction by trace (newer overload) |
| `SuggestProjectileVelocity` | BlueprintCallable | Calculates launch velocity to hit target |

### Level & World (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `GetCurrentLevelName` | BlueprintPure | Returns name of current level |
| `OpenLevel` | BlueprintCallable | Travels to another level |
| `OpenLevelBySoftObjectPtr` | BlueprintCallable | Level travel via soft reference |
| `LoadStreamLevel` | BlueprintCallable | Async streams in a level |
| `LoadStreamLevelBySoftObjectPtr` | BlueprintCallable | Streams level via soft reference |
| `UnloadStreamLevel` | BlueprintCallable | Unloads streamed level |
| `UnloadStreamLevelBySoftObjectPtr` | BlueprintCallable | Unloads via soft reference |
| `GetStreamingLevel` | BlueprintPure | Returns streaming level object |
| `FlushLevelStreaming` | BlueprintCallable | Blocks until streaming completes |
| `CancelAsyncLoading` | BlueprintCallable | Cancels queued streaming |
| `GetWorldOriginLocation` | BlueprintPure | Returns world origin position |
| `SetWorldOriginLocation` | BlueprintCallable | Sets world origin (origin rebasing) |
| `RebaseZeroOriginOntoLocal` | BlueprintPure | Converts origin-based to local coords |
| `RebaseLocalOriginOntoZero` | BlueprintPure | Converts local to origin-based coords |

### Time (Category: Utilities|Time)

| Function | Type | Description |
|----------|------|-------------|
| `GetTimeSeconds` | BlueprintPure | Game time (affected by pause+dilation) |
| `GetUnpausedTimeSeconds` | BlueprintPure | Time not affected by pause |
| `GetRealTimeSeconds` | BlueprintPure | Real-time (not pause/dilation affected) |
| `GetAccurateRealTime` | BlueprintPure | Precise real time at call moment |
| `GetAudioTimeSeconds` | BlueprintPure | Audio-synced time |
| `GetWorldDeltaSeconds` | BlueprintPure | Frame delta time with dilation |
| `GetGlobalTimeDilation` | BlueprintPure | Current time dilation value |
| `SetGlobalTimeDilation` | BlueprintCallable | Sets global time dilation |

### Game State (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `GetGameMode` | BlueprintPure | Returns current GameMode |
| `GetGameState` | BlueprintPure | Returns current GameState |
| `GetGameInstance` | BlueprintPure | Returns the GameInstance |
| `SetGamePaused` | BlueprintCallable | Pauses/unpauses the game |
| `IsGamePaused` | BlueprintPure | Returns pause state |
| `GetObjectClass` | BlueprintPure | Returns class of object |

### Camera & Viewport (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `ProjectWorldToScreen` | BlueprintPure | 3D world to 2D screen |
| `DeprojectScreenToWorld` | BlueprintPure | 2D screen to 3D world |
| `GetViewProjectionMatrix` | BlueprintPure | Returns view/projection matrices |
| `GetViewportMouseCaptureMode` | BlueprintPure | Returns mouse capture mode |
| `PlayWorldCameraShake` | BlueprintCallable | Plays camera shake for nearby players |

### Save Game (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `CreateSaveGameObject` | BlueprintCallable | Creates new SaveGame instance |
| `SaveGameToSlot` | BlueprintCallable | Saves to named slot |
| `LoadGameFromSlot` | BlueprintCallable | Loads from named slot |
| `DeleteGameInSlot` | BlueprintCallable | Deletes save file |
| `DoesSaveGameExist` | BlueprintPure | Checks if save slot exists |
| `AsyncSaveGameToSlot` | BlueprintCallable | Async save game |
| `AsyncLoadGameFromSlot` | BlueprintCallable | Async load game |

### Spawning (Category: Game)

| Function | Type | Description |
|----------|------|-------------|
| `BeginDeferredActorSpawnFromClass` | BlueprintCallable | Deferred spawn (call FinishSpawning later) |
| `FinishSpawningActor` | BlueprintCallable | Finishes deferred spawn |
| `SpawnObject` | BlueprintCallable | Spawns non-actor UObject |
| `BeginSpawningActorFromBlueprint` | BlueprintCallable | Begins spawning from Blueprint class |
| `BeginSpawningActorFromClass` | BlueprintCallable | Begins spawning from class |

### Particle Effects (Category: Effects)

| Function | Type | Description |
|----------|------|-------------|
| `SpawnEmitterAtLocation` | BlueprintCallable | Spawns particle effect at location |
| `SpawnEmitterAttached` | BlueprintCallable | Spawns particle attached to component |

### Decals (Category: Rendering|Components|Decal)

| Function | Type | Description |
|----------|------|-------------|
| `SpawnDecalAtLocation` | BlueprintCallable | Spawns decal at location |
| `SpawnDecalAttached` | BlueprintCallable | Spawns decal attached to component |

### Force Feedback / Haptics (Category: Game|ForceFeedback)

| Function | Type | Description |
|----------|------|-------------|
| `SpawnForceFeedbackAtLocation` | BlueprintCallable | Spawns force feedback at location |
| `SpawnForceFeedbackAttached` | BlueprintCallable | Spawns force feedback on component |
| `PlayForceFeedback` | BlueprintCallable | Plays force feedback effect |

### Option Parsing (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `ParseOption` | BlueprintPure | Extracts value from "key=value" string |
| `HasOption` | BlueprintPure | Checks if key exists in option string |
| `GetKeyValue` | BlueprintPure | Splits key=value pair |
| `GetIntOption` | BlueprintPure | Extracts int from option string |

### Platform / Misc (Category: Utilities)

| Function | Type | Description |
|----------|------|-------------|
| `GetPlatformName` | BlueprintPure | Returns platform identifier |
| `EnableLiveStreaming` | BlueprintCallable | Toggles DVR streaming |
| `AnnounceAccessibleString` | BlueprintCallable | Announces text via accessibility system |
| `SetForceDisableSplitscreen` | BlueprintCallable | Force disable/enable splitscreen |
| `IsSplitscreenForceDisabled` | BlueprintPure | Checks splitscreen state |
| `SetEnableWorldRendering` | BlueprintCallable | Toggles world rendering |
| `GetEnableWorldRendering` | BlueprintPure | Returns world rendering state |
| `GrassOverlappingSphereCount` | BlueprintCallable | Counts grass instances in sphere |
| `FindCollisionUV` | BlueprintCallable | Gets UV coordinates from hit result |

---

## Audio-Relevant Functions Summary (for UE Audio MCP)

Functions particularly relevant to audio/game audio systems:

### From UGameplayStatics (Audio)
- `PlaySound2D` / `PlaySoundAtLocation` / `SpawnSoundAttached` -- Core sound playback
- `CreateSound2D` -- Audio component creation without auto-play
- `PrimeSound` / `PrimeAllSoundsInSoundClass` -- Preloading for performance
- `ActivateReverbEffect` / `DeactivateReverbEffect` -- Programmatic reverb
- `SetBaseSoundMix` / `PushSoundMixModifier` / `PopSoundMixModifier` -- Sound mix control
- `SetGlobalPitchModulation` -- Global pitch scaling
- `SetGlobalListenerFocusParameters` -- Listener focus behavior
- `AreAnyListenersWithinRange` / `GetClosestListenerLocation` -- Listener proximity
- `GetAudioTimeSeconds` / `GetMaxAudioChannelCount` -- Audio system queries

### From UKismetMathLibrary (DSP/Procedural Audio)
- `MapRangeClamped` / `MapRangeUnclamped` -- RTPC parameter mapping
- `FClamp` / `Lerp` / `FInterpTo` / `FInterpTo_Constant` -- Smooth parameter transitions
- `Sin` / `Cos` / `PerlinNoise1D` -- Oscillation and noise for modulation
- `MakePulsatingValue` -- Ready-made LFO-like output
- `RandomFloatInRange` -- Randomization for variation
- `VInterpTo` / `VectorSpringInterp` -- Spatial audio position smoothing
- `Vector_Distance` / `Vector_Distance2D` -- Distance-based attenuation
- `FindLookAtRotation` -- Listener-to-source direction for spatialization

---

<meta>
research-date: 2026-02-06
confidence: high (function names verified from official Epic source code mirrors, Python API, and documentation)
version-checked: UE 5.4-5.7 (functions stable across versions, Int64 added in 5.0+)
sources-count: 15+
note: UKismetMathLibrary has 300+ functions total. This document captures all major categories. Some niche overloads (Matrix operations, FBox, FBox2D) omitted for brevity.
</meta>
