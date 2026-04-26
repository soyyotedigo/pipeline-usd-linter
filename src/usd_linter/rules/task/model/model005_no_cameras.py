from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class ModelNoCamerasRule(BaseRule):
    rule_id = "model005_no_cameras"
    title = "Model layer must not contain Camera prims"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "model"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Camera":
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Camera prim '{prim.name}' found in a model layer. "
                            "Cameras belong in layout or shot layers."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Move cameras to a layout or shot layer.",
                    )
                )

        return RuleResult(messages=messages)
