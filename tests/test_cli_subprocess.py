import json
from pathlib import Path
import subprocess
import sys
import unittest


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "usd_linter.cli", *args],
        check=False,
        capture_output=True,
        text=True,
    )


class CLISubprocessSmokeTests(unittest.TestCase):
    def test_text_output_smoke(self) -> None:
        result = _run_cli(str(FIXTURE_DIR / "valid_asset.usda"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("OK: no issues found", result.stdout)

    def test_json_output_smoke(self) -> None:
        result = _run_cli(str(FIXTURE_DIR / "valid_asset.usda"), "--format", "json")

        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["files_scanned"], 1)
        self.assertEqual(payload["messages"], [])

    def test_context_task_dcc_project_smoke(self) -> None:
        result = _run_cli(
            str(FIXTURE_DIR / "task/rig/contextual_rig_maya_demo.usda"),
            "--task",
            "rig",
            "--dcc",
            "maya",
            "--project",
            "demo",
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("OK: no issues found", result.stdout)

    def test_exit_code_2_smoke(self) -> None:
        result = _run_cli(str(FIXTURE_DIR / "does_not_exist.usda"))

        self.assertEqual(result.returncode, 2)
        self.assertIn("ERROR:", result.stdout)
