from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class ProjectForbiddenTypesRule(BaseRule):
    rule_id = "proj005_forbidden_types"
    title = "Forbidden prim types must not appear in project files"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        if context.project_name is None:
            return False
        if context.config is None:
            return False
        return bool(context.config.project_config.get("forbidden_prim_types"))

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        forbidden = set(context.config.project_config.get("forbidden_prim_types", []))
        if not forbidden:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name in forbidden:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim '{prim.name}' has forbidden type '{prim.type_name}' "
                            f"for this project."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            f"Remove or replace this prim. "
                            f"Forbidden types: {sorted(forbidden)}."
                        ),
                    )
                )

        return RuleResult(messages=messages)
