from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class RigHasSkelRootRule(BaseRule):
    rule_id = "rig002_has_skel_root"
    title = "Rig must contain a SkelRoot prim"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "rig"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        if any(p.type_name == "SkelRoot" for p in stage.prims):
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message="Rig USD layer contains no SkelRoot prim.",
                path=stage.path,
                line=1,
                suggestion="Wrap the Skeleton prim inside a SkelRoot.",
            )
        ])
