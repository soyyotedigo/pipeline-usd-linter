from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from ._composition import resolve_asset_path


class BrokenSublayersRule(BaseRule):
    rule_id = "unresolved_sublayer"
    title = "Sublayers must resolve to existing files"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for sublayer in stage.sublayers:
            resolved_path = resolve_asset_path(stage.path.parent, sublayer.raw_path)
            if resolved_path is None or resolved_path.exists():
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Sublayer '{sublayer.raw_path}' could not be resolved.",
                    path=stage.path,
                    line=sublayer.line,
                    suggestion="Fix the sublayer path or publish the missing layer.",
                )
            )

        return RuleResult(messages=messages)
