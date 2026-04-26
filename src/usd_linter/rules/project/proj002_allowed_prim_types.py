from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class ProjectAllowedPrimTypesRule(BaseRule):
    rule_id = "proj002_allowed_prim_types"
    title = "Only project-allowed prim types may be used"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        if context.project_name is None:
            return False
        if context.config is None:
            return False
        return bool(context.config.project_config.get("allowed_prim_types"))

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        allowed = set(context.config.project_config.get("allowed_prim_types", []))
        if not allowed:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name and prim.type_name not in allowed:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim '{prim.name}' has type '{prim.type_name}' which is not "
                            f"in the project allowlist."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            f"Allowed types: {sorted(allowed)}. "
                            "Update project_rules.allowed_prim_types or remove this prim."
                        ),
                    )
                )

        return RuleResult(messages=messages)
