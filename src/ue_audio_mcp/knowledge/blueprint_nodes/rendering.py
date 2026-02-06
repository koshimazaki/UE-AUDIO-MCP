"""Rendering, material, and viewport nodes. Source: dev.epicgames.com."""
from __future__ import annotations
from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ===================================================================
# MATERIAL NODES (20 nodes) -- Category: material
# ===================================================================

_n("CreateDynamicMaterialInstance", "UPrimitiveComponent", "material",
   "Generate runtime-modifiable material instance",
   ["material", "dynamic", "create"])
_n("SetScalarParameterValue", "UMaterialInstanceDynamic", "material",
   "Set float parameter on dynamic material",
   ["material", "scalar", "parameter"])
_n("SetVectorParameterValue", "UMaterialInstanceDynamic", "material",
   "Set vector/color parameter on material",
   ["material", "vector", "color"])
_n("SetTextureParameterValue", "UMaterialInstanceDynamic", "material",
   "Set texture parameter on material",
   ["material", "texture", "parameter"])
_n("GetScalarParameterValue", "UMaterialInstanceDynamic", "material",
   "Get float parameter from material",
   ["material", "scalar", "get"])
_n("GetVectorParameterValue", "UMaterialInstanceDynamic", "material",
   "Get vector parameter from material",
   ["material", "vector", "get"])
_n("GetTextureParameterValue", "UMaterialInstanceDynamic", "material",
   "Get texture parameter from material",
   ["material", "texture", "get"])
_n("SetMaterial", "UPrimitiveComponent", "material",
   "Apply material to component at index",
   ["material", "set", "assign"])
_n("GetMaterial", "UPrimitiveComponent", "material",
   "Retrieve material from component",
   ["material", "get"])
_n("GetNumMaterials", "UPrimitiveComponent", "material",
   "Count materials on component",
   ["material", "count"])
_n("GetMaterialSlotNames", "UMeshComponent", "material",
   "Get all material slot names",
   ["material", "slot", "names"])
_n("CopyMaterialInstanceParameters", "UMaterialInstanceDynamic", "material",
   "Duplicate material parameters",
   ["material", "copy", "parameters"])
_n("InterpolateMaterialInstanceParameters", "UMaterialInstanceDynamic", "material",
   "Blend between material states",
   ["material", "interpolate", "blend"])
_n("SetCustomPrimitiveDataFloat", "UPrimitiveComponent", "material",
   "Set custom primitive data float",
   ["material", "primitive", "data"])
_n("SetScalarParameterValueOnMaterials", "UKismetMaterialLibrary", "material",
   "Set scalar across all materials",
   ["material", "scalar", "batch"])
_n("SetColorParameterValueOnMaterials", "UKismetMaterialLibrary", "material",
   "Apply color across all materials",
   ["material", "color", "batch"])
_n("GetBaseMaterial", "UMaterialInterface", "material",
   "Get base material reference",
   ["material", "base", "parent"])
_n("SetRuntimeVirtualTextureParameterValue", "UMaterialInstanceDynamic", "material",
   "Set RVT parameter",
   ["material", "virtual", "texture"])
_n("GetBlendMode", "UMaterialInterface", "material",
   "Get material blend mode",
   ["material", "blend", "mode"])
_n("SetOverlayMaterial", "UMeshComponent", "material",
   "Apply overlay material layer",
   ["material", "overlay", "set"])
