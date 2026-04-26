from pathlib import Path
import unittest

from usd_linter import load_config
from usd_linter.core.context import LintContext
from usd_linter.core.engine import LintEngine
from usd_linter.parser import parse_stage
from usd_linter.rules import create_default_registry


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _run_project(fixture_rel: str, project_name: str, config_rel: str | None = None) -> list:
    fixture_path = FIXTURE_DIR / fixture_rel
    config_path = FIXTURE_DIR / config_rel if config_rel else None
    stage = parse_stage(fixture_path)
    config = load_config(fixture_path, config_path=config_path, project_name=project_name)
    context = LintContext(
        file_path=fixture_path,
        parsed_stage=stage,
        config=config,
        project_name=project_name,
    )
    registry = create_default_registry()
    results = LintEngine(registry).run(context)
    return [msg for result in results for msg in result.messages]


class ProjectRuleTests(unittest.TestCase):
    def test_valid_project_file_passes_prefix_check(self) -> None:
        messages = _run_project(
            "project/Hero_Character.usda",
            "myproject",
            "project/project_rules.toml",
        )
        proj_ids = {m.rule_id for m in messages if m.rule_id.startswith("proj")}
        self.assertEqual(proj_ids, set())

    def test_missing_asset_prefix_is_reported(self) -> None:
        messages = _run_project(
            "project/invalid_project.usda",
            "myproject",
            "project/project_rules.toml",
        )
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("proj001_asset_name_prefix", rule_ids)

    def test_forbidden_prim_type_is_reported(self) -> None:
        messages = _run_project(
            "project/invalid_project.usda",
            "myproject",
            "project/project_rules.toml",
        )
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("proj005_forbidden_types", rule_ids)

    def test_project_rules_do_not_fire_without_project_name(self) -> None:
        fixture_path = FIXTURE_DIR / "project/invalid_project.usda"
        stage = parse_stage(fixture_path)
        config = load_config(fixture_path, config_path=FIXTURE_DIR / "project/project_rules.toml")
        context = LintContext(
            file_path=fixture_path,
            parsed_stage=stage,
            config=config,
        )
        registry = create_default_registry()
        results = LintEngine(registry).run(context)
        messages = [msg for result in results for msg in result.messages]
        rule_ids = {m.rule_id for m in messages}
        self.assertNotIn("proj001_asset_name_prefix", rule_ids)

    def test_disallowed_prim_type_is_reported(self) -> None:
        messages = _run_project(
            "project/invalid_project.usda",
            "myproject",
            "project/allowed_types_rules.toml",
        )
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("proj002_allowed_prim_types", rule_ids)

    def test_invalid_filename_is_reported(self) -> None:
        messages = _run_project(
            "project/invalid_project.usda",
            "myproject",
            "project/project_rules.toml",
        )
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("proj004_file_naming", rule_ids)
