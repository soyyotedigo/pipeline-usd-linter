from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path

from .parser import ParseError, open_stage, suppress_pxr_diagnostics
from .rules.core._composition import resolve_asset_path


@dataclass(slots=True)
class SemanticPrim:
    path: str
    name: str
    type_name: str
    specifier: str
    active: bool
    defined: bool
    abstract: bool
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class CompositionArcInfo:
    arc_type: str
    owner_path: str
    introducing_prim_path: str
    target_prim_path: str
    introducing_layer_identifier: str | None
    target_layer_identifier: str | None
    has_specs: bool
    implicit: bool


@dataclass(slots=True)
class AuthoredPayloadInfo:
    prim_path: str
    asset_path: str
    target_prim_path: str
    resolved_path: Path | None
    has_composed_arc: bool


@dataclass(slots=True)
class MaterialBindingInfo:
    prim_path: str
    bound_material_path: str | None
    relationship_targets: tuple[str, ...] = ()
    is_resolved: bool = False


@dataclass(slots=True)
class VariantSetInfo:
    prim_path: str
    set_name: str
    variant_names: tuple[str, ...]
    selection: str | None
    has_authored_selection: bool


@dataclass(slots=True)
class XformStackInfo:
    prim_path: str
    reset_stack: bool
    op_order: tuple[str, ...]
    local_matrix: tuple[tuple[float, ...], ...]
    world_matrix: tuple[tuple[float, ...], ...]
    determinant: float
    is_singular: bool
    has_nan_or_inf: bool


@dataclass(slots=True)
class SemanticStage:
    path: Path
    root_layer_identifier: str
    default_prim: str | None = None
    prims: list[SemanticPrim] = field(default_factory=list)
    composition_arcs: list[CompositionArcInfo] = field(default_factory=list)
    authored_payloads: list[AuthoredPayloadInfo] = field(default_factory=list)
    material_bindings: list[MaterialBindingInfo] = field(default_factory=list)
    variant_sets: list[VariantSetInfo] = field(default_factory=list)
    xforms: list[XformStackInfo] = field(default_factory=list)


def inspect_stage(file_path: Path, pxr_stage=None) -> SemanticStage:
    file_path = file_path.resolve()
    if pxr_stage is None:
        pxr_stage = open_stage(file_path)

    try:
        from pxr import Pcp, Usd, UsdGeom, UsdShade
    except ImportError as exc:
        raise ParseError("usd-core is required. Install it with: pip install usd-core") from exc

    root_layer = pxr_stage.GetRootLayer()
    default_prim = pxr_stage.GetDefaultPrim()
    xform_cache = UsdGeom.XformCache()
    semantic_stage = SemanticStage(
        path=file_path,
        root_layer_identifier=getattr(root_layer, "identifier", str(file_path)),
        default_prim=default_prim.GetPath().pathString if default_prim else None,
    )

    with suppress_pxr_diagnostics():
        for prim in pxr_stage.TraverseAll():
            semantic_stage.prims.append(_inspect_prim(prim))
            arcs = _inspect_composition_arcs(prim, Usd)
            semantic_stage.composition_arcs.extend(arcs)
            semantic_stage.authored_payloads.extend(
                _inspect_authored_payloads(prim, arcs, Pcp.ArcTypePayload, file_path.parent)
            )
            material_binding = _inspect_material_binding(prim, UsdShade)
            if material_binding is not None:
                semantic_stage.material_bindings.append(material_binding)
            semantic_stage.variant_sets.extend(_inspect_variant_sets(prim))
            xform = _inspect_xform_stack(prim, UsdGeom, xform_cache)
            if xform is not None:
                semantic_stage.xforms.append(xform)

    return semantic_stage


def _inspect_prim(prim) -> SemanticPrim:
    return SemanticPrim(
        path=prim.GetPath().pathString,
        name=prim.GetName(),
        type_name=prim.GetTypeName(),
        specifier=str(prim.GetSpecifier()),
        active=prim.IsActive(),
        defined=prim.IsDefined(),
        abstract=prim.IsAbstract(),
        metadata={key: str(value) for key, value in prim.GetAllMetadata().items()},
    )


def _inspect_composition_arcs(prim, usd_module) -> list[CompositionArcInfo]:
    owner_path = prim.GetPath().pathString
    arcs: list[CompositionArcInfo] = []
    for arc in usd_module.PrimCompositionQuery(prim).GetCompositionArcs():
        introducing_layer = arc.GetIntroducingLayer()
        target_layer = arc.GetTargetLayer()
        arcs.append(
            CompositionArcInfo(
                arc_type=str(arc.GetArcType()),
                owner_path=owner_path,
                introducing_prim_path=arc.GetIntroducingPrimPath().pathString,
                target_prim_path=arc.GetTargetPrimPath().pathString,
                introducing_layer_identifier=(
                    introducing_layer.identifier if introducing_layer is not None else None
                ),
                target_layer_identifier=target_layer.identifier if target_layer is not None else None,
                has_specs=arc.HasSpecs(),
                implicit=arc.IsImplicit(),
            )
        )
    return arcs


def _inspect_authored_payloads(
    prim,
    arcs: list[CompositionArcInfo],
    payload_arc_type,
    anchor_dir: Path,
) -> list[AuthoredPayloadInfo]:
    payload_list = prim.GetMetadata("payload")
    if payload_list is None:
        return []

    payload_arc_type_text = str(payload_arc_type)
    authored_payloads: list[AuthoredPayloadInfo] = []
    for payload in payload_list.GetAppliedItems():
        asset_path = payload.assetPath
        target_prim_path = getattr(payload.primPath, "pathString", "")
        resolved_path = resolve_asset_path(anchor_dir, asset_path) if asset_path else None
        authored_payloads.append(
            AuthoredPayloadInfo(
                prim_path=prim.GetPath().pathString,
                asset_path=asset_path,
                target_prim_path=target_prim_path,
                resolved_path=resolved_path,
                has_composed_arc=_payload_has_composed_arc(
                    arcs,
                    payload_arc_type_text,
                    resolved_path,
                    target_prim_path,
                ),
            )
        )
    return authored_payloads


def _payload_has_composed_arc(
    arcs: list[CompositionArcInfo],
    payload_arc_type: str,
    resolved_path: Path | None,
    target_prim_path: str,
) -> bool:
    for arc in arcs:
        if arc.arc_type != payload_arc_type:
            continue
        if resolved_path is not None and not _same_layer(resolved_path, arc.target_layer_identifier):
            continue
        if target_prim_path and arc.target_prim_path != target_prim_path:
            continue
        if arc.has_specs:
            return True
    return False


def _inspect_material_binding(prim, usd_shade_module) -> MaterialBindingInfo | None:
    try:
        material, relationship = usd_shade_module.MaterialBindingAPI(prim).ComputeBoundMaterial()
    except Exception:
        return None

    relationship_targets: tuple[str, ...] = ()
    if relationship and relationship.IsValid():
        relationship_targets = tuple(target.pathString for target in relationship.GetTargets())

    bound_material_path = None
    if material and material.GetPrim().IsValid():
        bound_material_path = material.GetPath().pathString

    if bound_material_path is None and not relationship_targets:
        return None

    return MaterialBindingInfo(
        prim_path=prim.GetPath().pathString,
        bound_material_path=bound_material_path,
        relationship_targets=relationship_targets,
        is_resolved=bound_material_path is not None,
    )


def _inspect_variant_sets(prim) -> list[VariantSetInfo]:
    variant_sets = prim.GetVariantSets()
    infos: list[VariantSetInfo] = []
    for set_name in variant_sets.GetNames():
        variant_set = variant_sets.GetVariantSet(set_name)
        selection = variant_set.GetVariantSelection() or None
        infos.append(
            VariantSetInfo(
                prim_path=prim.GetPath().pathString,
                set_name=set_name,
                variant_names=tuple(variant_set.GetVariantNames()),
                selection=selection,
                has_authored_selection=variant_set.HasAuthoredVariantSelection(),
            )
        )
    return infos


def _inspect_xform_stack(prim, usd_geom_module, xform_cache) -> XformStackInfo | None:
    xformable = usd_geom_module.Xformable(prim)
    if not xformable:
        return None

    try:
        local_matrix = xformable.GetLocalTransformation()
        world_matrix = xform_cache.GetLocalToWorldTransform(prim)
    except Exception:
        return None

    local_tuple = _matrix_to_tuple(local_matrix)
    world_tuple = _matrix_to_tuple(world_matrix)
    determinant = float(world_matrix.GetDeterminant())
    values = [value for row in local_tuple + world_tuple for value in row]
    return XformStackInfo(
        prim_path=prim.GetPath().pathString,
        reset_stack=xformable.GetResetXformStack(),
        op_order=tuple(op.GetOpName() for op in xformable.GetOrderedXformOps()),
        local_matrix=local_tuple,
        world_matrix=world_tuple,
        determinant=determinant,
        is_singular=abs(determinant) < 1e-12,
        has_nan_or_inf=any(not math.isfinite(value) for value in values),
    )


def _matrix_to_tuple(matrix) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(matrix[row][column]) for column in range(4)) for row in range(4))


def _same_layer(expected_path: Path, layer_identifier: str | None) -> bool:
    if layer_identifier is None:
        return False
    try:
        return expected_path.resolve() == Path(layer_identifier).resolve()
    except OSError:
        return str(expected_path) == layer_identifier
