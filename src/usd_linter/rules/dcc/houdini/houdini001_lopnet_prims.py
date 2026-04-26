from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class HoudiniLopnetPrimsRule(BaseRule):
    rule_id = "houdini001_lopnet_prims"
    title = "USD layer must not contain Houdini LOP network residue prims"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "houdini"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if "/lopnet" in prim.path.lower() or prim.name.startswith("lop_"):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Prim '{prim.name}' appears to be a Houdini LOP network artifact "
                            "(path contains 'lopnet' or name starts with 'lop_')."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            "Review the Houdini LOP export settings to avoid including "
                            "internal network topology in the exported USD."
                        ),
                    )
                )

        return RuleResult(messages=messages)
