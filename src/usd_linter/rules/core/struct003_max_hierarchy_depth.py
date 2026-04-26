from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from .._helpers import depth_of


class MaxHierarchyDepthRule(BaseRule):
    rule_id = "max_hierarchy_depth"
    title = "Prim hierarchy must not exceed the configured maximum depth"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        max_depth = 8
        if context.config is not None:
            max_depth = context.config.max_hierarchy_depth

        messages: list[LintMessage] = []
        for prim in stage.prims:
            prim_depth = depth_of(prim.path)
            if prim_depth <= max_depth:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Prim '{prim.name}' exceeds the maximum hierarchy depth of "
                        f"{max_depth} (found depth {prim_depth})."
                    ),
                    path=stage.path,
                    line=prim.line,
                    prim_path=prim.path,
                    suggestion="Flatten the hierarchy or raise rules.max_hierarchy_depth.",
                )
            )

        return RuleResult(messages=messages)
