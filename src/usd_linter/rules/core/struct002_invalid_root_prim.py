from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from ...parser import ParsedPrim


class InvalidRootPrimRule(BaseRule):
    rule_id = "invalid_root_prim"
    title = "defaultPrim must reference an existing root prim"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        root_prims = [prim for prim in stage.prims if _is_root_prim(prim)]

        if not root_prims:
            return RuleResult(
                messages=[
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message="No root prims were found in the layer.",
                        path=stage.path,
                        line=1,
                        suggestion="Define a top-level prim such as Asset or Root.",
                    )
                ]
            )

        allowed_root_prims: tuple[str, ...] = ()
        if context.config is not None:
            allowed_root_prims = context.config.allowed_root_prims

        invalid_root_names = [prim for prim in root_prims if prim.name not in allowed_root_prims]
        if invalid_root_names:
            allowed_names = ", ".join(allowed_root_prims)
            return RuleResult(
                messages=[
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Root prim '{prim.name}' is not in the allowed set: {allowed_names}."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename the root prim or update rules.allowed_root_prims.",
                    )
                    for prim in invalid_root_names
                ]
            )

        default_prim = stage.stage_metadata.get("defaultPrim")
        if default_prim is not None and all(prim.name != default_prim for prim in root_prims):
            return RuleResult(
                messages=[
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"defaultPrim '{default_prim}' does not match any root prim in the layer.",
                        path=stage.path,
                        line=1,
                        suggestion="Align defaultPrim with an existing root prim.",
                    )
                ]
            )

        return RuleResult()


def _is_root_prim(prim: ParsedPrim) -> bool:
    return prim.path.count("/") == 1
