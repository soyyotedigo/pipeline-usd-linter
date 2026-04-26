from pathlib import Path
import tempfile
import unittest

from usd_linter.semantic import inspect_stage


class SemanticInspectionTests(unittest.TestCase):
    def test_inspects_prims_variants_xforms_materials_and_payloads(self) -> None:
        from pxr import Usd, UsdGeom, UsdShade

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            payload_path = temp_path / "payload.usda"
            payload_stage = Usd.Stage.CreateNew(str(payload_path))
            payload_root = payload_stage.DefinePrim("/PayloadRoot", "Xform")
            payload_stage.SetDefaultPrim(payload_root)
            payload_stage.GetRootLayer().Save()

            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            root.AddTranslateOp().Set((1.0, 2.0, 3.0))
            root.GetPrim().GetPayloads().AddPayload(str(payload_path))
            mesh = UsdGeom.Mesh.Define(stage, "/Asset/Body")
            material = UsdShade.Material.Define(stage, "/Asset/Looks/Mat")
            UsdShade.MaterialBindingAPI(mesh).Bind(material)
            variant_set = root.GetPrim().GetVariantSets().AddVariantSet("lod")
            variant_set.AddVariant("high")
            variant_set.SetVariantSelection("high")
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            opened_stage = Usd.Stage.Open(str(stage_path))
            semantic_stage = inspect_stage(stage_path, opened_stage)

        self.assertEqual(semantic_stage.default_prim, "/Asset")
        self.assertIn("/Asset", {prim.path for prim in semantic_stage.prims})
        self.assertTrue(any(arc.arc_type.endswith("ArcTypePayload") for arc in semantic_stage.composition_arcs))
        self.assertTrue(any(payload.has_composed_arc for payload in semantic_stage.authored_payloads))
        self.assertIn("/Asset/Looks/Mat", {binding.bound_material_path for binding in semantic_stage.material_bindings})
        self.assertIn("lod", {variant.set_name for variant in semantic_stage.variant_sets})
        self.assertIn("/Asset", {xform.prim_path for xform in semantic_stage.xforms})

    def test_payload_without_composed_arc_is_flagged(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            root.GetPrim().GetPayloads().AddPayload("./does_not_exist.usda")
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            opened_stage = Usd.Stage.Open(str(stage_path))
            semantic_stage = inspect_stage(stage_path, opened_stage)

        authored = [p for p in semantic_stage.authored_payloads if p.prim_path == "/Asset"]
        self.assertEqual(len(authored), 1)
        self.assertFalse(authored[0].has_composed_arc)
        self.assertEqual(authored[0].asset_path, "./does_not_exist.usda")

    def test_material_binding_with_missing_target_is_unresolved(self) -> None:
        from pxr import Sdf, Usd, UsdGeom, UsdShade

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            mesh = UsdGeom.Mesh.Define(stage, "/Asset/Body")
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
            rel = mesh.GetPrim().CreateRelationship("material:binding")
            rel.SetTargets([Sdf.Path("/Asset/Looks/MissingMat")])
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            opened_stage = Usd.Stage.Open(str(stage_path))
            semantic_stage = inspect_stage(stage_path, opened_stage)

        bindings = {b.prim_path: b for b in semantic_stage.material_bindings}
        self.assertIn("/Asset/Body", bindings)
        binding = bindings["/Asset/Body"]
        self.assertFalse(binding.is_resolved)
        self.assertIn("/Asset/Looks/MissingMat", binding.relationship_targets)

    def test_singular_xform_stack_is_detected(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            xform = UsdGeom.Xform.Define(stage, "/Asset")
            xform.AddScaleOp().Set((0.0, 1.0, 1.0))
            stage.SetDefaultPrim(xform.GetPrim())
            stage.GetRootLayer().Save()

            opened_stage = Usd.Stage.Open(str(stage_path))
            semantic_stage = inspect_stage(stage_path, opened_stage)

        xforms = {x.prim_path: x for x in semantic_stage.xforms}
        self.assertIn("/Asset", xforms)
        info = xforms["/Asset"]
        self.assertTrue(info.is_singular)
        self.assertAlmostEqual(info.determinant, 0.0)
        self.assertFalse(info.has_nan_or_inf)

    def test_variant_set_without_authored_selection(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            variant_set = root.GetPrim().GetVariantSets().AddVariantSet("lod")
            variant_set.AddVariant("high")
            variant_set.AddVariant("low")
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            opened_stage = Usd.Stage.Open(str(stage_path))
            semantic_stage = inspect_stage(stage_path, opened_stage)

        variants = [v for v in semantic_stage.variant_sets if v.set_name == "lod"]
        self.assertEqual(len(variants), 1)
        self.assertFalse(variants[0].has_authored_selection)
        self.assertIn("high", variants[0].variant_names)
        self.assertIn("low", variants[0].variant_names)

    def test_inspect_stage_opens_path_when_no_stage_provided(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stage_path = temp_path / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            UsdGeom.Xform.Define(stage, "/Asset")
            stage.GetRootLayer().Save()

            semantic_stage = inspect_stage(stage_path)

        self.assertIn("/Asset", {prim.path for prim in semantic_stage.prims})
