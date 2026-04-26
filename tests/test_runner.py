from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from usd_linter import load_config, run_linter
from usd_linter.parser import ParseError, ParsedPrim, ParsedStage
from usd_linter.runner import LinterExecutionError
from usd_linter.semantic import SemanticStage


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class RunnerTests(unittest.TestCase):
    def test_valid_fixture_has_no_findings(self) -> None:
        report = run_linter(load_config(FIXTURE_DIR / "valid_asset.usda"))

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(report.messages, [])

    def test_invalid_fixture_reports_all_base_rules(self) -> None:
        report = run_linter(load_config(FIXTURE_DIR / "invalid_asset.usda"))
        rule_ids = {message.rule_id for message in report.messages}

        self.assertTrue(
            {
                "invalid_prim_name",
                "unresolved_reference",
                "invalid_root_prim",
                "suspicious_over_prim",
                "missing_required_metadata",
            }.issubset(rule_ids)
        )

    def test_directory_target_scans_matching_layers(self) -> None:
        # Scan the refs/ sub-directory which contains exactly 1 file.
        report = run_linter(load_config(FIXTURE_DIR / "refs"))

        self.assertEqual(report.files_scanned, 1)

    def test_directory_target_reports_parse_errors_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            good_path = target / "good.usda"
            broken_path = target / "broken.usda"
            good_path.write_text("#usda 1.0\n", encoding="utf-8")
            broken_path.write_text("not usd\n", encoding="utf-8")

            def fake_parse_file(path: Path) -> tuple[ParsedStage, SemanticStage, object]:
                if path.name == "broken.usda":
                    raise ParseError("synthetic parse failure")
                stage = ParsedStage(
                    path=path,
                    prims=[
                        ParsedPrim(
                            name="Asset",
                            specifier="def",
                            path="/Asset",
                            line=1,
                            type_name="Xform",
                        )
                    ],
                    stage_metadata={"defaultPrim": "Asset"},
                )
                return (
                    stage,
                    SemanticStage(path=path, root_layer_identifier=str(path)),
                    object(),
                )

            with patch("usd_linter.runner._parse_file", side_effect=fake_parse_file):
                report = run_linter(load_config(target))

        parse_errors = [
            message for message in report.messages if message.rule_id == "parse_error"
        ]
        self.assertEqual(report.files_scanned, 2)
        self.assertEqual(len(parse_errors), 1)
        self.assertEqual(parse_errors[0].path, broken_path.resolve())
        self.assertIn("synthetic parse failure", parse_errors[0].message)

    def test_single_file_parse_error_remains_execution_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "broken.usda"
            file_path.write_text("not usd\n", encoding="utf-8")

            with patch("usd_linter.runner._parse_file", side_effect=ParseError("synthetic")):
                with self.assertRaises(LinterExecutionError):
                    run_linter(load_config(file_path))

    def test_runs_lint_pipeline_on_usdc_binary(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usdc"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            UsdGeom.Mesh.Define(stage, "/Asset/Body")
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            self.assertTrue(stage_path.exists())
            self.assertGreater(stage_path.stat().st_size, 0)
            with stage_path.open("rb") as fh:
                self.assertNotEqual(fh.read(8), b"#usda 1.")

            report = run_linter(load_config(stage_path))

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(
            [m for m in report.messages if m.severity == "error"],
            [],
            msg=f"Unexpected errors on USDC fixture: {report.messages}",
        )

    def test_runs_lint_pipeline_on_usdc_with_invalid_naming(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usdc"
            stage = Usd.Stage.CreateNew(str(stage_path))
            root = UsdGeom.Xform.Define(stage, "/Asset")
            UsdGeom.Mesh.Define(stage, "/Asset/badName")
            stage.SetDefaultPrim(root.GetPrim())
            stage.GetRootLayer().Save()

            report = run_linter(load_config(stage_path))

        rule_ids = {m.rule_id for m in report.messages}
        self.assertIn("invalid_prim_name", rule_ids)

    def test_apply_fixes_repairs_missing_default_prim(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            UsdGeom.Xform.Define(stage, "/Asset")
            stage.GetRootLayer().Save()
            del stage

            report = run_linter(load_config(stage_path), apply_fixes=True)

            metadata_msgs = [m for m in report.messages if m.rule_id == "missing_required_metadata"]
            self.assertEqual(len(metadata_msgs), 1)
            self.assertTrue(metadata_msgs[0].fixed)
            self.assertFalse(report.should_fail("error"))

            reopened = Usd.Stage.Open(str(stage_path))
            self.assertTrue(reopened.HasDefaultPrim())
            self.assertEqual(reopened.GetDefaultPrim().GetName(), "Asset")

    def test_apply_fixes_skips_when_multiple_root_prims(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            UsdGeom.Xform.Define(stage, "/Asset")
            UsdGeom.Xform.Define(stage, "/Other")
            stage.GetRootLayer().Save()
            del stage

            report = run_linter(load_config(stage_path), apply_fixes=True)

            metadata_msgs = [m for m in report.messages if m.rule_id == "missing_required_metadata"]
            self.assertEqual(len(metadata_msgs), 1)
            self.assertFalse(metadata_msgs[0].fixed)

            reopened = Usd.Stage.Open(str(stage_path))
            self.assertFalse(reopened.HasDefaultPrim())
