from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class MayaShapeNodeNamingRule(BaseRule):
    rule_id = "maya002_shape_node_naming"
    title = "Mesh prim names must not end with 'Shape' (Maya shape node suffix)"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "maya"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Mesh" and prim.name.endswith("Shape"):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Mesh prim '{prim.name}' ends with 'Shape' — a Maya shape node suffix "
                            "that should be stripped on publish."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            "Enable 'Merge Transform and Shape' in the Maya USD export options, "
                            "or rename the prim to remove the 'Shape' suffix."
                        ),
                    )
                )

        return RuleResult(messages=messages)
