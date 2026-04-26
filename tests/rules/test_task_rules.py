from pathlib import Path
import unittest

from usd_linter import load_config
from usd_linter.core.context import LintContext
from usd_linter.core.engine import LintEngine
from usd_linter.parser import parse_stage
from usd_linter.rules import create_default_registry
from usd_linter.semantic import inspect_stage


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _run_task(fixture_rel: str, task_type: str) -> list:
    fixture_path = FIXTURE_DIR / fixture_rel
    stage = parse_stage(fixture_path)
    semantic_stage = inspect_stage(fixture_path)
    config = load_config(fixture_path, task_type=task_type)
    context = LintContext(
        file_path=fixture_path,
        parsed_stage=stage,
        semantic_stage=semantic_stage,
        config=config,
        task_type=task_type,
    )
    registry = create_default_registry()
    results = LintEngine(registry).run(context)
    return [msg for result in results for msg in result.messages]


class RigRuleTests(unittest.TestCase):
    def test_valid_rig_has_no_task_findings(self) -> None:
        messages = _run_task("task/rig/valid_rig.usda", "rig")
        rig_ids = {m.rule_id for m in messages if m.rule_id.startswith("rig")}
        self.assertEqual(rig_ids, set())

    def test_missing_skeleton_is_reported(self) -> None:
        messages = _run_task("task/rig/invalid_rig.usda", "rig")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("rig001_has_skeleton", rule_ids)

    def test_missing_skel_root_is_reported(self) -> None:
        messages = _run_task("task/rig/invalid_rig.usda", "rig")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("rig002_has_skel_root", rule_ids)

    def test_mesh_at_root_in_rig_is_reported(self) -> None:
        messages = _run_task("task/rig/invalid_rig.usda", "rig")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("rig004_no_mesh_at_root", rule_ids)

    def test_rig_rules_do_not_fire_without_task(self) -> None:
        messages = _run_task("task/rig/invalid_rig.usda", "model")
        rule_ids = {m.rule_id for m in messages}
        self.assertNotIn("rig001_has_skeleton", rule_ids)

    def test_invalid_joint_names_are_reported(self) -> None:
        messages = _run_task("task/rig/invalid_joint_names.usda", "rig")
        joint_msgs = [m for m in messages if m.rule_id == "rig003_joint_naming"]
        bad_names = {m.message.split("'")[1] for m in joint_msgs}
        self.assertIn("01_bad", bad_names)
        self.assertIn("bad-joint", bad_names)

    def test_valid_joint_names_pass(self) -> None:
        messages = _run_task("task/rig/valid_rig.usda", "rig")
        joint_msgs = [m for m in messages if m.rule_id == "rig003_joint_naming"]
        self.assertEqual(joint_msgs, [])

    def test_duplicate_joint_names_are_reported(self) -> None:
        messages = _run_task("task/rig/duplicate_joints.usda", "rig")
        dup_msgs = [m for m in messages if m.rule_id == "rig005_duplicate_joint_names"]
        self.assertEqual(len(dup_msgs), 1)
        self.assertIn("knee", dup_msgs[0].message)

    def test_unique_joint_names_do_not_trigger_duplicate_rule(self) -> None:
        messages = _run_task("task/rig/valid_rig.usda", "rig")
        dup_msgs = [m for m in messages if m.rule_id == "rig005_duplicate_joint_names"]
        self.assertEqual(dup_msgs, [])



class ModelRuleTests(unittest.TestCase):
    def test_valid_model_has_no_model_task_findings(self) -> None:
        messages = _run_task("task/model/valid_model.usda", "model")
        model_ids = {m.rule_id for m in messages if m.rule_id.startswith("model")}
        self.assertEqual(model_ids, set())

    def test_missing_geometry_is_reported(self) -> None:
        messages = _run_task("task/model/invalid_model.usda", "model")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("model001_has_geometry", rule_ids)

    def test_light_in_model_is_reported(self) -> None:
        messages = _run_task("task/model/invalid_model.usda", "model")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("model003_no_lights", rule_ids)

    def test_camera_in_model_is_reported(self) -> None:
        messages = _run_task("task/model/invalid_model.usda", "model")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("model005_no_cameras", rule_ids)

    def test_invalid_lod_naming_is_reported(self) -> None:
        messages = _run_task("task/model/invalid_lod_naming.usda", "model")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("model002_lod_naming", rule_ids)

    def test_valid_lod_name_does_not_trigger_lod_rule(self) -> None:
        messages = _run_task("task/model/invalid_lod_naming.usda", "model")
        passing = [m for m in messages if m.rule_id == "model002_lod_naming"]
        flagged_names = {m.message.split("'")[1] for m in passing}
        self.assertNotIn("LOD0", flagged_names)


class AnimRuleTests(unittest.TestCase):
    def test_valid_anim_has_no_anim_task_findings(self) -> None:
        messages = _run_task("task/anim/valid_anim.usda", "anim")
        anim_ids = {m.rule_id for m in messages if m.rule_id.startswith("anim")}
        self.assertEqual(anim_ids, set())

    def test_missing_skel_animation_is_reported(self) -> None:
        messages = _run_task("task/anim/invalid_anim.usda", "anim")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("anim001_has_skel_animation", rule_ids)

    def test_missing_skel_root_in_anim_is_reported(self) -> None:
        messages = _run_task("task/anim/invalid_anim.usda", "anim")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("anim002_has_skel_root", rule_ids)

    def test_geometry_in_anim_is_reported(self) -> None:
        messages = _run_task("task/anim/invalid_anim.usda", "anim")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("anim003_no_geometry", rule_ids)


class LayoutRuleTests(unittest.TestCase):
    def test_invalid_layout_root_type_is_reported(self) -> None:
        messages = _run_task("task/layout/invalid_layout.usda", "layout")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("layout001_has_xform_root", rule_ids)

    def test_missing_references_in_layout_is_reported(self) -> None:
        messages = _run_task("task/layout/invalid_layout.usda", "layout")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("layout003_has_references", rule_ids)

    def test_bad_camera_name_in_layout_is_reported(self) -> None:
        messages = _run_task("task/layout/invalid_layout.usda", "layout")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("layout004_camera_naming", rule_ids)


class LookdevRuleTests(unittest.TestCase):
    def test_valid_lookdev_has_no_lookdev_task_findings(self) -> None:
        messages = _run_task("task/lookdev/valid_lookdev.usda", "lookdev")
        lookdev_ids = {m.rule_id for m in messages if m.rule_id.startswith("lookdev")}
        self.assertEqual(lookdev_ids, set())

    def test_missing_material_is_reported(self) -> None:
        messages = _run_task("task/lookdev/invalid_lookdev.usda", "lookdev")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("lookdev001_has_material", rule_ids)

    def test_material_outside_looks_scope_is_reported(self) -> None:
        messages = _run_task("task/lookdev/invalid_lookdev_scope.usda", "lookdev")
        rule_ids = {m.rule_id for m in messages}
        self.assertIn("lookdev002_looks_scope", rule_ids)

    def test_mesh_without_binding_is_reported(self) -> None:
        messages = _run_task("task/lookdev/mesh_without_binding.usda", "lookdev")
        binding_msgs = [
            m for m in messages if m.rule_id == "lookdev003_mesh_without_binding"
        ]
        flagged = {m.prim_path for m in binding_msgs}
        self.assertIn("/Asset/Body", flagged)
        self.assertNotIn("/Asset/BoundBody", flagged)
