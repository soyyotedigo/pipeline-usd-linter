from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class UnresolvedMaterialTargetRule(BaseRule):
    rule_id = "unresolved_material_target"
    title = "material:binding targets must resolve to defined materials"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return context.semantic_stage is not None

    def check(self, context: LintContext) -> RuleResult:
        semantic_stage = context.semantic_stage
        if semantic_stage is None:
            return RuleResult()

        defined_paths = {prim.path for prim in semantic_stage.prims if prim.defined}
        prim_lines = _build_prim_line_index(context)
        messages: list[LintMessage] = []
        for binding in semantic_stage.material_bindings:
            if not binding.relationship_targets:
                continue
            missing = [
                target for target in binding.relationship_targets
                if target not in defined_paths
            ]
            if not missing:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Prim '{binding.prim_path}' has material:binding targets that do not "
                        f"resolve to defined material prims: {', '.join(missing)}."
                    ),
                    path=semantic_stage.path,
                    line=prim_lines.get(binding.prim_path),
                    prim_path=binding.prim_path,
                    suggestion=(
                        "Author the missing material prim or repoint material:binding to an "
                        "existing UsdShade.Material."
                    ),
                )
            )

        return RuleResult(messages=messages)


def _build_prim_line_index(context: LintContext) -> dict[str, int]:
    parsed_stage = context.parsed_stage
    if parsed_stage is None:
        return {}
    return {prim.path: prim.line for prim in parsed_stage.prims}
