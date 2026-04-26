from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from usd_linter.cli import main


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class CLITests(unittest.TestCase):
    def test_help_includes_examples_epilog(self) -> None:
        buffer = io.StringIO()

        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(buffer):
                main(["--help"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("Examples:", buffer.getvalue())

    def test_version_flag_prints_installed_version(self) -> None:
        buffer = io.StringIO()

        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(buffer):
                main(["--version"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("usd-linter 0.1.0", buffer.getvalue())

    def test_text_output_renders_findings_and_ascii_suggestions(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main([str(FIXTURE_DIR / "invalid_asset.usda")])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR | unresolved_reference", output)
        self.assertIn("WARNING | suspicious_over_prim", output)
        self.assertIn("  -> ", output)

    def test_json_output_contains_summary_and_messages(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main([str(FIXTURE_DIR / "invalid_asset.usda"), "--format", "json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["files_scanned"], 1)
        self.assertGreaterEqual(payload["summary"]["error"], 1)
        self.assertTrue(payload["messages"])

    def test_invalid_target_returns_usage_exit_code(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main([str(FIXTURE_DIR / "does_not_exist.usda")])

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR:", buffer.getvalue())

    def test_valid_target_returns_success_exit_code(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main([str(FIXTURE_DIR / "valid_asset.usda")])

        self.assertEqual(exit_code, 0)
        self.assertIn("OK: no issues found", buffer.getvalue())

    def test_rules_filter_runs_only_requested_rule(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(
                [
                    str(FIXTURE_DIR / "invalid_asset.usda"),
                    "--rules",
                    "invalid_prim_name",
                ]
            )

        output = buffer.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("invalid_prim_name", output)
        self.assertNotIn("unresolved_reference", output)
        self.assertNotIn("suspicious_over_prim", output)

    def test_unknown_rules_filter_returns_config_error(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(
                [
                    str(FIXTURE_DIR / "valid_asset.usda"),
                    "--rules",
                    "not_a_real_rule",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown rule id", buffer.getvalue())

    def test_list_rules_prints_registered_rules_and_exits_zero(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["--list-rules", "--no-color"])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Registered rules", output)
        self.assertIn("invalid_prim_name", output)
        self.assertIn("singular_xform_matrix", output)
        self.assertIn("[core]", output)
        self.assertIn("[task:rig]", output)

    def test_explain_known_rule_prints_metadata(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["--explain", "singular_xform_matrix", "--no-color"])

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("singular_xform_matrix", output)
        self.assertIn("Title:", output)
        self.assertIn("Severity:", output)
        self.assertIn("WARNING", output)
        self.assertIn("Scope:", output)

    def test_explain_unknown_rule_returns_two(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["--explain", "not_a_real_rule", "--no-color"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown rule id", buffer.getvalue())

    def test_fix_flag_repairs_default_prim_and_returns_zero(self) -> None:
        from pxr import Usd, UsdGeom

        with tempfile.TemporaryDirectory() as temp_dir:
            stage_path = Path(temp_dir) / "asset.usda"
            stage = Usd.Stage.CreateNew(str(stage_path))
            UsdGeom.Xform.Define(stage, "/Asset")
            stage.GetRootLayer().Save()
            del stage

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main([str(stage_path), "--fix", "--no-color"])

            output = buffer.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("FIXED", output)
            self.assertIn("1 fixed", output)

            reopened = Usd.Stage.Open(str(stage_path))
            self.assertTrue(reopened.HasDefaultPrim())

    def test_missing_target_without_info_flags_returns_two(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main([])

        self.assertEqual(exit_code, 2)
        self.assertIn("target is required", buffer.getvalue())

    def test_contextual_smoke_fixture_passes(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(
                [
                    str(FIXTURE_DIR / "task/rig/contextual_rig_maya_demo.usda"),
                    "--task",
                    "rig",
                    "--dcc",
                    "maya",
                    "--project",
                    "demo",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("OK: no issues found", buffer.getvalue())
