from pathlib import Path
import unittest
from unittest.mock import patch

from usd_linter.core.context import LintContext
from usd_linter.core.models import LintMessage, RuleResult
from usd_linter.core.registry import BaseRule
from usd_linter.parser import ParsedStage
from usd_linter.rules import ENTRY_POINT_GROUP, RulePluginError, create_default_registry


class _EntryPoint:
    def __init__(self, name: str, loaded: object) -> None:
        self.name = name
        self._loaded = loaded

    def load(self) -> object:
        return self._loaded


class _EntryPoints(list):
    def select(self, *, group: str):
        if group == ENTRY_POINT_GROUP:
            return self
        return []


class _PluginRule(BaseRule):
    rule_id = "plugin001_sample"
    title = "Plugin sample rule"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        return RuleResult(
            messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Plugin rule executed.",
                    path=context.file_path,
                )
            ]
        )


class RulePluginTests(unittest.TestCase):
    def test_entry_point_rule_is_registered(self) -> None:
        entry_points = _EntryPoints([_EntryPoint("sample", _PluginRule)])

        with patch("usd_linter.rules.importlib_metadata.entry_points", return_value=entry_points):
            registry = create_default_registry()

        self.assertIn("plugin001_sample", {rule.rule_id for rule in registry.rules})

    def test_entry_point_factory_is_registered(self) -> None:
        entry_points = _EntryPoints([_EntryPoint("sample", _PluginRule)])

        with patch("usd_linter.rules.importlib_metadata.entry_points", return_value=entry_points):
            registry = create_default_registry()

        context = LintContext(
            file_path=Path("asset.usda"),
            parsed_stage=ParsedStage(path=Path("asset.usda")),
        )
        plugin_rule = next(rule for rule in registry.rules if rule.rule_id == "plugin001_sample")

        self.assertEqual(plugin_rule.check(context).messages[0].message, "Plugin rule executed.")

    def test_invalid_entry_point_type_raises_clear_error(self) -> None:
        entry_points = _EntryPoints([_EntryPoint("bad", object())])

        with patch("usd_linter.rules.importlib_metadata.entry_points", return_value=entry_points):
            with self.assertRaises(RulePluginError):
                create_default_registry()
