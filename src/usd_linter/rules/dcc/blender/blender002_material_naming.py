import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

# Matches Blender default material names: "Material", "Material.001", "Material.002", etc.
_BLENDER_MATERIAL_RE = re.compile(r"^Material(\.\d{3})?$")


class BlenderMaterialNamingRule(BaseRule):
    rule_id = "blender002_material_naming"
    title = "Material prims must not use Blender default material names"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "blender"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Material" and _BLENDER_MATERIAL_RE.fullmatch(prim.name):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Material prim '{prim.name}' uses a Blender default material name. "
                            "These generic names should be replaced before publishing."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename the material to a descriptive name in Blender before exporting.",
                    )
                )

        return RuleResult(messages=messages)
