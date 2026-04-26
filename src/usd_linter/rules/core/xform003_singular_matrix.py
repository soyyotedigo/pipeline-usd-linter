from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class SingularMatrixRule(BaseRule):
    rule_id = "singular_xform_matrix"
    title = "Xform local matrix must not be singular"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.semantic_stage is not None

    def check(self, context: LintContext) -> RuleResult:
        semantic_stage = context.semantic_stage
        if semantic_stage is None:
            return RuleResult()

        prim_lines = _build_prim_line_index(context)
        messages: list[LintMessage] = []
        for xform in semantic_stage.xforms:
            if xform.has_nan_or_inf:
                continue
            if not xform.is_singular:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Xform '{xform.prim_path}' has a singular world matrix "
                        f"(determinant={xform.determinant:.6g})."
                    ),
                    path=semantic_stage.path,
                    line=prim_lines.get(xform.prim_path),
                    prim_path=xform.prim_path,
                    suggestion=(
                        "Singular matrices collapse geometry. Check for zero scale components or "
                        "redundant ops in xformOpOrder."
                    ),
                )
            )

        return RuleResult(messages=messages)


def _build_prim_line_index(context: LintContext) -> dict[str, int]:
    parsed_stage = context.parsed_stage
    if parsed_stage is None:
        return {}
    return {prim.path: prim.line for prim in parsed_stage.prims}
