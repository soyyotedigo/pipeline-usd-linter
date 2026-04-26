from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_GEO_TYPES = frozenset({"Mesh", "BasisCurves", "Points", "NurbsPatch"})


class ModelHasGeometryRule(BaseRule):
    rule_id = "model001_has_geometry"
    title = "Model layer must contain at least one geometry prim"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "model"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        if any(p.type_name in _GEO_TYPES for p in stage.prims):
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message="Model USD layer contains no geometry prims (Mesh, BasisCurves, etc.).",
                path=stage.path,
                line=1,
                suggestion="Ensure the model layer includes geometry before publishing.",
            )
        ])
