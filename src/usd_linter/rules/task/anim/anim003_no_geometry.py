from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_GEO_TYPES = frozenset({"Mesh", "BasisCurves", "Points", "NurbsPatch"})


class AnimNoGeometryRule(BaseRule):
    rule_id = "anim003_no_geometry"
    title = "Anim layer should not contain geometry prims"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "anim"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name in _GEO_TYPES:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Geometry prim '{prim.name}' ({prim.type_name}) found in an anim layer. "
                            "Geometry belongs in the model/rig layer."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Remove geometry from the anim layer; reference the model layer instead.",
                    )
                )

        return RuleResult(messages=messages)
