from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class PrimCountRule(BaseRule):
    rule_id = "perf002_prim_count"
    title = "USD layers should stay under the configured prim-count budget"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        prim_count = len(stage.prims)
        max_prims = context.config.max_prim_count
        if prim_count <= max_prims:
            return RuleResult()

        return RuleResult(
            messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"USD layer contains {prim_count} prim(s), above the configured "
                        f"performance budget of {max_prims}."
                    ),
                    path=stage.path,
                    line=1,
                    suggestion="Reduce authored prim count, use instancing, or raise rules.max_prim_count.",
                )
            ]
        )
