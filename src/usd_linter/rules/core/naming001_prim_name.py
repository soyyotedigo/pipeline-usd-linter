import re

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class PrimNameRule(BaseRule):
    rule_id = "invalid_prim_name"
    title = "Prim name must match the studio naming pattern"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        name_pattern = "^[A-Z][A-Za-z0-9_]*$"
        if context.config is not None:
            name_pattern = context.config.name_pattern
        pattern = re.compile(name_pattern)

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if pattern.fullmatch(prim.name):
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Prim name '{prim.name}' does not match the studio naming pattern.",
                    path=stage.path,
                    line=prim.line,
                    prim_path=prim.path,
                    suggestion="Rename the prim to match rules.name_pattern.",
                )
            )

        return RuleResult(messages=messages)
