from collections import Counter

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule
from ..._helpers import extract_joint_names


class RigDuplicateJointNamesRule(BaseRule):
    rule_id = "rig005_duplicate_joint_names"
    title = "Joint names within a Skeleton must be unique"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "rig"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for skel in stage.prims:
            if skel.type_name != "Skeleton":
                continue
            raw_joints = skel.attributes.get("joints", "")
            if not raw_joints:
                continue
            names = extract_joint_names(raw_joints)
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            if not duplicates:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Skeleton '{skel.name}' has duplicate joint names: "
                        f"{', '.join(duplicates)}."
                    ),
                    path=stage.path,
                    line=skel.line,
                    prim_path=skel.path,
                    suggestion="Rename duplicate joints so every terminal name is unique in the skeleton.",
                )
            )

        return RuleResult(messages=messages)
