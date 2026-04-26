from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class PayloadCountRule(BaseRule):
    rule_id = "perf003_payload_count"
    title = "USD layers should stay under the configured payload-count budget"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        payload_count = len(stage.asset_payloads)
        max_payloads = context.config.max_payload_count
        if payload_count <= max_payloads:
            return RuleResult()

        return RuleResult(
            messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"USD layer authors {payload_count} payload(s), above the configured "
                        f"performance budget of {max_payloads}."
                    ),
                    path=stage.path,
                    line=1,
                    suggestion=(
                        "Review payload granularity or raise rules.max_payload_count."
                    ),
                )
            ]
        )
