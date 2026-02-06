# UE5 Blueprint Node Reference - Core Systems

_Generated: 2026-02-06 | Sources: 40+ official Epic docs pages_

<key-points>
- 16 major Blueprint systems documented with exact node names and C++ classes
- All nodes verified against UE 5.7 official documentation (dev.epicgames.com)
- Includes Enhanced Input, Save Game, Collision/Traces, Materials, Subsystems, DataTables, Struct operations
- NEW: Math Comparison, Interpolation, Random, Damage, Mesh/Static Mesh, Audio-Adjacent, Viewport/Screen, Platform Detection, EQS
- 400+ total Blueprint nodes catalogued with C++ class mappings
</key-points>

---

## 1. Enhanced Input System

### C++ Classes

| Class | Description |
|-------|-------------|
| `UEnhancedInputComponent` | Transient component enabling actors to bind enhanced actions to delegates |
| `UInputAction` | Data asset representing a user action (e.g., "Crouch", "Fire Weapon") |
| `UInputMappingContext` | Collection of key-to-action mappings for a specific input context |
| `UEnhancedInputLocalPlayerSubsystem` | Per-player subsystem managing mapping contexts and input processing |
| `UEnhancedPlayerInput` | Enhanced version of UPlayerInput with modifier/trigger pipeline |
| `UInputModifier` | Base class for input value pre-processors |
| `UInputTrigger` | Base class for input trigger evaluation |
| `UEnhancedInputPlatformData` | Platform-specific input configuration data asset |

### Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Add Mapping Context** | `UEnhancedInputLocalPlayerSubsystem::AddMappingContext()` | Registers an Input Mapping Context with priority |
| **Remove Mapping Context** | `UEnhancedInputLocalPlayerSubsystem::RemoveMappingContext()` | Unregisters an Input Mapping Context |
| **Get Bound Action Value** | `UEnhancedInputComponent::GetBoundActionValue()` | Returns current FInputActionValue for a bound action (BlueprintCallable) |
| **Inject Input for Action** | `InjectInputForAction()` | Programmatically inject input for testing/AI |

### Action Binding (C++ - SetupPlayerInputComponent)

```cpp
// Primary binding pattern - called in SetupPlayerInputComponent
EnhancedInputComponent->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyCharacter::Move);
EnhancedInputComponent->BindAction(JumpAction, ETriggerEvent::Started, this, &AMyCharacter::Jump);
EnhancedInputComponent->BindActionValue(LookAction);  // Poll-based value binding
```

### UEnhancedInputComponent Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `BindAction` | Multiple overloads (UFUNCTION, delegate, value, instance) | Binds action to callback with ETriggerEvent filter |
| `BindActionValue` | `FEnhancedInputActionValueBinding& BindActionValue(const UInputAction*)` | Binds for polling via GetBoundActionValue |
| `BindActionInstanceLambda` | Lambda variant with FInputActionInstance data | Lambda binding with full instance data |
| `BindActionValueLambda` | Lambda variant for value events | Lambda binding for input value |
| `GetBoundActionValue` | `FInputActionValue GetBoundActionValue(const UInputAction*)` | BlueprintCallable - pull current action value |
| `ClearActionBindings` | `virtual void ClearActionBindings()` | Removes all action bindings |
| `ClearActionEventBindings` | `void ClearActionEventBindings()` | Removes all event bindings |
| `ClearActionValueBindings` | `void ClearActionValueBindings()` | Removes all value bindings |
| `ClearBindingsForObject` | `virtual void ClearBindingsForObject(UObject*)` | Clears delegates for a specific UObject |
| `RemoveActionEventBinding` | `bool RemoveActionEventBinding(int32 BindingIndex)` | Remove by index |
| `RemoveBinding` | `bool RemoveBinding(const FInputBindingHandle&)` | Remove by handle |
| `RemoveBindingByHandle` | `bool RemoveBindingByHandle(uint32 Handle)` | Remove by unique handle ID |
| `HasBindings` | `virtual bool HasBindings()` | Check if any bindings exist |

### ETriggerEvent States

| State | Description |
|-------|-------------|
| `ETriggerEvent::Started` | Action evaluation began (first frame of activation) |
| `ETriggerEvent::Ongoing` | Action is being evaluated (held, charging, etc.) |
| `ETriggerEvent::Triggered` | Action completed trigger evaluation (primary fire event) |
| `ETriggerEvent::Completed` | Action ended after being triggered |
| `ETriggerEvent::Canceled` | Action was canceled before triggering |

### Input Action Value Types

| Type | C++ | Value |
|------|-----|-------|
| Digital/Bool | `bool` | true/false |
| Axis1D | `float` | Single axis value |
| Axis2D | `FVector2D` | Two-axis value (e.g., mouse/stick) |
| Axis3D | `FVector` | Three-axis value |

### Input Trigger Classes

| C++ Class | Blueprint Name | Description |
|-----------|---------------|-------------|
| `UInputTriggerDown` | Down | Fires while input is actuated (default implicit trigger) |
| `UInputTriggerPressed` | Pressed | Fires once on initial press |
| `UInputTriggerReleased` | Released | Fires once on release after actuation |
| `UInputTriggerHold` | Hold | Fires once after input held for HoldTimeThreshold seconds |
| `UInputTriggerHoldAndRelease` | Hold And Release | Fires on release after held for HoldTimeThreshold seconds |
| `UInputTriggerTap` | Tap | Fires if pressed and released within TapReleaseTimeThreshold seconds |
| `UInputTriggerPulse` | Pulse | Fires at intervals while input is actuated |
| `UInputTriggerChordAction` | Chord Action | Requires another action to be active simultaneously |

### Input Modifier Classes

| C++ Class | Blueprint Name | Description |
|-----------|---------------|-------------|
| `UInputModifierNegate` | Negate | Inverts input axis values |
| `UInputModifierSwizzleAxis` | Swizzle Input Axis Values | Reorders axis components (e.g., map 1D to Y axis of 2D) |
| `UInputModifierDeadZone` | Dead Zone | Applies dead zone threshold to input |
| `UInputModifierScalar` | Scalar | Multiplies input by a scale factor |
| `UInputModifierFOVScaling` | FOV Scaling | Scales input based on camera FOV |
| `UInputModifierToWorldSpace` | To World Space | Converts axial input to world space |
| `UInputModifierResponseCurveUser` | Response Curve | Applies custom response curve to input |
| `UInputModifierSmooth` | Smooth | Smooths input over time |

### Debug Commands

- `showdebug enhancedinput` - Display active input debug info
- `showdebug devices` - Display connected input devices
- `Input.+key` - Console: inject key press
- `Input.-key` - Console: inject key release

---

## 2. Save Game System

### C++ Classes

| Class | Description |
|-------|-------------|
| `USaveGame` | Abstract base class for save game objects. Add UPROPERTY members for data to save. |
| `UGameplayStatics` | Static utility class exposing save/load functions to Blueprint |
| `UAsyncActionHandleSaveGame` | Async action wrapper for async save/load operations |
| `ULocalPlayerSaveGame` | Per-player save game variant (UE 5.3+) |

### Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Create Save Game Object** | `UGameplayStatics::CreateSaveGameObject()` | Creates new USaveGame instance of specified class |
| **Save Game to Slot** | `UGameplayStatics::SaveGameToSlot()` | Synchronous save to named slot, returns bool success |
| **Load Game from Slot** | `UGameplayStatics::LoadGameFromSlot()` | Synchronous load from named slot, returns USaveGame* or null |
| **Async Save Game to Slot** | `UAsyncActionHandleSaveGame::AsyncSaveGameToSlot()` | Recommended async save with Completed delegate (success + object) |
| **Async Load Game from Slot** | `UAsyncActionHandleSaveGame::AsyncLoadGameFromSlot()` | Async load with Completed delegate (success + object) |
| **Does Save Game Exist** | `UGameplayStatics::DoesSaveGameExist()` | Returns bool if save file exists in slot |
| **Delete Game in Slot** | `UGameplayStatics::DeleteGameInSlot()` | Deletes save data in specified slot, returns bool |

### Additional C++ Functions (not directly exposed as individual BP nodes)

| Function | Description |
|----------|-------------|
| `SaveGameToMemory()` | Transfers SaveGame object to binary buffer (TArray<uint8>) |
| `LoadGameFromMemory()` | Converts binary data back to SaveGame object |
| `SaveDataToSlot()` | Saves raw binary data directly to file |
| `LoadDataFromSlot()` | Loads raw binary data from file |

### Save Game Workflow (Blueprint)

```
1. Create Save Game Object (class: MySaveGame) -> SaveGameObject
2. Set properties on SaveGameObject (player position, health, inventory, etc.)
3. Save Game to Slot (SaveGameObject, "SlotName", UserIndex: 0) -> bool Success
```

```
1. Does Save Game Exist ("SlotName", UserIndex: 0) -> bool Exists
2. Branch on Exists
3. Load Game from Slot ("SlotName", UserIndex: 0) -> USaveGame*
4. Cast to MySaveGame -> access saved properties
```

---

## 3. Collision / Physics Traces

### C++ Library: `UKismetSystemLibrary`

All trace and overlap Blueprint nodes are exposed via the Kismet System Library.

### Line Trace Blueprint Nodes

| Blueprint Node | Description | Returns |
|---------------|-------------|---------|
| **Line Trace By Channel** | Single trace against a Trace Channel, returns first blocking hit | bool + FHitResult |
| **Line Trace By Profile** | Single trace using a collision profile name | bool + FHitResult |
| **Line Trace For Objects** | Single trace filtered by object types array | bool + FHitResult |
| **Multi Line Trace By Channel** | Returns all overlaps up to first blocking hit | bool + TArray<FHitResult> |
| **Multi Line Trace By Profile** | Multi-hit trace using collision profile | bool + TArray<FHitResult> |
| **Multi Line Trace For Objects** | Multi-hit trace filtered by object types | bool + TArray<FHitResult> |

### Sphere Trace Blueprint Nodes

| Blueprint Node | Description | Returns |
|---------------|-------------|---------|
| **Sphere Trace By Channel** | Sweeps sphere along line, first blocking hit by channel | bool + FHitResult |
| **Sphere Trace By Profile** | Sweeps sphere using collision profile | bool + FHitResult |
| **Sphere Trace For Objects** | Sweeps sphere filtered by object types | bool + FHitResult |
| **Multi Sphere Trace By Channel** | Multi-hit sphere sweep by channel | bool + TArray<FHitResult> |
| **Multi Sphere Trace By Profile** | Multi-hit sphere sweep by profile | bool + TArray<FHitResult> |
| **Multi Sphere Trace For Objects** | Multi-hit sphere sweep by object types | bool + TArray<FHitResult> |

### Box Trace Blueprint Nodes

| Blueprint Node | Description | Returns |
|---------------|-------------|---------|
| **Box Trace By Channel** | Sweeps box along line, first blocking hit by channel | bool + FHitResult |
| **Box Trace By Profile** | Sweeps box using collision profile | bool + FHitResult |
| **Box Trace For Objects** | Sweeps box filtered by object types | bool + FHitResult |
| **Multi Box Trace By Channel** | Multi-hit box sweep by channel | bool + TArray<FHitResult> |
| **Multi Box Trace By Profile** | Multi-hit box sweep by profile | bool + TArray<FHitResult> |
| **Multi Box Trace For Objects** | Multi-hit box sweep by object types | bool + TArray<FHitResult> |

### Capsule Trace Blueprint Nodes

| Blueprint Node | Description | Returns |
|---------------|-------------|---------|
| **Capsule Trace By Channel** | Sweeps capsule along line, first blocking hit by channel | bool + FHitResult |
| **Capsule Trace By Profile** | Sweeps capsule using collision profile | bool + FHitResult |
| **Capsule Trace For Objects** | Sweeps capsule filtered by object types | bool + FHitResult |
| **Multi Capsule Trace By Channel** | Multi-hit capsule sweep by channel | bool + TArray<FHitResult> |
| **Multi Capsule Trace By Profile** | Multi-hit capsule sweep by profile | bool + TArray<FHitResult> |
| **Multi Capsule Trace For Objects** | Multi-hit capsule sweep by object types | bool + TArray<FHitResult> |

### Line Trace By Channel - Full Parameter Reference

**Inputs:**
| Type | Pin Name | Description |
|------|----------|-------------|
| vector | Start | Start of line segment |
| vector | End | End of line segment |
| enum | Trace Channel | ETraceTypeQuery channel to trace against |
| boolean | Trace Complex | True = complex collision, False = simplified |
| object[] | Actors to Ignore | Actors excluded from trace |
| enum | Draw Debug Type | None / ForOneFrame / ForDuration / Persistent |
| boolean | Ignore Self | Skip calling actor |
| linearcolor | Trace Color | Debug line color |
| linearcolor | Trace Hit Color | Debug hit point color |
| real | Draw Time | Debug visualization duration |

**Outputs:**
| Type | Pin Name | Description |
|------|----------|-------------|
| struct | Out Hit | FHitResult with hit properties |
| boolean | Return Value | True if hit occurred |

### Overlap Blueprint Nodes

| Blueprint Node | Description | Returns |
|---------------|-------------|---------|
| **Sphere Overlap Actors** | Returns actors overlapping a sphere at position | TArray<AActor*> |
| **Sphere Overlap Components** | Returns components overlapping a sphere | TArray<UPrimitiveComponent*> |
| **Sphere Overlap Component** | Tests single component against sphere | bool |
| **Box Overlap Actors** | Returns actors overlapping an AABB box | TArray<AActor*> |
| **Box Overlap Actors With Orientation** | Returns actors overlapping an oriented box | TArray<AActor*> |
| **Box Overlap Components** | Returns components overlapping a box | TArray<UPrimitiveComponent*> |
| **Box Overlap Component** | Tests single component against box (AABB) | bool |
| **Capsule Overlap Actors** | Returns actors overlapping a capsule | TArray<AActor*> |
| **Capsule Overlap Actors With Orientation** | Returns actors overlapping oriented capsule | TArray<AActor*> |
| **Capsule Overlap Components** | Returns components overlapping a capsule | TArray<UPrimitiveComponent*> |
| **Component Overlap Actors** | Returns actors overlapping a given component | TArray<AActor*> |
| **Component Overlap Components** | Returns components overlapping a given component | TArray<UPrimitiveComponent*> |

### FHitResult Struct (Break Hit Result node)

| Field | Type | Description |
|-------|------|-------------|
| Blocking Hit | boolean | Whether the hit was a blocking hit |
| Initial Overlap | boolean | Whether the trace started inside a collision volume |
| Time | real | Time of impact along trace (0.0 to 1.0) |
| Distance | real | Distance from trace start to impact point |
| Location | vector | Location in world space of the trace end (adjusted for penetration) |
| Impact Point | vector | Actual location in world space where the hit occurred |
| Normal | vector | Normal of the surface hit (for swept traces) |
| Impact Normal | vector | Normal of the surface at impact point |
| Phys Mat | object | Physical material at hit surface (UPhysicalMaterial*) |
| Hit Actor | object | Actor that was hit (AActor*) |
| Hit Component | object | Component that was hit (UPrimitiveComponent*) |
| Hit Bone Name | name | Name of bone hit (skeletal meshes) |
| Bone Name | name | Name of the bone on the hit component |
| Hit Item | integer | Index of item on hit component |
| Element Index | integer | Index of face/element hit |
| Face Index | integer | Index of face hit (mesh triangles) |
| Trace Start | vector | World space start of the trace |
| Trace End | vector | World space end of the trace |

---

## 4. Material Parameters / Dynamic Material Instances

### C++ Classes

| Class | Description |
|-------|-------------|
| `UMaterialInterface` | Abstract base for all material types |
| `UMaterialInstance` | Base for material instances (constant or dynamic) |
| `UMaterialInstanceConstant` | Editor-time material instance, not modifiable at runtime |
| `UMaterialInstanceDynamic` | Runtime-modifiable material instance (MID) |
| `UMaterialParameterCollection` | Shared material parameters accessible globally |
| `UMaterialParameterCollectionInstance` | Runtime instance of a parameter collection |

### Blueprint Nodes - Dynamic Material Instance

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Create Dynamic Material Instance** | `UPrimitiveComponent::CreateDynamicMaterialInstance()` | Creates MID from material on a component, optionally at element index |
| **Set Scalar Parameter Value** | `UMaterialInstanceDynamic::SetScalarParameterValue()` | Sets a float parameter by name |
| **Set Vector Parameter Value** | `UMaterialInstanceDynamic::SetVectorParameterValue()` | Sets a vector/color parameter by name |
| **Set Texture Parameter Value** | `UMaterialInstanceDynamic::SetTextureParameterValue()` | Sets a texture parameter by name |
| **Get Scalar Parameter Value** | `UMaterialInstanceDynamic::K2_GetScalarParameterValue()` | Gets current float parameter value |
| **Get Vector Parameter Value** | `UMaterialInstanceDynamic::K2_GetVectorParameterValue()` | Gets current vector/color parameter value |
| **Get Texture Parameter Value** | `UMaterialInstanceDynamic::K2_GetTextureParameterValue()` | Gets current texture parameter |
| **Set Material** | `UPrimitiveComponent::SetMaterial()` | Applies a material to a component at element index |

### UMaterialInstanceDynamic - Full C++ API

**Parameter Setters:**
```cpp
void SetScalarParameterValue(FName ParameterName, float Value);
void SetScalarParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo, float Value);
void SetVectorParameterValue(FName ParameterName, FLinearColor Value);
void SetVectorParameterValue(FName ParameterName, const FVector& Value);
void SetVectorParameterValue(FName ParameterName, const FVector4& Value);
void SetVectorParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo, FLinearColor Value);
void SetVectorParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo, const FVector& Value);
void SetVectorParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo, const FVector4& Value);
void SetTextureParameterValue(FName ParameterName, UTexture* Value);
void SetTextureParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo, UTexture* Value);
void SetTextureCollectionParameterValue(FName ParameterName, UTextureCollection* Value);
void SetRuntimeVirtualTextureParameterValue(FName ParameterName, URuntimeVirtualTexture* Value);
```

**Parameter Getters:**
```cpp
float K2_GetScalarParameterValue(FName ParameterName);
float K2_GetScalarParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo);
FLinearColor K2_GetVectorParameterValue(FName ParameterName);
FLinearColor K2_GetVectorParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo);
UTexture* K2_GetTextureParameterValue(FName ParameterName);
UTexture* K2_GetTextureParameterValueByInfo(const FMaterialParameterInfo& ParameterInfo);
```

**Utilities:**
```cpp
void CopyParameterOverrides(UMaterialInstance* MaterialInstance);
void CopyMaterialUniformParameters(UMaterialInterface* Source);
void K2_InterpolateMaterialInstanceParams(UMaterialInstance* SourceA, UMaterialInstance* SourceB, float Alpha);
void ClearParameterValues();
static UMaterialInstanceDynamic* Create(UMaterialInterface* ParentMaterial, UObject* InOuter, FName Name = NAME_None);
```

### Blueprint Nodes - Material Parameter Collection

| Blueprint Node | Description |
|---------------|-------------|
| **Get Scalar Parameter Value** (on MPC) | Gets scalar from a Material Parameter Collection |
| **Set Scalar Parameter Value** (on MPC) | Sets scalar on a Material Parameter Collection (global) |
| **Get Vector Parameter Value** (on MPC) | Gets vector from a Material Parameter Collection |
| **Set Vector Parameter Value** (on MPC) | Sets vector on a Material Parameter Collection (global) |

### Blueprint Nodes - Per-Primitive Custom Data

| Blueprint Node | Description |
|---------------|-------------|
| **Set Custom Primitive Data Float** | Sets float custom primitive data at index |
| **Set Custom Primitive Data Vector** | Sets vector custom primitive data at index |
| **Set Scalar Parameter Value on Materials** | Sets scalar parameter across all materials on a component |

---

## 5. Subsystems

### C++ Class Hierarchy

```
UObject -> USubsystem -> UDynamicSubsystem
                      -> UGameInstanceSubsystem
                      -> ULocalPlayerSubsystem
                      -> UWorldSubsystem -> UTickableWorldSubsystem
                      -> UEngineSubsystem
                      -> UEditorSubsystem
```

### Subsystem Types

| Base Class | Lifetime | Access (C++) | Access (Blueprint) |
|-----------|----------|-------------|-------------------|
| `UEngineSubsystem` | Engine lifetime | `GEngine->GetEngineSubsystem<T>()` | Get Engine Subsystem (auto-typed) |
| `UEditorSubsystem` | Editor lifetime | `GEditor->GetEditorSubsystem<T>()` | Get Editor Subsystem (auto-typed) |
| `UGameInstanceSubsystem` | Game Instance lifetime | `GameInstance->GetSubsystem<T>()` | Get Game Instance Subsystem (auto-typed) |
| `UWorldSubsystem` | World lifetime | `World->GetSubsystem<T>()` | Get World Subsystem (auto-typed) |
| `ULocalPlayerSubsystem` | Local Player lifetime | `LocalPlayer->GetSubsystem<T>()` | Get Local Player Subsystem (auto-typed) |
| `UTickableWorldSubsystem` | World lifetime + ticks | `World->GetSubsystem<T>()` | Same as UWorldSubsystem |

### Blueprint Access

Subsystems are automatically exposed to Blueprints with "smart nodes" that understand context and do not require casting. When searching the Blueprint context menu, subsystems appear categorized under their type (e.g., "World Subsystems", "Game Instance Subsystems").

### UWorldSubsystem Methods

| Method | Description |
|--------|-------------|
| `Initialize(FSubsystemCollectionBase&)` | Called during world initialization |
| `PostInitialize()` | Called after all UWorldSubsystems are initialized |
| `Deinitialize()` | Called during world teardown |
| `PreDeinitialize()` | Called before any UWorldSubsystems are deinitialized |
| `ShouldCreateSubsystem(UObject*)` | Override to control creation (return false to skip) |
| `OnWorldBeginPlay(UWorld&)` | Called when world gameplay begins |
| `OnWorldEndPlay(UWorld&)` | Called when world gameplay ends |
| `OnWorldComponentsUpdated(UWorld&)` | Called after world components updated |
| `UpdateStreamingState()` | Manages streaming behavior |
| `GetWorld()` | Returns UWorld pointer |
| `GetWorldRef()` | Returns UWorld reference |
| `DoesSupportWorldType(EWorldType::Type)` | Protected - filter by world type (Game, Editor, PIE, etc.) |

### Python Access

```python
my_engine_subsystem = unreal.get_engine_subsystem(unreal.MyEngineSubsystem)
my_editor_subsystem = unreal.get_editor_subsystem(unreal.MyEditorSubsystem)
```

### Built-in Subsystems (Notable)

| Subsystem | Type | Description |
|-----------|------|-------------|
| `UEnhancedInputLocalPlayerSubsystem` | LocalPlayer | Enhanced Input management |
| `UEnhancedInputEditorSubsystem` | Editor | Enhanced Input editor support |
| `UEnhancedInputUserSettings` | - | User input settings/preferences |

---

## 6. Data Tables

### C++ Classes

| Class | Description |
|-------|-------------|
| `UDataTable` | Data table asset containing rows of a single struct type |
| `UCurveTable` | Curve table asset for float curve data |
| `FDataTableRowHandle` | Handle referencing a specific row in a DataTable |
| `FCurveTableRowHandle` | Handle referencing a specific row in a CurveTable |

### Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Data Table Row** | `UDataTableFunctionLibrary::GetDataTableRow()` | Attempts to retrieve a row by RowName. Returns bool success + row struct. |
| **Get Data Table Row Names** | `UDataTableFunctionLibrary::GetDataTableRowNames()` | Returns TArray<FName> of all row names in the table |
| **Get Data Table Row Struct** | `UDataTableFunctionLibrary::GetDataTableRowStruct()` | Returns the UScriptStruct used by the DataTable |
| **Does Data Table Row Exist** | `UDataTableFunctionLibrary::DoesDataTableRowExist()` | Returns bool if a row with given name exists |
| **Get Data Table Column as String** | `UDataTableFunctionLibrary::GetDataTableColumnAsString()` | Returns all values in a column as TArray<FString> |
| **Get Data Table Column Names** | `UDataTableFunctionLibrary::GetDataTableColumnNames()` | Returns TArray<FString> of all column names |
| **Get Data Table Column Export Names** | `UDataTableFunctionLibrary::GetDataTableColumnExportNames()` | Returns export-format column names |
| **Get Data Table Column Name from Export Name** | `UDataTableFunctionLibrary::GetDataTableColumnNameFromExportName()` | Converts export name back to column name |
| **Evaluate Curve Table Row** | `UDataTableFunctionLibrary::EvaluateCurveTableRow()` | Evaluates a CurveTable row at a given X value |
| **Add Data Table Row** | (Editor Scripting) | Adds a row to a DataTable (editor-only) |

### DataTable Row Handle (Blueprint Variable)

When you expose a `FDataTableRowHandle` property to Blueprint, it creates a picker widget in the Details panel that lets you select a DataTable asset and a specific row from it. This is the recommended way to reference DataTable rows in actor/component properties.

---

## 7. Struct Operations (Break / Make)

### FVector

| Blueprint Node | Library | Pins |
|---------------|---------|------|
| **Make Vector** | KismetMathLibrary | In: X (real), Y (real), Z (real) -> Out: Return Value (vector) |
| **Break Vector** | KismetMathLibrary | In: In Vec (vector) -> Out: X (real), Y (real), Z (real) |
| **Make Vector 2D** | KismetMathLibrary | In: X (real), Y (real) -> Out: Return Value (vector2d) |
| **Break Vector 2D** | KismetMathLibrary | In: In Vec (vector2d) -> Out: X (real), Y (real) |

### FRotator

| Blueprint Node | Library | Pins |
|---------------|---------|------|
| **Make Rotator** | KismetMathLibrary | In: Roll (real), Pitch (real), Yaw (real) -> Out: Return Value (rotator) |
| **Break Rotator** | KismetMathLibrary | In: Rotation (rotator) -> Out: X/Roll (real), Y/Pitch (real), Z/Yaw (real) |

### FTransform

| Blueprint Node | Library | Pins |
|---------------|---------|------|
| **Make Transform** | KismetMathLibrary | In: Location (vector), Rotation (rotator), Scale (vector) -> Out: Return Value (transform) |
| **Break Transform** | KismetMathLibrary | In: In Transform (transform) -> Out: Location (vector), Rotation (rotator), Scale (vector) |

### FLinearColor

| Blueprint Node | Library | Pins |
|---------------|---------|------|
| **Make Color** | KismetMathLibrary | In: R (real), G (real), B (real), A (real) -> Out: Return Value (linearcolor) |
| **Break Color** | KismetMathLibrary | In: In Color (linearcolor) -> Out: R (real), G (real), B (real), A (real) |

### FHitResult

| Blueprint Node | Library | Description |
|---------------|---------|-------------|
| **Break Hit Result** | GameplayStatics | Decomposes FHitResult into 19 output pins (see Section 3 for full field list) |

### Additional Common Struct Nodes

| Blueprint Node | Struct | Description |
|---------------|--------|-------------|
| **Make Literal Int** | - | Creates an integer constant |
| **Make Literal Float** | - | Creates a float constant |
| **Make Literal Bool** | - | Creates a boolean constant |
| **Make Literal String** | - | Creates a string constant |
| **Make Literal Name** | - | Creates an FName constant |
| **Make Literal Text** | - | Creates an FText constant |
| **Make Array** | TArray | Creates an array from individual elements |
| **Make Set** | TSet | Creates a set from individual elements |
| **Make Map** | TMap | Creates a map from key-value pairs |

### Auto-Generated Make/Break Pattern

Any `USTRUCT(BlueprintType)` with `UPROPERTY(BlueprintReadWrite)` or `UPROPERTY(BlueprintReadOnly)` members automatically generates:
- **Make [StructName]** - Pure node with one input per writable property
- **Break [StructName]** - Pure node with one output per readable property

---

## 8. Math Comparison Nodes

### C++ Library: `UKismetMathLibrary`

All comparison operators are exposed as Blueprint-callable static functions. In the Blueprint editor, these appear as operator nodes (e.g., `>`, `<`, `==`).

### Float Comparison Nodes

| Blueprint Node (Display) | C++ Function | Description |
|--------------------------|-------------|-------------|
| **float > float** | `UKismetMathLibrary::Greater_DoubleDouble()` | Returns true if A is greater than B (A > B) |
| **float >= float** | `UKismetMathLibrary::GreaterEqual_DoubleDouble()` | Returns true if A is greater than or equal to B (A >= B) |
| **float < float** | `UKismetMathLibrary::Less_DoubleDouble()` | Returns true if A is less than B (A < B) |
| **float <= float** | `UKismetMathLibrary::LessEqual_DoubleDouble()` | Returns true if A is less than or equal to B (A <= B) |
| **float == float** | `UKismetMathLibrary::EqualEqual_DoubleDouble()` | Returns true if A is exactly equal to B (A == B) |
| **float != float** | `UKismetMathLibrary::NotEqual_DoubleDouble()` | Returns true if A is not equal to B (A != B) |
| **Nearly Equal (Float)** | `UKismetMathLibrary::NearlyEqual_FloatFloat()` | Returns true if A is nearly equal to B within tolerance |
| **In Range (Float)** | `UKismetMathLibrary::InRange_FloatFloat()` | Returns true if value is between min and max (inclusive options) |

### Integer Comparison Nodes

| Blueprint Node (Display) | C++ Function | Description |
|--------------------------|-------------|-------------|
| **integer > integer** | `UKismetMathLibrary::Greater_IntInt()` | Returns true if A is greater than B |
| **integer >= integer** | `UKismetMathLibrary::GreaterEqual_IntInt()` | Returns true if A >= B |
| **integer < integer** | `UKismetMathLibrary::Less_IntInt()` | Returns true if A is less than B |
| **integer <= integer** | `UKismetMathLibrary::LessEqual_IntInt()` | Returns true if A <= B |
| **integer == integer** | `UKismetMathLibrary::EqualEqual_IntInt()` | Returns true if A equals B |
| **integer != integer** | `UKismetMathLibrary::NotEqual_IntInt()` | Returns true if A does not equal B |
| **In Range (Integer)** | `UKismetMathLibrary::InRange_IntInt()` | Returns true if value is between min and max |

### Boolean Logic Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **AND Boolean** | `UKismetMathLibrary::BooleanAND()` | Logical AND of two booleans |
| **OR Boolean** | `UKismetMathLibrary::BooleanOR()` | Logical OR of two booleans |
| **NOT Boolean** | `UKismetMathLibrary::Not_PreBool()` | Logical NOT (complement) |
| **NAND Boolean** | `UKismetMathLibrary::BooleanNAND()` | Logical NAND |
| **NOR Boolean** | `UKismetMathLibrary::BooleanNOR()` | Logical NOR |
| **XOR Boolean** | `UKismetMathLibrary::BooleanXOR()` | Logical exclusive OR |

### Other Comparison Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Nearly Equal (Transform)** | `UKismetMathLibrary::NearlyEqual_TransformTransform()` | Checks if two transforms are nearly equal within tolerance |
| **Equal (Vector)** | `UKismetMathLibrary::EqualEqual_VectorVector()` | Exact vector equality check |
| **Equal (Rotator)** | `UKismetMathLibrary::EqualEqual_RotatorRotator()` | Exact rotator equality check |
| **Compare Float Values** | `UMVVMViewModelBlueprintLibrary` | Viewmodel comparison utility for floats |

### Clamping and Range Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Clamp (Float)** | `UKismetMathLibrary::FClamp()` | Returns value clamped between A and B (inclusive) |
| **Clamp (Integer)** | `UKismetMathLibrary::Clamp()` | Returns integer clamped between min and max |
| **Clamp Angle** | `UKismetMathLibrary::ClampAngle()` | Clamps an angle to a specified range |
| **Map Range Clamped** | `UKismetMathLibrary::MapRangeClamped()` | Maps value from one range to another, clamping result |
| **Map Range Unclamped** | `UKismetMathLibrary::MapRangeUnclamped()` | Maps value from one range to another, no clamping |
| **Normalize to Range** | `UKismetMathLibrary::NormalizeToRange()` | Normalizes value to 0-1 based on given range |
| **Wrap (Float)** | `UKismetMathLibrary::FWrap()` | Returns value wrapped from A to B (inclusive) |
| **Wrap (Integer)** | `UKismetMathLibrary::Wrap()` | Wraps integer between min and max |

### Min/Max Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Max (Float)** | `UKismetMathLibrary::FMax()` | Returns the larger of two floats |
| **Min (Float)** | `UKismetMathLibrary::FMin()` | Returns the smaller of two floats |
| **Max (Integer)** | `UKismetMathLibrary::Max()` | Returns the larger of two integers |
| **Min (Integer)** | `UKismetMathLibrary::Min()` | Returns the smaller of two integers |
| **Max Of Float Array** | `UKismetMathLibrary::MaxOfFloatArray()` | Returns max value from an array of floats |
| **Min Of Float Array** | `UKismetMathLibrary::MinOfFloatArray()` | Returns min value from an array of floats |
| **Max Of Int Array** | `UKismetMathLibrary::MaxOfIntArray()` | Returns max value from an array of integers |
| **Min Of Int Array** | `UKismetMathLibrary::MinOfIntArray()` | Returns min value from an array of integers |

### Float Utility Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Absolute (Float)** | `UKismetMathLibrary::Abs()` | Returns absolute value of a float |
| **Absolute (Integer)** | `UKismetMathLibrary::Abs_Int()` | Returns absolute value of an integer |
| **Sign (Float)** | `UKismetMathLibrary::SignOfFloat()` | Returns -1, 0, or 1 based on sign |
| **Sign (Integer)** | `UKismetMathLibrary::SignOfInteger()` | Returns -1, 0, or 1 based on sign |
| **Power** | `UKismetMathLibrary::MultiplyMultiply_FloatFloat()` | Returns A raised to the power of B |
| **Sqrt** | `UKismetMathLibrary::Sqrt()` | Returns square root |
| **Square** | `UKismetMathLibrary::Square()` | Returns value squared |
| **Exp** | `UKismetMathLibrary::Exp()` | Returns e^A |
| **Log** | `UKismetMathLibrary::Log()` | Returns log base 10 |
| **Loge** | `UKismetMathLibrary::Loge()` | Returns natural log (ln) |
| **Ceil** | `UKismetMathLibrary::FCeil()` | Rounds up to nearest integer |
| **Floor** | `UKismetMathLibrary::FFloor()` | Rounds down to nearest integer |
| **Round** | `UKismetMathLibrary::Round()` | Rounds to nearest integer |
| **Truncate** | `UKismetMathLibrary::FTrunc()` | Truncates toward zero |
| **Fraction** | `UKismetMathLibrary::Fraction()` | Returns fractional part of a float |
| **Safe Divide** | `UKismetMathLibrary::SafeDivide()` | Divides A by B, returns 0 if B is 0 |
| **Snap To Grid (Float)** | `UKismetMathLibrary::GridSnap_Float()` | Snaps value to nearest grid increment |
| **Hypotenuse** | `UKismetMathLibrary::Hypotenuse()` | Returns sqrt(Width^2 + Height^2) |
| **% (Float)** | `UKismetMathLibrary::Percent_FloatFloat()` | Modulo operation for floats |
| **% (Integer)** | `UKismetMathLibrary::Percent_IntInt()` | Modulo operation for integers |
| **Multiply by Pi** | `UKismetMathLibrary::MultiplyByPi()` | Returns value * Pi |

---

## 9. Interpolation / Lerp Nodes

### C++ Library: `UKismetMathLibrary`

### Core Interpolation Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Lerp** | `UKismetMathLibrary::Lerp()` | Linearly interpolates between A and B based on Alpha (0=A, 1=B) |
| **Lerp (Vector)** | `UKismetMathLibrary::VLerp()` | Linearly interpolates between two vectors |
| **Lerp (Rotator)** | `UKismetMathLibrary::RLerp()` | Linearly interpolates between two rotators |
| **Lerp (Transform)** | `UKismetMathLibrary::TLerp()` | Linearly interpolates between two transforms |
| **Lerp (LinearColor)** | `UKismetMathLibrary::LinearColorLerp()` | Linearly interpolates between two colors |
| **Lerp Using HSV (LinearColor)** | `UKismetMathLibrary::LinearColorLerpUsingHSV()` | Interpolates colors in HSV space for more natural transitions |

### Framerate-Independent Interpolation (FInterp)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **FInterp To** | `UKismetMathLibrary::FInterpTo()` | Smooth float interp based on distance from current to target (framerate independent) |
| **FInterp to Constant** | `UKismetMathLibrary::FInterpTo_Constant()` | Moves toward target at constant rate |
| **VInterp To** | `UKismetMathLibrary::VInterpTo()` | Smooth vector interp toward target |
| **VInterp to Constant** | `UKismetMathLibrary::VInterpTo_Constant()` | Vector interp at constant rate |
| **RInterp To** | `UKismetMathLibrary::RInterpTo()` | Smooth rotator interp toward target |
| **RInterp to Constant** | `UKismetMathLibrary::RInterpTo_Constant()` | Rotator interp at constant rate |
| **TInterp To** | `UKismetMathLibrary::TInterpTo()` | Smooth transform interp toward target |
| **Vector 2DInterp To** | `UKismetMathLibrary::Vector2DInterpTo()` | Smooth Vector2D interp toward target |
| **Vector 2DInterp to Constant** | `UKismetMathLibrary::Vector2DInterpTo_Constant()` | Vector2D interp at constant rate |
| **Interpolate (LinearColor)** | `UKismetMathLibrary::CInterpTo()` | Smooth color interp toward target |

### Ease / Curve Interpolation

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Ease** | `UKismetMathLibrary::Ease()` | Interpolates with selectable easing function (EaseIn, EaseOut, EaseInOut, etc.) |
| **FInterp Ease in Out** | `UKismetMathLibrary::FInterpEaseInOut()` | Interpolates between A and B with ease in/out curve |
| **Make Pulsating Value** | `UKismetMathLibrary::MakePulsatingValue()` | Creates oscillating value for pulsing effects |

### Spring Interpolation

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Float Spring Interp** | `UKismetMathLibrary::FloatSpringInterp()` | Physics-based spring interpolation for floats |
| **Vector Spring Interp** | `UKismetMathLibrary::VectorSpringInterp()` | Physics-based spring interpolation for vectors |
| **Quaternion Spring Interp** | `UKismetMathLibrary::QuaternionSpringInterp()` | Physics-based spring interpolation for quaternions |
| **Reset Float Spring State** | `UKismetMathLibrary::ResetFloatSpringState()` | Resets float spring to initial state |
| **Reset Vector Spring State** | `UKismetMathLibrary::ResetVectorSpringState()` | Resets vector spring to initial state |
| **Reset Quaternion Spring State** | `UKismetMathLibrary::ResetQuaternionSpringState()` | Resets quaternion spring to initial state |
| **Set Float Spring State Velocity** | `UKismetMathLibrary::SetFloatSpringStateVelocity()` | Manually set spring velocity |
| **Set Vector Spring State Velocity** | `UKismetMathLibrary::SetVectorSpringStateVelocity()` | Manually set vector spring velocity |
| **Set Quaternion Spring State Angular Velocity** | `UKismetMathLibrary::SetQuaternionSpringStateAngularVelocity()` | Manually set quaternion spring angular velocity |

### Utility

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Fixed Turn** | `UKismetMathLibrary::FixedTurn()` | Rotates toward target at fixed rate, useful for turrets |

---

## 10. Math Random Nodes

### C++ Library: `UKismetMathLibrary`

### Core Random Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Random Float** | `UKismetMathLibrary::RandomFloat()` | Returns random float between 0.0 and 1.0 |
| **Random Float in Range** | `UKismetMathLibrary::RandomFloatInRange()` | Returns random float between Min and Max |
| **Random Integer** | `UKismetMathLibrary::RandomInteger()` | Returns random int from 0 to Max-1 |
| **Random Integer in Range** | `UKismetMathLibrary::RandomIntegerInRange()` | Returns random int between Min and Max (inclusive) |
| **Random Integer 64** | `UKismetMathLibrary::RandomInteger64()` | Returns random 64-bit integer |
| **Random Integer 64 In Range** | `UKismetMathLibrary::RandomInteger64InRange()` | Returns random 64-bit int in range |
| **Random Bool** | `UKismetMathLibrary::RandomBool()` | Returns random true/false (50/50) |
| **Random Bool with Weight** | `UKismetMathLibrary::RandomBoolWithWeight()` | Returns true based on weight probability (0.0 to 1.0) |

### Random Vector / Rotation Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Random Unit Vector** | `UKismetMathLibrary::RandomUnitVector()` | Returns random vector with length 1 |
| **Random Unit Vector in Cone in Degrees** | `UKismetMathLibrary::RandomUnitVectorInConeInDegrees()` | Random unit vector within a cone (degrees) |
| **Random Unit Vector in Cone in Radians** | `UKismetMathLibrary::RandomUnitVectorInConeInRadians()` | Random unit vector within a cone (radians) |
| **Random Unit Vector in Elliptical Cone in Degrees** | `UKismetMathLibrary::RandomUnitVectorInEllipticalConeInDegrees()` | Random unit vector in elliptical cone |
| **Random Unit Vector in Elliptical Cone in Radians** | `UKismetMathLibrary::RandomUnitVectorInEllipticalConeInRadians()` | Random unit vector in elliptical cone (radians) |
| **Random Rotator** | `UKismetMathLibrary::RandomRotator()` | Returns random rotator (optionally roll-only) |
| **Random Point In Bounding Box** | `UKismetMathLibrary::RandomPointInBoundingBox()` | Returns random point inside a bounding box |

### Random Streams (Seeded / Deterministic)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Make Random Stream** | `UKismetMathLibrary::MakeRandomStream()` | Creates a seeded random stream for deterministic results |
| **Break Random Stream** | `UKismetMathLibrary::BreakRandomStream()` | Decomposes random stream into seed |
| **Seed Random Stream** | `UKismetMathLibrary::SeedRandomStream()` | Seeds a random stream with new seed value |
| **Set Random Stream Seed** | `UKismetMathLibrary::SetRandomStreamSeed()` | Sets the seed on an existing stream |
| **Reset Random Stream** | `UKismetMathLibrary::ResetRandomStream()` | Resets stream to initial seed |
| **Random Float from Stream** | `UKismetMathLibrary::RandomFloatFromStream()` | Returns random float using a seeded stream |
| **Random Float in Range from Stream** | `UKismetMathLibrary::RandomFloatInRangeFromStream()` | Random float in range from stream |
| **Random Integer from Stream** | `UKismetMathLibrary::RandomIntegerFromStream()` | Random int from stream |
| **Random Integer in Range from Stream** | `UKismetMathLibrary::RandomIntegerInRangeFromStream()` | Random int in range from stream |
| **Random Bool from Stream** | `UKismetMathLibrary::RandomBoolFromStream()` | Random bool from stream |
| **Random Bool with Weight from Stream** | `UKismetMathLibrary::RandomBoolWithWeightFromStream()` | Weighted random bool from stream |
| **Random Unit Vector from Stream** | `UKismetMathLibrary::RandomUnitVectorFromStream()` | Random unit vector from stream |
| **Random Rotator from Stream** | `UKismetMathLibrary::RandomRotatorFromStream()` | Random rotator from stream |
| **Random Point In Bounding Box From Stream** | `UKismetMathLibrary::RandomPointInBoundingBoxFromStream()` | Random point in box from stream |

### Noise / Quasi-Random Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Perlin Noise 1D** | `UKismetMathLibrary::PerlinNoise1D()` | Returns 1D Perlin noise value for given input |
| **Random Sobol Float** | `UKismetMathLibrary::RandomSobolFloat()` | Returns quasi-random Sobol sequence float |
| **Random Sobol Cell 2D** | `UKismetMathLibrary::RandomSobolCell2D()` | Returns quasi-random 2D Sobol cell |
| **Random Sobol Cell 3D** | `UKismetMathLibrary::RandomSobolCell3D()` | Returns quasi-random 3D Sobol cell |
| **Next Sobol Float** | `UKismetMathLibrary::NextSobolFloat()` | Advances Sobol sequence and returns next float |
| **Next Sobol Cell 2D** | `UKismetMathLibrary::NextSobolCell2D()` | Advances 2D Sobol sequence |
| **Next Sobol Cell 3D** | `UKismetMathLibrary::NextSobolCell3D()` | Advances 3D Sobol sequence |

### Importance Sampling

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Make Importance Texture** | `UKismetMathLibrary::MakeImportanceTexture()` | Creates importance texture for weighted sampling |
| **Break Importance Texture** | `UKismetMathLibrary::BreakImportanceTexture()` | Decomposes importance texture |
| **Importance Sample** | `UKismetMathLibrary::ImportanceSample()` | Samples from importance distribution |
| **Make Random Stream from Location** | `UKismetMathLibrary::MakeRandomStreamFromLocation()` | Creates deterministic stream based on world location |

---

## 11. Damage System Nodes

### C++ Library: `UGameplayStatics`

### Damage Application Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Apply Damage** | `UGameplayStatics::ApplyDamage()` | Hurts the specified actor with generic damage |
| **Apply Point Damage** | `UGameplayStatics::ApplyPointDamage()` | Hurts the specified actor with impact at a specific point/direction |
| **Apply Radial Damage** | `UGameplayStatics::ApplyRadialDamage()` | Hurts locally authoritative actors within radius. Returns true if damage applied. |
| **Apply Radial Damage with Falloff** | `UGameplayStatics::ApplyRadialDamageWithFalloff()` | Applies radial damage with distance-based falloff (inner/outer radius) |

### Apply Damage - Full Parameter Reference

**Inputs:**
| Type | Pin Name | Description |
|------|----------|-------------|
| object | Damaged Actor | Actor to damage (AActor*) |
| real | Base Damage | Amount of damage to apply |
| object | Event Instigator | Controller responsible for damage (AController*) |
| object | Damage Causer | Actor that caused the damage (AActor*, e.g., projectile) |
| class | Damage Type Class | Class describing the damage (TSubclassOf<UDamageType>) |

### Apply Radial Damage - Full Parameter Reference

**Inputs:**
| Type | Pin Name | Description |
|------|----------|-------------|
| real | Base Damage | Maximum damage at origin |
| vector | Origin | Center point of damage sphere |
| real | Damage Radius | Radius of damage sphere |
| object[] | Ignore Actors | Actors to exclude |
| object | Damage Causer | Actor that caused the damage |
| object | Instigated By | Controller responsible |
| class | Damage Type Class | Damage type class |
| enum | Damage Prevention Channel | Channel to check for blocking |
| boolean | Do Full Damage | If true, full damage to all in radius (no falloff) |

### Damage Receiving Events (Override in Blueprint)

| Blueprint Event | C++ Override | Description |
|----------------|-------------|-------------|
| **Event Any Damage** | `AActor::ReceiveAnyDamage()` | Called when actor receives any damage type |
| **Event Point Damage** | `AActor::ReceivePointDamage()` | Called when actor receives point damage (with hit info) |
| **Event Radial Damage** | `AActor::ReceiveRadialDamage()` | Called when actor receives radial damage |

### UDamageType Properties

| Property | Type | Description |
|----------|------|-------------|
| `DamageImpulse` | float | Impulse magnitude applied to physics bodies on damage |
| `DestructibleImpulse` | float | Impulse magnitude applied to destructible meshes |
| `DestructibleDamageSpreadScale` | float | How much damage spreads across destructible mesh |
| `DamageFalloff` | float | Damage falloff exponent (0 = no falloff) |
| `bCausedByWorld` | bool | True if damage is from the world (falling, environment) |
| `bScaleMomentumByMass` | bool | Scale impulse by victim's mass |
| `bRadialDamageVelChange` | bool | Use velocity change instead of impulse |

---

## 12. Mesh / Static Mesh Operations

### C++ Classes

| Class | Description |
|-------|-------------|
| `UStaticMeshComponent` | Creates an instance of a UStaticMesh, used for non-deforming geometry |
| `UStaticMesh` | Static mesh asset (the mesh data itself) |
| `UInstancedStaticMeshComponent` | Renders many instances of same mesh efficiently |
| `UHierarchicalInstancedStaticMeshComponent` | ISM with LOD hierarchy for large instance counts |
| `UProceduralMeshComponent` | Runtime-generated mesh geometry |

### Static Mesh Component Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Set Static Mesh** | `UStaticMeshComponent::SetStaticMesh()` | Changes the StaticMesh used by this component instance |
| **Get Static Mesh** | `UStaticMeshComponent::GetStaticMesh()` | Returns the current StaticMesh asset |
| **Get Local Bounds** | `UStaticMeshComponent::GetLocalBounds()` | Returns local-space bounding box of the mesh |
| **Get Bounds** | `UStaticMesh::GetBounds()` | Returns the bounds of the static mesh asset |
| **Get Bounding Box** | `UStaticMesh::GetBoundingBox()` | Returns the AABB of the static mesh |
| **Get Material** | `UStaticMeshComponent::GetMaterial()` | Returns material at specified element index |
| **Set Material** | `UPrimitiveComponent::SetMaterial()` | Sets material at element index on the component |
| **Get Num Materials** | `UPrimitiveComponent::GetNumMaterials()` | Returns number of material slots |
| **Set Forced Lod Model** | `UStaticMeshComponent::SetForcedLodModel()` | Forces a specific LOD level |
| **Set Reverse Culling** | `UStaticMeshComponent::SetReverseCulling()` | Reverses triangle winding order |
| **Set Evaluate World Position Offset** | `UStaticMeshComponent::SetEvaluateWorldPositionOffset()` | Controls World Position Offset evaluation |
| **Add Static Mesh Component** | Physics category utility | Adds a new StaticMeshComponent to an actor at runtime |

### Instanced Static Mesh Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Add Instance** | `UInstancedStaticMeshComponent::AddInstance()` | Adds a new instance with a transform |
| **Add Instances** | `UInstancedStaticMeshComponent::AddInstances()` | Batch-adds multiple instances |
| **Remove Instance** | `UInstancedStaticMeshComponent::RemoveInstance()` | Removes instance at index |
| **Remove Instances** | `UInstancedStaticMeshComponent::RemoveInstances()` | Batch-removes multiple instances |
| **Clear Instances** | `UInstancedStaticMeshComponent::ClearInstances()` | Removes all instances |
| **Get Instance Count** | `UInstancedStaticMeshComponent::GetInstanceCount()` | Returns total instance count |
| **Get Instance Transform** | `UInstancedStaticMeshComponent::GetInstanceTransform()` | Returns transform of instance at index |
| **Update Instance Transform** | `UInstancedStaticMeshComponent::UpdateInstanceTransform()` | Updates transform for a specific instance |
| **Batch Update Instances Transform** | `UInstancedStaticMeshComponent::BatchUpdateInstancesTransform()` | Applies delta transform to range of instances |
| **Batch Update Instances Transforms** | `UInstancedStaticMeshComponent::BatchUpdateInstancesTransforms()` | Sets absolute transforms for range of instances |
| **Is Valid Instance** | `UInstancedStaticMeshComponent::IsValidInstance()` | Checks if instance index is valid |
| **Set Custom Data Value** | `UInstancedStaticMeshComponent::SetCustomDataValue()` | Sets per-instance custom float data |
| **Set Num Custom Data Floats** | `UInstancedStaticMeshComponent::SetNumCustomDataFloats()` | Sets number of custom data floats per instance |
| **Get Instances Overlapping Box** | `UInstancedStaticMeshComponent::GetInstancesOverlappingBox()` | Returns instances inside a box |
| **Get Instances Overlapping Sphere** | `UInstancedStaticMeshComponent::GetInstancesOverlappingSphere()` | Returns instances inside a sphere |
| **Set Cull Distances** | `UInstancedStaticMeshComponent::SetCullDistances()` | Sets start/end cull distances |
| **Get Cull Distances** | `UInstancedStaticMeshComponent::GetCullDistances()` | Gets current cull distances |
| **Set LODDistance Scale** | `UInstancedStaticMeshComponent::SetLODDistanceScale()` | Scales LOD transition distances |
| **Get LODDistance Scale** | `UInstancedStaticMeshComponent::GetLODDistanceScale()` | Gets current LOD distance scale |

### Common Scene Component Nodes (inherited by all mesh components)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Set Relative Location** | `USceneComponent::SetRelativeLocation()` | Sets position relative to parent |
| **Set Relative Rotation** | `USceneComponent::SetRelativeRotation()` | Sets rotation relative to parent |
| **Set Relative Scale 3D** | `USceneComponent::SetRelativeScale3D()` | Sets scale relative to parent |
| **Set World Location** | `USceneComponent::SetWorldLocation()` | Sets position in world space |
| **Set World Rotation** | `USceneComponent::SetWorldRotation()` | Sets rotation in world space |
| **Set World Scale 3D** | `USceneComponent::SetWorldScale3D()` | Sets scale in world space |
| **Get World Location** | `USceneComponent::GetComponentLocation()` | Returns world position |
| **Get World Rotation** | `USceneComponent::GetComponentRotation()` | Returns world rotation |
| **Get World Scale** | `USceneComponent::GetComponentScale()` | Returns world scale |
| **Set Visibility** | `USceneComponent::SetVisibility()` | Shows/hides the component |
| **Set Hidden in Game** | `USceneComponent::SetHiddenInGame()` | Controls runtime visibility |
| **Attach To Component** | `USceneComponent::K2_AttachToComponent()` | Attaches to another component |
| **Detach From Component** | `USceneComponent::K2_DetachFromComponent()` | Detaches from parent |

---

## 13. Audio-Adjacent Blueprint Nodes

### C++ Classes

| Class | Description |
|-------|-------------|
| `UAudioComponent` | Component for playing sounds, attachable to actors |
| `UGameplayStatics` | Static library with fire-and-forget audio functions |
| `USoundBase` | Abstract base for all sound assets |
| `USoundCue` | Sound cue asset (graph-based audio) |
| `USoundWave` | Raw wave audio asset |
| `USoundAttenuation` | Attenuation settings asset |
| `USoundConcurrency` | Concurrency settings for sound limiting |
| `USoundMix` | Sound mix/snapshot settings |
| `UReverbEffect` | Reverb effect settings |

### Fire-and-Forget Audio (UGameplayStatics)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Play Sound 2D** | `UGameplayStatics::PlaySound2D()` | Plays a sound with no attenuation, perfect for UI sounds |
| **Play Sound at Location** | `UGameplayStatics::PlaySoundAtLocation()` | Plays a sound at given world location (fire-and-forget) |
| **Spawn Sound 2D** | `UGameplayStatics::SpawnSound2D()` | Creates non-spatialized AudioComponent, returns reference for control |
| **Spawn Sound at Location** | `UGameplayStatics::SpawnSoundAtLocation()` | Creates spatialized AudioComponent at location, returns reference |
| **Spawn Sound Attached** | `UGameplayStatics::SpawnSoundAttached()` | Creates AudioComponent attached to another component |
| **Create Sound 2D** | `UGameplayStatics::CreateSound2D()` | Creates non-spatialized AudioComponent without auto-play |

### Dialogue Audio (UGameplayStatics)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Play Dialogue 2D** | `UGameplayStatics::PlayDialogue2D()` | Plays dialogue with no attenuation |
| **Play Dialogue at Location** | `UGameplayStatics::PlayDialogueAtLocation()` | Plays dialogue at world location |
| **Spawn Dialogue 2D** | `UGameplayStatics::SpawnDialogue2D()` | Creates non-spatialized dialogue component |
| **Spawn Dialogue Attached** | `UGameplayStatics::SpawnDialogueAttached()` | Creates attached dialogue component |
| **Spawn Dialogue at Location** | `UGameplayStatics::SpawnDialogueAtLocation()` | Creates spatialized dialogue component |

### UAudioComponent Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Set Sound** | `UAudioComponent::SetSound()` | Changes which sound asset this component plays |
| **Play** | `UAudioComponent::Play()` | Begins playing at optional start time |
| **Stop** | `UAudioComponent::Stop()` | Stops playback, fires delegates |
| **Set Paused** | `UAudioComponent::SetPaused()` | Pauses/unpauses playback |
| **Stop Delayed** | `UAudioComponent::StopDelayed()` | Stops after a delay in seconds |
| **Is Playing** | `UAudioComponent::IsPlaying()` | Returns true if currently playing |
| **Get Play State** | `UAudioComponent::GetPlayState()` | Returns enumerated play state |
| **Set Volume Multiplier** | `UAudioComponent::SetVolumeMultiplier()` | Sets volume multiplier |
| **Set Pitch Multiplier** | `UAudioComponent::SetPitchMultiplier()` | Sets pitch multiplier |
| **Adjust Volume** | `UAudioComponent::AdjustVolume()` | Triggers volume adjustment over time |
| **Fade In** | `UAudioComponent::FadeIn()` | Play with volume fade-in curve |
| **Fade Out** | `UAudioComponent::FadeOut()` | Delayed stop with volume fade-out curve |
| **Adjust Attenuation** | `UAudioComponent::AdjustAttenuation()` | Modify attenuation settings at runtime |
| **BP Get Attenuation Settings To Apply** | `UAudioComponent::BP_GetAttenuationSettingsToApply()` | Retrieves current attenuation settings |
| **Set Low Pass Filter Frequency** | `UAudioComponent::SetLowPassFilterFrequency()` | Sets low pass filter cutoff in Hz |
| **Set High Pass Filter Frequency** | `UAudioComponent::SetHighPassFilterFrequency()` | Sets high pass filter cutoff in Hz |
| **Set Submix Send** | `UAudioComponent::SetSubmixSend()` | Sets send level to a submix |
| **Set Audio Bus Send Pre Effect** | `UAudioComponent::SetAudioBusSendPreEffect()` | Sets pre-effect send to audio bus |
| **Set Audio Bus Send Post Effect** | `UAudioComponent::SetAudioBusSendPostEffect()` | Sets post-effect send to audio bus |
| **Set Float Parameter** | `UAudioComponent::SetFloatParameter()` | Sets a named float parameter on the sound |
| **Set Int Parameter** | `UAudioComponent::SetIntParameter()` | Sets a named int parameter |
| **Set Bool Parameter** | `UAudioComponent::SetBoolParameter()` | Sets a named bool parameter |
| **Set Wave Parameter** | `UAudioComponent::SetWaveParameter()` | Sets a wave asset parameter |
| **Has Cooked FFT Data** | `UAudioComponent::HasCookedFFTData()` | Checks if sound has cooked FFT analysis data |
| **Has Cooked Amplitude Envelope Data** | `UAudioComponent::HasCookedAmplitudeEnvelopeData()` | Checks if sound has cooked envelope data |

### Sound Mix Control (UGameplayStatics)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Push Sound Mix Modifier** | `UGameplayStatics::PushSoundMixModifier()` | Pushes a sound mix onto the active stack |
| **Pop Sound Mix Modifier** | `UGameplayStatics::PopSoundMixModifier()` | Removes a sound mix from the active stack |
| **Clear Sound Mix Modifiers** | `UGameplayStatics::ClearSoundMixModifiers()` | Clears all sound mix modifiers |
| **Set Sound Mix Class Override** | `UGameplayStatics::SetSoundMixClassOverride()` | Overrides a sound class volume/pitch in a mix |
| **Clear Sound Mix Class Override** | `UGameplayStatics::ClearSoundMixClassOverride()` | Clears a sound class override |
| **Set Base Sound Mix** | `UGameplayStatics::SetBaseSoundMix()` | Sets the base (default) sound mix |
| **Activate Reverb Effect** | `UGameplayStatics::ActivateReverbEffect()` | Activates a reverb effect with priority |
| **Deactivate Reverb Effect** | `UGameplayStatics::DeactivateReverbEffect()` | Deactivates a reverb effect by tag |

### Audio Device Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Available Audio Output Devices** | Platform audio | Lists available audio output devices |
| **Get Available Audio Input Devices** | Platform audio | Lists available audio input devices |
| **Get Current Audio Output Device Name** | Platform audio | Returns name of current output device |
| **Swap Audio Output Device** | Platform audio | Switches to a different output device |

---

## 14. Viewport / Screen Nodes

### C++ Libraries

| Class | Description |
|-------|-------------|
| `UGameplayStatics` | World-to-screen projection functions |
| `UWidgetLayoutLibrary` | Widget/viewport measurement utilities |
| `APlayerController` | Screen-space conversion utilities |
| `APlayerCameraManager` | Camera state access |

### Projection Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Project World to Screen** | `APlayerController::ProjectWorldLocationToScreen()` | Transforms 3D world point to 2D screen coordinates |
| **Deproject Screen to World** | `APlayerController::DeprojectScreenPositionToWorld()` | Transforms 2D screen position to 3D world location + direction |
| **Convert World Location to Screen Location** | `APlayerController::ProjectWorldLocationToScreen()` | Alternate name for world-to-screen projection |
| **Project World Location to Widget Position** | `UWidgetLayoutLibrary` | Projects world location to widget-space position |

### Viewport Size / Scale

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Viewport Size** (Viewport category) | `UWidgetLayoutLibrary::GetViewportSize()` | Returns the size of the game viewport |
| **Get Viewport Size** (HUD category) | `AHUD::GetViewportSize()` | Returns HUD canvas size for player controller |
| **Get Viewport Scale** | `UWidgetLayoutLibrary::GetViewportScale()` | Returns current viewport DPI scale factor |
| **Get View Projection Matrix** | Viewport category | Returns the combined view-projection matrix |
| **Get Viewport Widget Geometry** | Viewport category | Returns widget geometry of the viewport |
| **Get Player Screen Widget Geometry** | Viewport category | Returns screen widget geometry for player |
| **Get Viewport World** | Viewport category | Returns the UWorld associated with viewport |

### Mouse / Input Position

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Mouse Position on Viewport** | Viewport category | Returns mouse position in viewport space |
| **Get Mouse Position on Platform** | Viewport category | Returns mouse position in platform coordinates |
| **Get Mouse Position Scaled by DPI** | Viewport category | Returns DPI-adjusted mouse position |

### Camera Access

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Player Camera Manager** | `UGameplayStatics::GetPlayerCameraManager()` | Returns APlayerCameraManager for specified player index |
| **Get Camera Location** | `APlayerCameraManager::GetCameraLocation()` | Returns current camera world position |
| **Get Camera Rotation** | `APlayerCameraManager::GetCameraRotation()` | Returns current camera world rotation |
| **Get FOV Angle** | `APlayerCameraManager::GetFOVAngle()` | Returns current camera field of view |

### Viewport Control

| Blueprint Node | Description |
|---------------|-------------|
| **Set Viewport Mouse Capture Mode** | Sets mouse capture behavior |
| **Get Viewport Mouse Capture Mode** | Gets current mouse capture mode |
| **Has Multiple Local Players** | Returns true if splitscreen is active |
| **Is Splitscreen Force Disabled** | Checks if splitscreen is force-disabled |
| **Set Force Disable Splitscreen** | Force-disables splitscreen |
| **Set Suppress Viewport Transition Message** | Suppresses level transition messages |
| **Set Show Flag** | Sets a viewport show flag |
| **Remove All Widgets** | Removes all UMG widgets from viewport |

---

## 15. Platform Detection Nodes

### C++ Library: `UGameplayStatics`, `UKismetSystemLibrary`

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Platform Name** | `UGameplayStatics::GetPlatformName()` | Returns string name of current platform ("Windows", "Mac", "Linux", "IOS", "Android", etc.) |
| **Get Platform User Name** | `UKismetSystemLibrary::GetPlatformUserName()` | Returns the platform user's display name |
| **Get Platform User Index** | Save Game category | Returns the platform user index for save games |
| **Get Supported Platform Names** | Mobile Patching category | Returns list of supported platform names |

### Platform Name Return Values

| Return Value | Platform |
|-------------|----------|
| `"Windows"` | Windows PC |
| `"Mac"` | macOS |
| `"Linux"` | Linux |
| `"IOS"` | iOS |
| `"Android"` | Android |
| `"PS5"` | PlayStation 5 |
| `"XSX"` | Xbox Series X/S |
| `"Switch"` | Nintendo Switch |

### Usage Pattern (Branch on Platform)

```
Get Platform Name -> Switch on String -> platform-specific logic
```

---

## 16. Environment Query System (EQS) Nodes

### C++ Classes

| Class | Description |
|-------|-------------|
| `UEnvQueryManager` | Manages EQS query execution |
| `UEnvQuery` | EQS query asset (the template defining generators + tests) |
| `UEnvQueryInstanceBlueprintWrapper` | Blueprint-friendly wrapper for query results |
| `UEnvQueryGenerator` | Base class for EQS generators |
| `UEnvQueryTest` | Base class for EQS scoring tests |
| `UEnvQueryContext` | Base class for EQS context providers |

### Blueprint Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Run EQS Query** | `UEnvQueryManager::RunEQSQuery()` | Executes an EQS query template, returns results as wrapper object |

### Run EQS Query - Parameter Reference

| Type | Pin Name | Description |
|------|----------|-------------|
| object | Query Template | The EQS query asset to execute |
| object | Querier | The entity performing the query (typically AI controller or pawn) |
| enum | Run Mode | Execution mode for the query |
| class | Wrapper Class | Optional custom wrapper class for results |
| **Return** | object | UEnvQueryInstanceBlueprintWrapper result object |

### EQS Result Access (on UEnvQueryInstanceBlueprintWrapper)

| Blueprint Node | Description |
|---------------|-------------|
| **Get Results as Actors** | Returns scored results as array of actors |
| **Get Results as Locations** | Returns scored results as array of vectors |
| **Get Item Score** | Gets the score of a specific result item |
| **On Query Finished Event** | Delegate fired when async query completes |

### Behavior Tree EQS Integration

| Task/Service | Description |
|-------------|-------------|
| **Run EQS Query (Task)** | BT task that executes EQS query and stores result in Blackboard |
| **Run EQS (Service)** | BT service that periodically runs EQS query |

### Common EQS Generators

| Generator | Description |
|----------|-------------|
| Actors Of Class | Generates items from actors of a specific class |
| On Circle | Generates points on a circle around context |
| Simple Grid | Generates a grid of points |
| Path Grid | Grid that follows navmesh paths |
| Current Location | Single point at context location |

### Common EQS Tests

| Test | Description |
|------|-------------|
| Distance | Scores based on distance to context |
| Trace | Line trace visibility check |
| Dot | Dot product between direction vectors |
| Pathfinding | Navigation path cost/length |
| Overlap | Physics overlap check |
| GameplayTags | Matches gameplay tag queries |

---

## 17. Collision / Overlap Event Nodes (Extended)

### C++ Class: `UPrimitiveComponent`, `AActor`

Extends Section 3 with event-based collision nodes.

### Component Overlap Events

| Blueprint Event | C++ Delegate | Description |
|----------------|-------------|-------------|
| **On Component Begin Overlap** | `UPrimitiveComponent::OnComponentBeginOverlap` | Fires when something starts overlapping (e.g., player enters trigger) |
| **On Component End Overlap** | `UPrimitiveComponent::OnComponentEndOverlap` | Fires when overlap ends |
| **On Component Hit** | `UPrimitiveComponent::OnComponentHit` | Fires on blocking collision (e.g., hitting a wall) |

### Actor Overlap Events

| Blueprint Event | C++ Delegate | Description |
|----------------|-------------|-------------|
| **On Actor Begin Overlap** | `AActor::OnActorBeginOverlap` | Fires when any component on this actor begins overlapping another actor |
| **On Actor End Overlap** | `AActor::OnActorEndOverlap` | Fires when overlap between actors ends |
| **On Actor Hit** | `AActor::OnActorHit` | Fires when actor has a blocking collision |

### Chaos Physics Events

| Blueprint Event | Description |
|----------------|-------------|
| **On Chaos Physics Collision** | Fires during Chaos physics collision events (UE5 Chaos engine) |

### Collision Configuration Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Set Collision Enabled** | `UPrimitiveComponent::SetCollisionEnabled()` | Enables/disables collision (No Collision, Query Only, Physics Only, Query and Physics) |
| **Set Collision Object Type** | `UPrimitiveComponent::SetCollisionObjectType()` | Sets the object type channel |
| **Set Collision Profile Name** | `UPrimitiveComponent::SetCollisionProfileName()` | Sets collision using named profile (e.g., "BlockAll", "OverlapAll") |
| **Set Collision Response to Channel** | `UPrimitiveComponent::SetCollisionResponseToChannel()` | Sets response to a specific channel (Ignore/Overlap/Block) |
| **Set Collision Response to All Channels** | `UPrimitiveComponent::SetCollisionResponseToAllChannels()` | Sets response to all channels at once |
| **Get Collision Enabled** | `UPrimitiveComponent::GetCollisionEnabled()` | Returns current collision enabled state |
| **Get Collision Object Type** | `UPrimitiveComponent::GetCollisionObjectType()` | Returns collision object type |
| **Get Collision Profile Name** | `UPrimitiveComponent::GetCollisionProfileName()` | Returns current collision profile name |
| **Get Collision Response to Channel** | `UPrimitiveComponent::GetCollisionResponseToChannel()` | Returns response for a specific channel |
| **Is Collision Enabled** | `UPrimitiveComponent::IsCollisionEnabled()` | Quick check if any collision is enabled |

### Overlap Query Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Overlapping Actors** | `AActor::GetOverlappingActors()` | Returns all actors currently overlapping |
| **Get Overlapping Components** | `AActor::GetOverlappingComponents()` | Returns all components currently overlapping |
| **Is Overlapping Actor** | `AActor::IsOverlappingActor()` | Checks if overlapping a specific actor |
| **Is Overlapping Component** | `UPrimitiveComponent::IsOverlappingComponent()` | Checks if overlapping a specific component |

### Collision Ignore Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Set Actor Enable Collision** | `AActor::SetActorEnableCollision()` | Enables/disables all collision on actor |
| **Get Actor Enable Collision** | `AActor::GetActorEnableCollision()` | Returns collision enabled state |
| **Ignore Actor when Moving** | `UPrimitiveComponent::IgnoreActorWhenMoving()` | Ignores specific actor during movement sweeps |
| **Ignore Component when Moving** | `UPrimitiveComponent::IgnoreComponentWhenMoving()` | Ignores specific component during sweeps |
| **Get Move Ignore Actors** | `UPrimitiveComponent::GetMoveIgnoreActors()` | Returns list of ignored actors |
| **Get Move Ignore Components** | `UPrimitiveComponent::GetMoveIgnoreComponents()` | Returns list of ignored components |
| **Clear Move Ignore Actors** | `UPrimitiveComponent::ClearMoveIgnoreActors()` | Clears all actor ignores |
| **Clear Move Ignore Components** | `UPrimitiveComponent::ClearMoveIgnoreComponents()` | Clears all component ignores |

### Collision Utility Nodes

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Break Hit Result** | Struct utility | Decomposes FHitResult into all output pins (see Section 3) |
| **Make Hit Result** | Struct utility | Constructs FHitResult from individual values |
| **Get Actor Bounds** | `AActor::GetActorBounds()` | Returns actor's axis-aligned bounding box |
| **Get Component Bounds** | `USceneComponent::GetComponentBounds()` | Returns component bounding box |
| **Get Closest Point on Collision** | `UPrimitiveComponent::GetClosestPointOnCollision()` | Finds closest point on collision surface |
| **Find Collision UV** | `UPrimitiveComponent::K2_FindCollisionUV()` | Returns UV coordinates at collision point |
| **Get Surface Type** | Collision utility | Returns physical surface type at hit point |
| **Can Character Step Up** | Character movement | Checks if character can step up onto hit |

---

## 18. Struct Operations (Extended)

Extends Section 7 with additional common struct nodes.

### FVector Operations

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Make Vector** | `UKismetMathLibrary::MakeVector()` | Constructs vector from X, Y, Z |
| **Break Vector** | `UKismetMathLibrary::BreakVector()` | Decomposes vector into X, Y, Z |
| **Cross Product** | `UKismetMathLibrary::Cross_VectorVector()` | Returns cross product of two vectors |
| **Dot Product** | `UKismetMathLibrary::Dot_VectorVector()` | Returns dot product of two vectors |
| **Normalize** | `UKismetMathLibrary::Normal()` | Returns unit-length vector |
| **Vector Length** | `UKismetMathLibrary::VSize()` | Returns magnitude of vector |
| **Vector Length Squared** | `UKismetMathLibrary::VSizeSquared()` | Returns squared magnitude (faster, no sqrt) |
| **Distance (Vector)** | `UKismetMathLibrary::Vector_Distance()` | Returns distance between two points |
| **Distance 2D (Vector)** | `UKismetMathLibrary::Vector_Distance2D()` | Returns 2D distance (ignores Z) |
| **Get Unit Direction (Vector)** | `UKismetMathLibrary::GetDirectionUnitVector()` | Returns unit direction from A to B |
| **Clamp Vector Size** | `UKismetMathLibrary::ClampVectorSize()` | Clamps vector magnitude between min and max |
| **Rotate Vector** | `UKismetMathLibrary::GreaterGreater_VectorRotator()` | Rotates vector by rotator |
| **Rotate Vector Around Axis** | `UKismetMathLibrary::RotateAngleAxis()` | Rotates vector around specified axis |
| **Mirror Vector by Normal** | `UKismetMathLibrary::MirrorVectorByNormal()` | Reflects vector off a surface normal |
| **Project Vector on to Vector** | `UKismetMathLibrary::ProjectVectorOnToVector()` | Projects A onto B |
| **Project Vector on to Plane** | `UKismetMathLibrary::ProjectVectorOnToPlane()` | Projects vector onto a plane |
| **Get Forward Vector** | `UKismetMathLibrary::GetForwardVector()` | Returns forward (X) unit vector from rotator |
| **Get Right Vector** | `UKismetMathLibrary::GetRightVector()` | Returns right (Y) unit vector from rotator |
| **Get Up Vector** | `UKismetMathLibrary::GetUpVector()` | Returns up (Z) unit vector from rotator |

### FRotator Operations

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Make Rotator** | `UKismetMathLibrary::MakeRotator()` | Constructs rotator from Roll, Pitch, Yaw |
| **Break Rotator** | `UKismetMathLibrary::BreakRotator()` | Decomposes rotator into Roll, Pitch, Yaw |
| **Combine Rotators** | `UKismetMathLibrary::ComposeRotators()` | Combines two rotators |
| **Delta (Rotator)** | `UKismetMathLibrary::NormalizedDeltaRotator()` | Returns shortest rotation between two rotators |
| **Find Look at Rotation** | `UKismetMathLibrary::FindLookAtRotation()` | Returns rotation to look from Start to Target |
| **Normalize Axis** | `UKismetMathLibrary::NormalizeAxis()` | Normalizes angle to [-180, 180] |
| **Clamp Axis** | `UKismetMathLibrary::ClampAxis()` | Clamps angle to [0, 360] |
| **Invert Rotator** | `UKismetMathLibrary::InvertRotator()` | Returns negated rotator |
| **Break Rot Into Axes** | `UKismetMathLibrary::BreakRotIntoAxes()` | Returns forward, right, up vectors from rotator |
| **Make Rotation from Axes** | `UKismetMathLibrary::MakeRotFromAxes()` | Constructs rotator from axis vectors |

### FTransform Operations

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Make Transform** | `UKismetMathLibrary::MakeTransform()` | Constructs from location, rotation, scale |
| **Break Transform** | `UKismetMathLibrary::BreakTransform()` | Decomposes into location, rotation, scale |
| **Compose Transforms** | `UKismetMathLibrary::ComposeTransforms()` | Multiplies two transforms (A * B) |
| **Invert Transform** | `UKismetMathLibrary::InvertTransform()` | Returns inverse of transform |
| **Transform Location** | `UKismetMathLibrary::TransformLocation()` | Transforms a point by the given transform |
| **Inverse Transform Location** | `UKismetMathLibrary::InverseTransformLocation()` | Applies inverse transform to a point |
| **Transform Direction** | `UKismetMathLibrary::TransformDirection()` | Transforms a direction vector (ignores translation) |
| **Inverse Transform Direction** | `UKismetMathLibrary::InverseTransformDirection()` | Inverse-transforms a direction |
| **Transform Rotation** | `UKismetMathLibrary::TransformRotation()` | Transforms a rotation |
| **Inverse Transform Rotation** | `UKismetMathLibrary::InverseTransformRotation()` | Inverse-transforms a rotation |
| **Make Relative Transform** | `UKismetMathLibrary::MakeRelativeTransform()` | Creates transform relative to another |
| **Determinant** | `UKismetMathLibrary::Determinant()` | Returns determinant of the transform matrix |
| **To Matrix (Transform)** | `UKismetMathLibrary::Conv_TransformToMatrix()` | Converts transform to 4x4 matrix |
| **Lerp (Transform)** | `UKismetMathLibrary::TLerp()` | Linearly interpolates between two transforms |
| **Nearly Equal (Transform)** | `UKismetMathLibrary::NearlyEqual_TransformTransform()` | Checks approximate equality |
| **Select Transform** | `UKismetMathLibrary::SelectTransform()` | Returns A or B based on boolean |

### Type Conversion Nodes (Math > Conversions)

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **To Float (Integer)** | `UKismetMathLibrary::Conv_IntToFloat()` | Converts int to float |
| **To Float (Boolean)** | `UKismetMathLibrary::Conv_BoolToFloat()` | Converts bool to float (0.0 or 1.0) |
| **To Float (Byte)** | `UKismetMathLibrary::Conv_ByteToFloat()` | Converts byte to float |
| **To Integer (Boolean)** | `UKismetMathLibrary::Conv_BoolToInt()` | Converts bool to int (0 or 1) |
| **To Integer (Float)** | `UKismetMathLibrary::FTrunc()` | Truncates float to int |
| **To Integer (Byte)** | `UKismetMathLibrary::Conv_ByteToInt()` | Converts byte to int |
| **To Boolean (Integer)** | `UKismetMathLibrary::Conv_IntToBool()` | Converts int to bool (0 = false) |
| **To Boolean (Float)** | `UKismetMathLibrary::Conv_FloatToBool()` | Converts float to bool (0.0 = false) |
| **To Vector (Float)** | `UKismetMathLibrary::Conv_FloatToVector()` | Creates vector (X=Y=Z=float) |
| **To Vector (LinearColor)** | `UKismetMathLibrary::Conv_LinearColorToVector()` | Converts color RGB to vector |
| **To LinearColor (Vector)** | `UKismetMathLibrary::Conv_VectorToLinearColor()` | Converts vector to color |
| **To LinearColor (Color)** | `UKismetMathLibrary::Conv_ColorToLinearColor()` | Converts FColor to FLinearColor |
| **To Color (LinearColor)** | `UKismetMathLibrary::Conv_LinearColorToColor()` | Converts FLinearColor to FColor |
| **ToRotator (Quat)** | `UKismetMathLibrary::Conv_QuatToRotator()` | Converts quaternion to rotator |
| **ToQuaternion (Rotator)** | `UKismetMathLibrary::Conv_RotatorToQuaternion()` | Converts rotator to quaternion |
| **To Transform (Vector)** | `UKismetMathLibrary::Conv_VectorToTransform()` | Creates transform from location vector |
| **To Transform (Rotator)** | `UKismetMathLibrary::Conv_RotatorToTransform()` | Creates transform from rotation |
| **To Transform (Matrix)** | `UKismetMathLibrary::Conv_MatrixToTransform()` | Converts matrix to transform |
| **To Rotator (Matrix)** | `UKismetMathLibrary::Conv_MatrixToRotator()` | Extracts rotation from matrix |
| **To Vector2D (Vector)** | `UKismetMathLibrary::Conv_VectorToVector2D()` | Drops Z component |
| **To Vector (Vector2D)** | `UKismetMathLibrary::Conv_Vector2DToVector()` | Adds Z=0 |

---

## 19. Additional UGameplayStatics Nodes

### Player / Game State Access

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Player Controller** | `UGameplayStatics::GetPlayerController()` | Returns player controller at index |
| **Get Player Character** | `UGameplayStatics::GetPlayerCharacter()` | Returns player character at index |
| **Get Player Pawn** | `UGameplayStatics::GetPlayerPawn()` | Returns player pawn at index |
| **Get Player State** | `UGameplayStatics::GetPlayerState()` | Returns player state at index from GameState array |
| **Get Game Mode** | `UGameplayStatics::GetGameMode()` | Returns current AGameModeBase (server only) |
| **Get Game State** | `UGameplayStatics::GetGameState()` | Returns current AGameStateBase |
| **Get Game Instance** | `UGameplayStatics::GetGameInstance()` | Returns UGameInstance |

### Time Control

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Time Seconds** | `UGameplayStatics::GetTimeSeconds()` | Time since play started (dilated, pauses) |
| **Get Real Time Seconds** | `UGameplayStatics::GetRealTimeSeconds()` | Real time since play started (not dilated, no pause) |
| **Get World Delta Seconds** | `UGameplayStatics::GetWorldDeltaSeconds()` | Frame delta time (dilated) |
| **Get Global Time Dilation** | `UGameplayStatics::GetGlobalTimeDilation()` | Returns current time dilation factor |
| **Set Global Time Dilation** | `UGameplayStatics::SetGlobalTimeDilation()` | Sets time dilation (1.0 = normal, 0.5 = half speed) |
| **Set Game Paused** | `UGameplayStatics::SetGamePaused()` | Pauses/unpauses the game |
| **Is Game Paused** | `UGameplayStatics::IsGamePaused()` | Returns current pause state |

### Level Management

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Open Level** | `UGameplayStatics::OpenLevel()` | Travels to another level by name or URL |
| **Get Current Level Name** | `UGameplayStatics::GetCurrentLevelName()` | Returns name of the current level |
| **Load Stream Level** | `UGameplayStatics::LoadStreamLevel()` | Begins streaming a sublevel |
| **Unload Stream Level** | `UGameplayStatics::UnloadStreamLevel()` | Unloads a streaming sublevel |

### Actor Query

| Blueprint Node | C++ Function | Description |
|---------------|-------------|-------------|
| **Get Actor Of Class** | `UGameplayStatics::GetActorOfClass()` | Finds first actor of specified class |
| **Get All Actors Of Class** | `UGameplayStatics::GetAllActorsOfClass()` | Returns all actors of specified class |
| **Get All Actors with Tag** | `UGameplayStatics::GetAllActorsWithTag()` | Returns all actors with specified tag |
| **Find Nearest Actor** | `UGameplayStatics::FindNearestActor()` | Returns closest actor from array to origin |
| **Create Player** | `UGameplayStatics::CreatePlayer()` | Creates new local player (local multiplayer) |
| **Remove Player** | `UGameplayStatics::RemovePlayer()` | Removes a local player |

---

## Resources

<references>
- [Enhanced Input Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine) - Main Enhanced Input documentation
- [UEnhancedInputComponent API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UEnhancedInputComponent) - Full C++ API reference
- [UInputAction API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputAction) - Input Action data asset
- [UInputMappingContext API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputMappingContext) - Mapping context class
- [UInputTriggerTap](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputTriggerTap) - Tap trigger
- [UInputTriggerHoldAndRelease](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputTriggerHoldAndRelease) - Hold and release trigger
- [UInputTriggerReleased](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputTriggerReleased) - Released trigger
- [UInputTriggerChordAction](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputTriggerChordAction) - Chord trigger
- [UInputModifierSwizzleAxis](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EnhancedInput/UInputModifierSwizzleAxis) - Swizzle modifier
- [Saving and Loading](https://dev.epicgames.com/documentation/en-us/unreal-engine/saving-and-loading-your-game-in-unreal-engine) - Save Game guide
- [USaveGame API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/GameFramework/USaveGame) - Save game base class
- [UGameplayStatics API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UGameplayStatics) - Static gameplay utilities
- [Save Game to Slot BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/SaveGametoSlot) - Blueprint node
- [Load Game from Slot BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/LoadGamefromSlot) - Blueprint node
- [Async Save Game to Slot BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/AsyncSaveGametoSlot) - Async save node
- [Delete Game in Slot BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/DeleteGameinSlot) - Delete save node
- [Create Save Game Object BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/SaveGame/CreateSaveGameObject) - Create save node
- [Traces Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/traces-in-unreal-engine---overview) - Trace system overview
- [Line Trace By Channel BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/LineTraceByChannel) - Line trace node
- [Sphere Trace By Channel BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/SphereTraceByChannel) - Sphere trace node
- [Box Trace By Channel BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/BoxTraceByChannel) - Box trace node
- [Capsule Trace By Channel BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/CapsuleTraceByChannel) - Capsule trace node
- [Break Hit Result BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/BreakHitResult) - Hit result decomposition
- [Sphere Overlap Actors BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/SphereOverlapActors) - Overlap node
- [Box Overlap Actors BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/BoxOverlapActors) - Box overlap node
- [Instanced Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-materials-in-unreal-engine) - Material instances guide
- [UMaterialInstanceDynamic API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UMaterialInstanceDynamic) - MID C++ API
- [Set Scalar Parameter Value BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Rendering/Material/SetScalarParameterValue) - Scalar param node
- [Material Parameter Collections](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-material-parameter-collections-in-unreal-engine) - MPC guide
- [Programming Subsystems](https://dev.epicgames.com/documentation/en-us/unreal-engine/programming-subsystems-in-unreal-engine) - Subsystem guide
- [UGameInstanceSubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UGameInstanceSubsystem) - Game instance subsystem
- [UWorldSubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UWorldSubsystem) - World subsystem
- [USubsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/USubsystem) - Base subsystem
- [World Subsystems BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/WorldSubsystems) - World subsystem nodes
- [Get Data Table Row BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Utilities/GetDataTableRow) - Get row node
- [Get Data Table Row Names BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/DataTable/GetDataTableRowNames) - Get row names node
- [Get Data Table Row Struct BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/DataTable/GetDataTableRowStruct) - Get row struct node
- [Get Data Table Column as String BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/DataTable/GetDataTableColumnasString) - Column as string
- [DataTable BP Category](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/DataTable) - All DataTable nodes
- [Data Driven Gameplay](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-driven-gameplay-elements-in-unreal-engine) - DataTable usage guide
- [Blueprint Struct Variables](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-struct-variables-in-unreal-engine) - Struct usage in BP
- [Break Vector BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Vector/BreakVector) - Break Vector node
- [Make Vector BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Vector/MakeVector) - Make Vector node
- [Make Rotator BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Rotator/MakeRotator) - Make Rotator node
- [Break Rotator BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Rotator/BreakRotator) - Break Rotator node
- [Make Transform BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Transform/MakeTransform) - Make Transform node
- [Break Transform BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Transform/BreakTransform) - Break Transform node
- [Make Color BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Color/MakeColor) - Make Color node
- [FLinearColor API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/Math/FLinearColor) - Linear color struct
- [UKismetMathLibrary API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UKismetMathLibrary) - Math library (comparison, interp, random, clamp)
- [Math > Float BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Float) - Float math nodes
- [Math > Integer BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Integer) - Integer math nodes
- [Math > Boolean BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Boolean) - Boolean logic nodes
- [Math > Random BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Random) - Random nodes
- [Math > Interpolation BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Interpolation) - Interpolation nodes
- [Math > Vector BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Vector) - Vector nodes
- [Math > Rotator BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Rotator) - Rotator nodes
- [Math > Transform BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Transform) - Transform nodes
- [Math > Conversions BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Conversions) - Type conversion nodes
- [Lerp BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Float/Lerp) - Linear interpolation
- [FInterp To BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Interpolation/FInterpTo) - Framerate-independent interp
- [Nearly Equal (Float) BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Math/Float/NearlyEqual_Float) - Float approximate equality
- [Apply Damage BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/Damage/ApplyDamage) - Damage application
- [Apply Point Damage BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/Damage/ApplyPointDamage) - Point damage
- [Apply Radial Damage BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Kismet/UGameplayStatics/ApplyRadialDamage) - Radial damage
- [Set Static Mesh BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Components/StaticMesh/SetStaticMesh) - Static mesh component
- [Instanced Static Mesh BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Components/InstancedStaticMesh) - ISM nodes
- [UStaticMeshComponent API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UStaticMeshComponent) - Static mesh component C++
- [UAudioComponent API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UAudioComponent) - Audio component C++
- [Audio BP Category](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio) - All audio nodes
- [Play Sound 2D BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/PlaySound2D) - Fire-and-forget 2D sound
- [Spawn Sound 2D BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/SpawnSound2D) - Spawned 2D audio component
- [Create Sound 2D BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/CreateSound2D) - Created 2D audio component
- [Get Platform Name BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/GetPlatformName) - Platform detection
- [Viewport BP Category](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Viewport) - Viewport nodes
- [Get Viewport Size BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Viewport/GetViewportSize) - Viewport size
- [Project World to Screen BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Camera/ProjectWorldtoScreen) - World-to-screen projection
- [Get Player Camera Manager BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Game/GetPlayerCameraManager) - Camera manager access
- [EQS Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/environment-query-system-overview-in-unreal-engine) - EQS documentation
- [Run EQS Query BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/AI/EQS/RunEQSQuery) - EQS query node
- [EQS Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/environment-query-system-quick-start-in-unreal-engine) - EQS tutorial
- [Collision Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/collision-in-unreal-engine---overview) - Collision system overview
- [Collision BP Category](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision) - All collision nodes
- [On Component Begin Overlap BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/OnComponentBeginOverlap) - Overlap event
- [On Actor Begin Overlap BP](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Collision/OnActorBeginOverlap) - Actor overlap event
- [Random Streams](https://dev.epicgames.com/documentation/en-us/unreal-engine/random-streams-in-unreal-engine) - Seeded random guide
- [UE5 Blueprint API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI) - Full Blueprint API index
</references>

## Metadata

<meta>
research-date: 2026-02-06
confidence: high
version-checked: UE 5.7 (primary), UE 5.5/5.6 (secondary references)
source: dev.epicgames.com official documentation
total-nodes-documented: 400+
categories: Enhanced Input, Save Game, Collision/Traces, Materials, Subsystems, DataTables, Structs, Math Comparison, Interpolation, Random, Damage, Mesh/Static Mesh, Audio-Adjacent, Viewport/Screen, Platform Detection, EQS, Overlap Events, Type Conversions, UGameplayStatics
</meta>
