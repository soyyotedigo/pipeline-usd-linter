from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class RigNoMeshAtRootRule(BaseRule):
    rule_id = "rig004_no_mesh_at_root"
    title = "Rig layer must not contain Mesh prims as direct children of the root"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "rig"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Mesh" and prim.path.count("/") == 2:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Mesh prim '{prim.name}' is a direct child of the root in a rig layer. "
                            "Geometry should not be baked directly into rig layers."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Reference geometry from the model layer instead.",
                    )
                )

        return RuleResult(messages=messages)
