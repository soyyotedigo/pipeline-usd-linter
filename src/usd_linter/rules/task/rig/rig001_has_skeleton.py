from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class RigHasSkeletonRule(BaseRule):
    rule_id = "rig001_has_skeleton"
    title = "Rig must contain a Skeleton prim"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "rig"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        if any(p.type_name == "Skeleton" for p in stage.prims):
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message="Rig USD layer contains no Skeleton prim.",
                path=stage.path,
                line=1,
                suggestion="Add a Skeleton prim under the SkelRoot.",
            )
        ])
