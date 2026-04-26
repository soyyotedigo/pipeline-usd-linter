import re

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule

_NAN_INF_RE = re.compile(r"\b(nan|[-+]?inf)\b", re.IGNORECASE)


class NanInfValuesRule(BaseRule):
    rule_id = "nan_inf_values"
    title = "Transform attributes must not contain NaN or Inf values"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            for attr_name, raw_value in prim.attributes.items():
                if not attr_name.startswith("xformOp:"):
                    continue
                match = _NAN_INF_RE.search(raw_value)
                if match is None:
                    continue
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim '{prim.name}' has an invalid numeric value "
                            f"'{match.group(0)}' in {attr_name}: {raw_value}"
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="NaN/Inf values crash renderers. Re-export from source DCC.",
                    )
                )

        return RuleResult(messages=messages)
