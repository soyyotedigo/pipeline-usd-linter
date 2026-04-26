from pathlib import Path
import tempfile
import unittest

from usd_linter import load_config
from usd_linter.core.context import LintContext
from usd_linter.core.engine import LintEngine
from usd_linter.parser import _parse_stage_from_text, parse_stage
from usd_linter.rules import create_default_registry
from usd_linter.semantic import inspect_stage


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _run_rules(fixture_name: str, config_name: str | None = None):
    """Helper: parse a fixture, build a context, run all rules via engine."""
    fixture_path = FIXTURE_DIR / fixture_name
    stage = parse_stage(fixture_path)
    semantic_stage = inspect_stage(fixture_path)
    config_path = FIXTURE_DIR / config_name if config_name else None
    config = load_config(fixture_path, config_path=config_path)

    context = LintContext(
        file_path=fixture_path,
        parsed_stage=stage,
        semantic_stage=semantic_stage,
        config=config,
    )
    registry = create_default_registry()
    engine = LintEngine(registry)
    results = engine.run(context)

    messages = []
    for result in results:
        messages.extend(result.messages)
    return messages


class BuiltinRuleTests(unittest.TestCase):
    def test_boolean_rule_flags_activate_only_declared_checks(self) -> None:
        findings = _run_rules("invalid_asset.usda", "selective_rules.toml")
        rule_ids = {finding.rule_id for finding in findings}

        self.assertEqual(rule_ids, {"unresolved_reference"})

    def test_rule_specific_parameters_activate_rule(self) -> None:
        findings = _run_rules("invalid_asset.usda", "custom_rules.toml")
        self.assertEqual(findings, [])

    def test_invalid_prim_name_reports_prim_path_context(self) -> None:
        findings = _run_rules("invalid_asset.usda")
        invalid_name = next(f for f in findings if f.rule_id == "invalid_prim_name")

        self.assertEqual(invalid_name.prim_path, "/BadRoot/badMesh")

    def test_invalid_root_prim_reports_defaultprim_mismatch(self) -> None:
        findings = _run_rules("defaultprim_mismatch.usda")
        root_finding = next(f for f in findings if f.rule_id == "invalid_root_prim")

        self.assertIn("Asset", root_finding.message)
        self.assertIn("does not match", root_finding.message)

    def test_invalid_root_prim_passes_when_defaultprim_matches(self) -> None:
        findings = _run_rules("valid_asset.usda")
        root_findings = [f for f in findings if f.rule_id == "invalid_root_prim"]

        self.assertEqual(root_findings, [])

    def test_invalid_root_prim_reports_disallowed_root_name(self) -> None:
        findings = _run_rules("invalid_asset.usda")
        root_finding = next(f for f in findings if f.rule_id == "invalid_root_prim")

        self.assertIn("BadRoot", root_finding.message)
        self.assertIn("allowed set", root_finding.message)

    def test_allowed_root_prims_config_can_reject_otherwise_valid_root_name(self) -> None:
        findings = _run_rules("valid_asset.usda", "custom_rules.toml")
        root_finding = next(f for f in findings if f.rule_id == "invalid_root_prim")

        self.assertIn("Asset", root_finding.message)
        self.assertIn("BadRoot", root_finding.message)

    def test_max_hierarchy_depth_reports_deep_prims(self) -> None:
        findings = _run_rules("deep_hierarchy.usda", "max_depth_rules.toml")
        depth_finding = next(f for f in findings if f.rule_id == "max_hierarchy_depth")

        self.assertIn("maximum hierarchy depth of 3", depth_finding.message)
        self.assertEqual(depth_finding.prim_path, "/Asset/GrpA/GrpB/GrpC")

    def test_unresolved_composition_reports_reference_payload_and_sublayer(self) -> None:
        findings = _run_rules("invalid_composition.usda")
        rule_ids = {finding.rule_id for finding in findings}

        self.assertIn("unresolved_reference", rule_ids)
        self.assertIn("unresolved_payload", rule_ids)
        self.assertIn("unresolved_sublayer", rule_ids)

    def test_valid_composition_does_not_report_missing_paths(self) -> None:
        findings = _run_rules("valid_composition.usda")
        composition_ids = {
            finding.rule_id
            for finding in findings
            if finding.rule_id in {"unresolved_reference", "unresolved_payload", "unresolved_sublayer"}
        }

        self.assertEqual(composition_ids, set())

    def test_sublayer_cycle_is_reported(self) -> None:
        findings = _run_rules("cycles/cycle_a.usda")
        cycle_finding = next(f for f in findings if f.rule_id == "sublayer_cycle")

        self.assertIn("cycle_a.usda -> cycle_b.usda -> cycle_a.usda", cycle_finding.message)

    def test_acyclic_sublayers_do_not_trigger_cycle_rule(self) -> None:
        findings = _run_rules("cycles/acyclic_root.usda")
        cycle_findings = [f for f in findings if f.rule_id == "sublayer_cycle"]

        self.assertEqual(cycle_findings, [])

    def test_empty_over_without_composition_is_reported(self) -> None:
        findings = _run_rules("over_empty_no_composition.usda")
        over_finding = next(f for f in findings if f.rule_id == "suspicious_over_prim")

        self.assertIn("no references, payloads, or sublayers", over_finding.message)

    def test_meaningful_over_with_composition_is_not_reported(self) -> None:
        findings = _run_rules("over_meaningful_with_composition.usda")
        over_findings = [f for f in findings if f.rule_id == "suspicious_over_prim"]

        self.assertEqual(over_findings, [])

    def test_zero_or_negative_scale_is_reported(self) -> None:
        findings = _run_rules("invalid_scale.usda")
        scale_findings = [f for f in findings if f.rule_id == "zero_or_negative_scale"]

        severities = {f.severity for f in scale_findings}
        self.assertIn("error", severities)
        self.assertIn("warning", severities)

        prim_paths = {f.prim_path for f in scale_findings}
        self.assertIn("/Asset", prim_paths)
        self.assertIn("/Asset/NegativeChild", prim_paths)

    def test_nan_inf_values_are_reported(self) -> None:
        usda = (
            '#usda 1.0\n'
            '(\n    defaultPrim = "Asset"\n)\n\n'
            'def Xform "Asset" {\n'
            '    double3 xformOp:translate = (nan, 0, 0)\n'
            '    double3 xformOp:scale = (1, inf, 1)\n'
            '    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]\n'
            '}\n'
        )
        fixture_path = FIXTURE_DIR / "valid_asset.usda"
        stage = _parse_stage_from_text(fixture_path, usda)
        config = load_config(fixture_path)
        context = LintContext(file_path=fixture_path, parsed_stage=stage, config=config)
        results = LintEngine(create_default_registry()).run(context)
        findings = [m for r in results for m in r.messages if m.rule_id == "nan_inf_values"]

        messages = " ".join(f.message for f in findings)
        self.assertIn("nan", messages.lower())
        self.assertIn("inf", messages.lower())

    def test_absolute_asset_path_is_reported_for_ref_payload_and_sublayer(self) -> None:
        findings = _run_rules("absolute_paths.usda")
        abs_findings = [f for f in findings if f.rule_id == "absolute_asset_path"]

        messages = " ".join(f.message for f in abs_findings)
        self.assertIn("reference", messages)
        self.assertIn("payload", messages)
        self.assertIn("sublayer", messages)

    def test_performance_budgets_report_size_prims_and_payloads(self) -> None:
        findings = _run_rules("valid_composition.usda", "performance_rules.toml")
        rule_ids = {finding.rule_id for finding in findings}

        self.assertIn("perf001_stage_file_size", rule_ids)
        self.assertIn("perf002_prim_count", rule_ids)
        self.assertIn("perf003_payload_count", rule_ids)

    def test_unused_payload_is_reported_semantically(self) -> None:
        findings = _run_rules("unused_payload.usda")
        unused_payload = next(f for f in findings if f.rule_id == "perf004_unused_payload")

        self.assertEqual(unused_payload.prim_path, "/Asset")
        self.assertIn("does not compose any payload arc", unused_payload.message)

    def test_valid_payload_is_not_reported_as_unused(self) -> None:
        findings = _run_rules("valid_composition.usda")
        unused_payload_findings = [f for f in findings if f.rule_id == "perf004_unused_payload"]

        self.assertEqual(unused_payload_findings, [])


def _run_rules_on_stage(stage_path: Path) -> list:
    parsed_stage = parse_stage(stage_path)
    semantic_stage = inspect_stage(stage_path)
    config = load_config(stage_path)
    context = LintContext(
        file_path=stage_path,
        parsed_stage=parsed_stage,
        semantic_stage=semantic_stage,
        config=config,
    )
    engine = LintEngine(create_default_registry())
    messages: list = []
    for result in engine.run(context):
        messages.extend(result.messages)
    return messages


class SemanticRuleTests(unittest.TestCase):
    def test_singular_xform_matrix_is_reported(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            xform = UsdGeom.Xform.Define(stage, "/Asset")
            xform.AddScaleOp().Set((0.0, 1.0, 1.0))
            stage.SetDefaultPrim(xform.GetPrim())
            stage.GetRootLayer().Save()

            findings = _run_rules_on_stage(stage_path)

        singular = [f for f in findings if f.rule_id == "singular_xform_matrix"]
        self.assertEqual(len(singular), 1)
        self.assertEqual(singular[0].prim_path, "/Asset")
        self.assertEqual(singular[0].severity, "warning")

    def test_singular_xform_matrix_skipped_when_nan_or_inf(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            xform = UsdGeom.Xform.Define(stage, "/Asset")
            xform.AddScaleOp().Set((float("nan"), 1.0, 1.0))
            stage.SetDefaultPrim(xform.GetPrim())
            stage.GetRootLayer().Save()

            findings = _run_rules_on_stage(stage_path)

        singular = [f for f in findings if f.rule_id == "singular_xform_matrix"]
        self.assertEqual(singular, [])

    def test_unresolved_material_target_is_reported(self) -> None:
        from pxr import Sdf, Usd, UsdGeom, UsdShade

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            mesh = UsdGeom.Mesh.Define(stage, "/Asset/Body")
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
            rel = mesh.GetPrim().CreateRelationship("material:binding")
            rel.SetTargets([Sdf.Path("/Asset/Looks/MissingMat")])
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            findings = _run_rules_on_stage(stage_path)

        unresolved = [f for f in findings if f.rule_id == "unresolved_material_target"]
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].prim_path, "/Asset/Body")
        self.assertIn("/Asset/Looks/MissingMat", unresolved[0].message)
        self.assertEqual(unresolved[0].severity, "error")

    def test_unresolved_material_target_passes_when_target_exists(self) -> None:
        from pxr import Usd, UsdGeom, UsdShade

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            mesh = UsdGeom.Mesh.Define(stage, "/Asset/Body")
            material = UsdShade.Material.Define(stage, "/Asset/Looks/Mat")
            UsdShade.MaterialBindingAPI(mesh).Bind(material)
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            findings = _run_rules_on_stage(stage_path)

        unresolved = [f for f in findings if f.rule_id == "unresolved_material_target"]
        self.assertEqual(unresolved, [])
