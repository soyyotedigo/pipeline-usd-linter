from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from ._composition import resolve_asset_path


class BrokenPayloadsRule(BaseRule):
    rule_id = "unresolved_payload"
    title = "Payloads must resolve to existing files"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for payload in stage.asset_payloads:
            resolved_path = resolve_asset_path(stage.path.parent, payload.raw_path)
            if resolved_path is None or resolved_path.exists():
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Payload layer '{payload.raw_path}' could not be resolved.",
                    path=stage.path,
                    line=payload.line,
                    suggestion="Fix the payload path or publish the missing layer.",
                )
            )

        return RuleResult(messages=messages)
