"""Rule registration and default registry factory."""

from importlib import metadata as importlib_metadata

from ..core.registry import BaseRule, RuleRegistry

# --- Core rules ---
from .core.comp001_broken_references import BrokenReferencesRule
from .core.comp002_broken_payloads import BrokenPayloadsRule
from .core.comp003_broken_sublayers import BrokenSublayersRule
from .core.comp004_sublayer_cycle import SublayerCycleRule
from .core.comp005_absolute_asset_path import AbsoluteAssetPathRule
from .core.meta001_missing_metadata import MissingMetadataRule
from .core.naming001_prim_name import PrimNameRule
from .core.struct001_suspicious_over import SuspiciousOverRule
from .core.struct002_invalid_root_prim import InvalidRootPrimRule
from .core.struct003_max_hierarchy_depth import MaxHierarchyDepthRule
from .core.mat001_unresolved_material_target import UnresolvedMaterialTargetRule
from .core.xform001_zero_or_negative_scale import ZeroOrNegativeScaleRule
from .core.xform002_nan_inf_values import NanInfValuesRule
from .core.xform003_singular_matrix import SingularMatrixRule
from .performance.perf001_stage_file_size import StageFileSizeRule
from .performance.perf002_prim_count import PrimCountRule
from .performance.perf003_payload_count import PayloadCountRule
from .performance.perf004_unused_payload import UnusedPayloadRule

# --- Task: rig ---
from .task.rig.rig001_has_skeleton import RigHasSkeletonRule
from .task.rig.rig002_has_skel_root import RigHasSkelRootRule
from .task.rig.rig003_joint_naming import RigJointNamingRule
from .task.rig.rig004_no_mesh_at_root import RigNoMeshAtRootRule
from .task.rig.rig005_duplicate_joint_names import RigDuplicateJointNamesRule

# --- Task: model ---
from .task.model.model001_has_geometry import ModelHasGeometryRule
from .task.model.model002_lod_naming import ModelLodNamingRule
from .task.model.model003_no_lights import ModelNoLightsRule
from .task.model.model005_no_cameras import ModelNoCamerasRule

# --- Task: anim ---
from .task.anim.anim001_has_skel_animation import AnimHasSkelAnimationRule
from .task.anim.anim002_has_skel_root import AnimHasSkelRootRule
from .task.anim.anim003_no_geometry import AnimNoGeometryRule

# --- Task: layout ---
from .task.layout.layout001_has_xform_root import LayoutHasXformRootRule
from .task.layout.layout003_has_references import LayoutHasReferencesRule
from .task.layout.layout004_camera_naming import LayoutCameraNamingRule

# --- Task: lookdev ---
from .task.lookdev.lookdev001_has_material import LookdevHasMaterialRule
from .task.lookdev.lookdev002_looks_scope import LookdevLooksScopeRule
from .task.lookdev.lookdev003_mesh_without_binding import LookdevMeshWithoutBindingRule

# --- DCC: maya ---
from .dcc.maya.maya001_namespace_clean import MayaNamespaceCleanRule
from .dcc.maya.maya002_shape_node_naming import MayaShapeNodeNamingRule
from .dcc.maya.maya004_transform_as_xform import MayaTransformAsXformRule

# --- DCC: houdini ---
from .dcc.houdini.houdini001_lopnet_prims import HoudiniLopnetPrimsRule
from .dcc.houdini.houdini002_primitive_path import HoudiniPrimitivePathRule

# --- DCC: blender ---
from .dcc.blender.blender002_material_naming import BlenderMaterialNamingRule
from .dcc.blender.blender003_armature_skeleton import BlenderArmatureSkeletonRule

# --- Project rules ---
from .project.proj001_asset_name_prefix import ProjectAssetNamePrefixRule
from .project.proj002_allowed_prim_types import ProjectAllowedPrimTypesRule
from .project.proj004_file_naming import ProjectFileNamingRule
from .project.proj005_forbidden_types import ProjectForbiddenTypesRule


ENTRY_POINT_GROUP = "usd_linter.rules"


class RulePluginError(RuntimeError):
    """Raised when an external rule plugin cannot be loaded."""


def _register_core_rules(registry: RuleRegistry) -> None:
    registry.register(PrimNameRule())
    registry.register(BrokenReferencesRule())
    registry.register(BrokenPayloadsRule())
    registry.register(BrokenSublayersRule())
    registry.register(SublayerCycleRule())
    registry.register(SuspiciousOverRule())
    registry.register(MissingMetadataRule())
    registry.register(InvalidRootPrimRule())
    registry.register(MaxHierarchyDepthRule())
    registry.register(AbsoluteAssetPathRule())
    registry.register(ZeroOrNegativeScaleRule())
    registry.register(NanInfValuesRule())
    registry.register(SingularMatrixRule())
    registry.register(UnresolvedMaterialTargetRule())


def _register_performance_rules(registry: RuleRegistry) -> None:
    registry.register(StageFileSizeRule())
    registry.register(PrimCountRule())
    registry.register(PayloadCountRule())
    registry.register(UnusedPayloadRule())


def _register_task_rules(registry: RuleRegistry) -> None:
    # rig
    registry.register(RigHasSkeletonRule())
    registry.register(RigHasSkelRootRule())
    registry.register(RigJointNamingRule())
    registry.register(RigNoMeshAtRootRule())
    registry.register(RigDuplicateJointNamesRule())
    # model
    registry.register(ModelHasGeometryRule())
    registry.register(ModelLodNamingRule())
    registry.register(ModelNoLightsRule())
    registry.register(ModelNoCamerasRule())
    # anim
    registry.register(AnimHasSkelAnimationRule())
    registry.register(AnimHasSkelRootRule())
    registry.register(AnimNoGeometryRule())
    # layout
    registry.register(LayoutHasXformRootRule())
    registry.register(LayoutHasReferencesRule())
    registry.register(LayoutCameraNamingRule())
    # lookdev
    registry.register(LookdevHasMaterialRule())
    registry.register(LookdevLooksScopeRule())
    registry.register(LookdevMeshWithoutBindingRule())


def _register_dcc_rules(registry: RuleRegistry) -> None:
    # maya
    registry.register(MayaNamespaceCleanRule())
    registry.register(MayaShapeNodeNamingRule())
    registry.register(MayaTransformAsXformRule())
    # houdini
    registry.register(HoudiniLopnetPrimsRule())
    registry.register(HoudiniPrimitivePathRule())
    # blender
    registry.register(BlenderMaterialNamingRule())
    registry.register(BlenderArmatureSkeletonRule())


def _register_project_rules(registry: RuleRegistry) -> None:
    registry.register(ProjectAssetNamePrefixRule())
    registry.register(ProjectAllowedPrimTypesRule())
    registry.register(ProjectFileNamingRule())
    registry.register(ProjectForbiddenTypesRule())


def _register_entry_point_rules(registry: RuleRegistry) -> None:
    existing_rule_ids = {rule.rule_id for rule in registry.rules}
    for entry_point in _rule_entry_points():
        rule = _load_entry_point_rule(entry_point)
        if rule.rule_id in existing_rule_ids:
            raise RulePluginError(
                f"Rule plugin {entry_point.name!r} declares duplicate rule id {rule.rule_id!r}."
            )
        registry.register(rule)
        existing_rule_ids.add(rule.rule_id)


def _rule_entry_points():
    try:
        entry_points = importlib_metadata.entry_points()
    except Exception as exc:  # pragma: no cover - depends on installed metadata state
        raise RulePluginError(f"Failed to read rule plugin entry points: {exc}") from exc

    if hasattr(entry_points, "select"):
        return entry_points.select(group=ENTRY_POINT_GROUP)
    return entry_points.get(ENTRY_POINT_GROUP, ())


def _load_entry_point_rule(entry_point) -> BaseRule:
    try:
        loaded = entry_point.load()
        if isinstance(loaded, BaseRule):
            return loaded
        if isinstance(loaded, type) and issubclass(loaded, BaseRule):
            return loaded()
        if callable(loaded):
            candidate = loaded()
            if isinstance(candidate, BaseRule):
                return candidate
    except RulePluginError:
        raise
    except Exception as exc:
        raise RulePluginError(f"Failed to load rule plugin {entry_point.name!r}: {exc}") from exc

    raise RulePluginError(
        f"Rule plugin {entry_point.name!r} must load to a BaseRule subclass, "
        "BaseRule instance, or zero-argument factory returning a BaseRule."
    )


def create_default_registry(*, include_entry_points: bool = True) -> RuleRegistry:
    """Build a registry with all built-in rules."""
    registry = RuleRegistry()
    _register_core_rules(registry)
    _register_performance_rules(registry)
    _register_task_rules(registry)
    _register_dcc_rules(registry)
    _register_project_rules(registry)
    if include_entry_points:
        _register_entry_point_rules(registry)
    return registry


def get_supported_rule_ids() -> tuple[str, ...]:
    """Derive supported rule IDs from the default registry."""
    return tuple(rule.rule_id for rule in create_default_registry().rules)
