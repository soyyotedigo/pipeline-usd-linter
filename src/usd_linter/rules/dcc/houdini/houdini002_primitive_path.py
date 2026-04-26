import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

# Matches Houdini default primitive names like geo1, sphere2, box3
_HOUDINI_DEFAULT_RE = re.compile(r"^[a-z]+\d+$")


class HoudiniPrimitivePathRule(BaseRule):
    rule_id = "houdini002_primitive_path"
    title = "Prim names must not look like Houdini default primitive names"
    severity = "info"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "houdini"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if _HOUDINI_DEFAULT_RE.fullmatch(prim.name):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim name '{prim.name}' looks like a Houdini default primitive name "
                            "(all-lowercase + digits). These should be renamed before publishing."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename the prim to a descriptive name in the LOP network.",
                    )
                )

        return RuleResult(messages=messages)
