import re

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule

_TUPLE_RE = re.compile(r"\(([^)]+)\)")


class ZeroOrNegativeScaleRule(BaseRule):
    rule_id = "zero_or_negative_scale"
    title = "Transform scale components must be positive non-zero values"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            raw = prim.attributes.get("xformOp:scale")
            if not raw:
                continue
            match = _TUPLE_RE.search(raw)
            if match is None:
                continue
            try:
                components = [float(c.strip()) for c in match.group(1).split(",")]
            except ValueError:
                continue

            if any(c == 0 for c in components):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity="error",
                        message=f"Prim '{prim.name}' has a zero scale component: {raw}",
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Scale components of 0 collapse geometry. Set positive non-zero values.",
                    )
                )
            elif any(c < 0 for c in components):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity="warning",
                        message=f"Prim '{prim.name}' has a negative scale component: {raw}",
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Negative scales silently flip normals. Use positive scale + explicit orientation flip.",
                    )
                )

        return RuleResult(messages=messages)
