from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_LOOKS_NAMES = frozenset({"Looks", "looks"})


class LookdevLooksScopeRule(BaseRule):
    rule_id = "lookdev002_looks_scope"
    title = "Material prims should be grouped under a 'Looks' Scope"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "lookdev"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        material_prims = [p for p in stage.prims if p.type_name == "Material"]
        if not material_prims:
            return RuleResult()

        looks_paths = {
            p.path for p in stage.prims
            if p.type_name == "Scope" and p.name in _LOOKS_NAMES
        }
        if not looks_paths:
            return RuleResult(messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        "Material prims exist but no 'Looks' Scope was found. "
                        "Materials should be organized under a Scope named 'Looks'."
                    ),
                    path=stage.path,
                    line=material_prims[0].line,
                    suggestion="Group all Material prims inside a Scope named 'Looks'.",
                )
            ])

        messages: list[LintMessage] = []
        for mat in material_prims:
            under_looks = any(mat.path.startswith(lp + "/") for lp in looks_paths)
            if not under_looks:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Material prim '{mat.name}' is not under a 'Looks' Scope."
                        ),
                        path=stage.path,
                        line=mat.line,
                        prim_path=mat.path,
                        suggestion="Move the material under a Scope named 'Looks'.",
                    )
                )

        return RuleResult(messages=messages)
