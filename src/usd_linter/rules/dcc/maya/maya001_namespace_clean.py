from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class MayaNamespaceCleanRule(BaseRule):
    rule_id = "maya001_namespace_clean"
    title = "Prim names must not contain Maya namespace separators"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "maya"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if ":" in prim.name:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim name '{prim.name}' contains ':' — a Maya namespace separator "
                            "that leaked through the USD export."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            "Strip namespaces before export or use the 'Strip Namespaces' "
                            "option in the Maya USD export dialog."
                        ),
                    )
                )

        return RuleResult(messages=messages)
