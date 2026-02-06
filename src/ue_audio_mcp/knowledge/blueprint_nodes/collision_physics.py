"""Collision traces, overlap tests, and physics nodes.
Source: UKismetSystemLibrary, UGameplayStatics, UPrimitiveComponent.
"""
from __future__ import annotations
from ue_audio_mcp.knowledge.blueprint_nodes import _n

# --- COLLISION (32 nodes) ---
# Line Traces
_n("LineTraceSingle", "UKismetSystemLibrary", "collision", "Single line trace by trace channel", ["collision", "trace", "line", "raycast"])
_n("LineTraceMulti", "UKismetSystemLibrary", "collision", "Multi-hit line trace by trace channel", ["collision", "trace", "line", "multi"])
_n("LineTraceSingleByProfile", "UKismetSystemLibrary", "collision", "Single line trace by collision profile", ["collision", "trace", "line", "profile"])
_n("LineTraceMultiByProfile", "UKismetSystemLibrary", "collision", "Multi-hit line trace by profile", ["collision", "trace", "line", "profile"])
_n("LineTraceSingleForObjects", "UKismetSystemLibrary", "collision", "Single line trace for object types", ["collision", "trace", "line", "objects"])
_n("LineTraceMultiForObjects", "UKismetSystemLibrary", "collision", "Multi-hit line trace for objects", ["collision", "trace", "line", "objects"])
# Box Traces
_n("BoxTraceSingle", "UKismetSystemLibrary", "collision", "Single box sweep by trace channel", ["collision", "trace", "box", "sweep"])
_n("BoxTraceMulti", "UKismetSystemLibrary", "collision", "Multi-hit box sweep", ["collision", "trace", "box", "multi"])
_n("BoxTraceSingleByProfile", "UKismetSystemLibrary", "collision", "Single box sweep by collision profile", ["collision", "trace", "box", "profile"])
_n("BoxTraceMultiByProfile", "UKismetSystemLibrary", "collision", "Multi-hit box sweep by profile", ["collision", "trace", "box", "profile"])
_n("BoxTraceSingleForObjects", "UKismetSystemLibrary", "collision", "Single box sweep for object types", ["collision", "trace", "box", "objects"])
_n("BoxTraceMultiForObjects", "UKismetSystemLibrary", "collision", "Multi-hit box sweep for objects", ["collision", "trace", "box", "objects"])
# Sphere Traces
_n("SphereTraceSingle", "UKismetSystemLibrary", "collision", "Single sphere sweep", ["collision", "trace", "sphere", "sweep"])
_n("SphereTraceMulti", "UKismetSystemLibrary", "collision", "Multi-hit sphere sweep", ["collision", "trace", "sphere", "multi"])
_n("SphereTraceSingleByProfile", "UKismetSystemLibrary", "collision", "Single sphere sweep by profile", ["collision", "trace", "sphere", "profile"])
_n("SphereTraceMultiByProfile", "UKismetSystemLibrary", "collision", "Multi-hit sphere sweep by profile", ["collision", "trace", "sphere", "profile"])
_n("SphereTraceSingleForObjects", "UKismetSystemLibrary", "collision", "Single sphere sweep for objects", ["collision", "trace", "sphere", "objects"])
_n("SphereTraceMultiForObjects", "UKismetSystemLibrary", "collision", "Multi-hit sphere sweep for objects", ["collision", "trace", "sphere", "objects"])
# Capsule Traces
_n("CapsuleTraceSingle", "UKismetSystemLibrary", "collision", "Single capsule sweep", ["collision", "trace", "capsule", "sweep"])
_n("CapsuleTraceMulti", "UKismetSystemLibrary", "collision", "Multi-hit capsule sweep", ["collision", "trace", "capsule", "multi"])
_n("CapsuleTraceSingleByProfile", "UKismetSystemLibrary", "collision", "Single capsule sweep by profile", ["collision", "trace", "capsule", "profile"])
_n("CapsuleTraceMultiByProfile", "UKismetSystemLibrary", "collision", "Multi-hit capsule sweep by profile", ["collision", "trace", "capsule", "profile"])
_n("CapsuleTraceSingleForObjects", "UKismetSystemLibrary", "collision", "Single capsule sweep for objects", ["collision", "trace", "capsule", "objects"])
_n("CapsuleTraceMultiForObjects", "UKismetSystemLibrary", "collision", "Multi-hit capsule sweep for objects", ["collision", "trace", "capsule", "objects"])
# Overlap Tests
_n("BoxOverlapActors", "UKismetSystemLibrary", "collision", "Returns actors overlapping box", ["collision", "overlap", "box", "actors"])
_n("BoxOverlapComponents", "UKismetSystemLibrary", "collision", "Returns components overlapping box", ["collision", "overlap", "box", "components"])
_n("SphereOverlapActors", "UKismetSystemLibrary", "collision", "Returns actors overlapping sphere", ["collision", "overlap", "sphere", "actors"])
_n("SphereOverlapComponents", "UKismetSystemLibrary", "collision", "Returns components overlapping sphere", ["collision", "overlap", "sphere", "components"])
_n("CapsuleOverlapActors", "UKismetSystemLibrary", "collision", "Returns actors overlapping capsule", ["collision", "overlap", "capsule", "actors"])
_n("CapsuleOverlapComponents", "UKismetSystemLibrary", "collision", "Returns components overlapping capsule", ["collision", "overlap", "capsule", "components"])
_n("ComponentOverlapActors", "UKismetSystemLibrary", "collision", "Returns actors overlapping component", ["collision", "overlap", "component", "actors"])
_n("ComponentOverlapComponents", "UKismetSystemLibrary", "collision", "Returns components overlapping component", ["collision", "overlap", "component"])

# --- PHYSICS (5 nodes) ---
_n("BlueprintPredictProjectilePath_Advanced", "UGameplayStatics", "physics", "Full projectile prediction with collision", ["physics", "projectile", "trajectory"])
_n("BlueprintPredictProjectilePath_ByObjectType", "UGameplayStatics", "physics", "Prediction by object types", ["physics", "projectile", "objects"])
_n("BlueprintPredictProjectilePath_ByTraceChannel", "UGameplayStatics", "physics", "Prediction by trace channel", ["physics", "projectile", "trace"])
_n("SuggestProjectileVelocity", "UGameplayStatics", "physics", "Calculates launch velocity to hit target", ["physics", "projectile", "velocity"])
_n("GetSurfaceType", "UGameplayStatics", "physics", "Return physical surface type from hit result", ["physics", "surface", "material", "audio"])
