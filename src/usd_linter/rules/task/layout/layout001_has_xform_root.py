from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule
from ..._helpers import root_prims


class LayoutHasXformRootRule(BaseRule):
    rule_id = "layout001_has_xform_root"
    title = "Layout layer root prim must be an Xform"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "layout"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        roots = root_prims(stage.prims)
        if not roots:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in roots:
            if prim.type_name != "Xform":
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Root prim '{prim.name}' has type '{prim.type_name}' in a layout layer. "
                            "Layout root prims must be Xform."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Change the root prim type to Xform.",
                    )
                )

        return RuleResult(messages=messages)
