import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

# Matches Maya auto-generated transform names like pCube1, nurbsCircle3, locator2
_MAYA_AUTONAME_RE = re.compile(r"^[a-z][A-Za-z]+\d+$")


class MayaTransformAsXformRule(BaseRule):
    rule_id = "maya004_transform_as_xform"
    title = "Xform prims must not have Maya auto-numbered names"
    severity = "info"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "maya"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Xform" and _MAYA_AUTONAME_RE.fullmatch(prim.name):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Xform prim '{prim.name}' looks like a Maya auto-numbered transform name. "
                            "These placeholder names should be replaced before publishing."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename the prim to a descriptive name before export.",
                    )
                )

        return RuleResult(messages=messages)
