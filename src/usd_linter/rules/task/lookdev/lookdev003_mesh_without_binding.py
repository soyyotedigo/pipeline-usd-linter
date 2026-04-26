from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class LookdevMeshWithoutBindingRule(BaseRule):
    rule_id = "lookdev003_mesh_without_binding"
    title = "Mesh prims in lookdev layers must have a material binding"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "lookdev"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        resolved_bindings = _resolved_material_bindings(context)
        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name != "Mesh":
                continue
            if resolved_bindings is not None and prim.path in resolved_bindings:
                continue
            if resolved_bindings is None and "material:binding" in prim.attributes:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Mesh prim '{prim.name}' has no material:binding relationship.",
                    path=stage.path,
                    line=prim.line,
                    prim_path=prim.path,
                    suggestion="Bind a Material to the Mesh with 'rel material:binding = <path>'.",
                )
            )

        return RuleResult(messages=messages)


def _resolved_material_bindings(context: LintContext) -> set[str] | None:
    if context.semantic_stage is None:
        return None
    return {
        binding.prim_path
        for binding in context.semantic_stage.material_bindings
        if binding.is_resolved
    }
