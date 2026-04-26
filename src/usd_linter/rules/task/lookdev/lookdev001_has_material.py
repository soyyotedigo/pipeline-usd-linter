from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class LookdevHasMaterialRule(BaseRule):
    rule_id = "lookdev001_has_material"
    title = "Lookdev layer must contain at least one Material prim"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "lookdev"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        if any(p.type_name == "Material" for p in stage.prims):
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message="Lookdev USD layer contains no Material prims.",
                path=stage.path,
                line=1,
                suggestion="Add at least one Material prim to the lookdev layer.",
            )
        ])
