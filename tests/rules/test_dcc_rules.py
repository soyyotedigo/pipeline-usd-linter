from pathlib import Path
import unittest

from usd_linter import load_config
from usd_linter.core.context import LintContext
from usd_linter.core.engine import LintEngine
from usd_linter.parser import parse_stage, _parse_stage_from_text
from usd_linter.rules import create_default_registry


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _run_dcc(fixture_rel: str, target_dcc: str) -> list:
    fixture_path = FIXTURE_DIR / fixture_rel
    stage = parse_stage(fixture_path)
    config = load_config(fixture_path, target_dcc=target_dcc)
    context = LintContext(
        file_path=fixture_path,
        parsed_stage=stage,
        config=config,
        target_dcc=target_dcc,
    )
    registry = create_default_registry()
    results = LintEngine(registry).run(context)
    return [msg for result in results for msg in result.messages]


class MayaRuleTests(unittest.TestCase):
    def test_valid_maya_file_has_no_maya_findings(self) -> None:
        messages = _run_dcc("dcc/maya/valid_maya.usda", "maya")
        maya_ids = {m.rule_id for m in messages if m.rule_id.startswith("maya")}
        self.assertEqual(maya_ids, set())

    def test_maya_namespace_in_prim_name_is_reported(self) -> None:
        usda = '#usda 1.0\ndef Xform "Asset" {\n    def Mesh "ns:Body" {\n    }\n}\n'
        fixture_path = FIXTURE_DIR / "dcc/maya/valid_maya.usda"
        stage = _parse_stage_from_text(fixture_path, usda)
        config = load_config(fixture_path, target_dcc="maya")
        context = LintContext(
            file_path=fixture_path,
            parsed_stage=stage,
            config=config,
            target_dcc="maya",
        )
        results = LintEngine(create_default_registry()).run(context)
        rule_ids = {m.rule_id for r in results for m in r.messages}
        self.assertIn("maya001_namespace_clean", rule_ids)

    def test_shape_node_suffix_is_reported(self) -> None:
        messages = _run_dcc("dcc/maya/invalid_maya.usda", "maya")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("maya002_shape_node_naming", rule_ids)

    def test_auto_numbered_xform_is_reported(self) -> None:
        messages = _run_dcc("dcc/maya/invalid_maya.usda", "maya")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("maya004_transform_as_xform", rule_ids)

    def test_maya_rules_do_not_fire_for_other_dcc(self) -> None:
        messages = _run_dcc("dcc/maya/invalid_maya.usda", "houdini")
        rule_ids = {m.rule_id for m in messages}
        self.assertNotIn("maya002_shape_node_naming", rule_ids)


class HoudiniRuleTests(unittest.TestCase):
    def test_valid_houdini_file_has_no_houdini_findings(self) -> None:
        messages = _run_dcc("dcc/houdini/valid_houdini.usda", "houdini")
        h_ids = {m.rule_id for m in messages if m.rule_id.startswith("houdini")}
        self.assertEqual(h_ids, set())

    def test_houdini_default_prim_name_is_reported(self) -> None:
        messages = _run_dcc("dcc/houdini/invalid_houdini.usda", "houdini")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("houdini002_primitive_path", rule_ids)

    def test_lopnet_prim_is_reported(self) -> None:
        messages = _run_dcc("dcc/houdini/invalid_houdini.usda", "houdini")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("houdini001_lopnet_prims", rule_ids)


class BlenderRuleTests(unittest.TestCase):
    def test_valid_blender_file_has_no_blender_findings(self) -> None:
        messages = _run_dcc("dcc/blender/valid_blender.usda", "blender")
        b_ids = {m.rule_id for m in messages if m.rule_id.startswith("blender")}
        self.assertEqual(b_ids, set())

    def test_blender_default_material_name_is_reported(self) -> None:
        messages = _run_dcc("dcc/blender/invalid_blender.usda", "blender")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("blender002_material_naming", rule_ids)

    def test_skeleton_without_skel_root_is_reported(self) -> None:
        messages = _run_dcc("dcc/blender/invalid_blender.usda", "blender")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("blender003_armature_skeleton", rule_ids)
