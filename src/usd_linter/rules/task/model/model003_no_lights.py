from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_LIGHT_TYPES = frozenset({
    "DomeLight", "DistantLight", "SphereLight", "RectLight",
    "DiskLight", "CylinderLight", "PortalLight", "GeometryLight",
})


class ModelNoLightsRule(BaseRule):
    rule_id = "model003_no_lights"
    title = "Model layer must not contain light prims"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "model"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name in _LIGHT_TYPES:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Light prim '{prim.name}' ({prim.type_name}) found in a model layer. "
                            "Lights belong in lighting or lookdev layers."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Move lights to a dedicated lighting layer.",
                    )
                )

        return RuleResult(messages=messages)
