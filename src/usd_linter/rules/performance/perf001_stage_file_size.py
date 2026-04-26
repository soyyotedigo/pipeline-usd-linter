from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class StageFileSizeRule(BaseRule):
    rule_id = "perf001_stage_file_size"
    title = "USD layer file size should stay under the configured budget"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        try:
            file_size = stage.path.stat().st_size
        except OSError:
            return RuleResult()

        max_size = context.config.max_stage_file_size_bytes
        if file_size <= max_size:
            return RuleResult()

        return RuleResult(
            messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"USD layer is {file_size} bytes, above the configured performance "
                        f"budget of {max_size} bytes."
                    ),
                    path=stage.path,
                    line=1,
                    suggestion="Split heavy content into payloads or raise rules.max_stage_file_size_bytes.",
                )
            ]
        )
