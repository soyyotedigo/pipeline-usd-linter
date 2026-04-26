from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class LayoutHasReferencesRule(BaseRule):
    rule_id = "layout003_has_references"
    title = "Layout layer should contain at least one asset reference"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "layout"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        if stage.asset_references:
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message="Layout USD layer contains no asset references.",
                path=stage.path,
                line=1,
                suggestion="A layout layer should reference at least one asset.",
            )
        ])
