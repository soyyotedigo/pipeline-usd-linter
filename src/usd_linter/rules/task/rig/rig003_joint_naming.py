import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule
from ..._helpers import extract_joint_names

_DEFAULT_JOINT_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_]*$"


class RigJointNamingRule(BaseRule):
    rule_id = "rig003_joint_naming"
    title = "Joint names must match the joint naming pattern"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "rig"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        pattern_str = _DEFAULT_JOINT_PATTERN
        if context.config is not None:
            pattern_str = context.config.task_config.get("joint_name_pattern", _DEFAULT_JOINT_PATTERN)
        pattern = re.compile(pattern_str)

        skeleton_prims = [p for p in stage.prims if p.type_name == "Skeleton"]
        messages: list[LintMessage] = []
        for skel in skeleton_prims:
            raw_joints = skel.attributes.get("joints", "")
            if not raw_joints:
                continue
            for joint_name in extract_joint_names(raw_joints):
                if not pattern.fullmatch(joint_name):
                    messages.append(
                        LintMessage(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Joint name '{joint_name}' does not match the joint naming pattern.",
                            path=stage.path,
                            line=skel.line,
                            prim_path=skel.path,
                            suggestion="Rename joint to match task_rig.joint_name_pattern.",
                        )
                    )

        return RuleResult(messages=messages)
