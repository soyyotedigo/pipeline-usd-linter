import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_LOD_DETECT_RE = re.compile(r"(?i)lod")
_LOD_VALID_RE = re.compile(r"^LOD\d+$")


class ModelLodNamingRule(BaseRule):
    rule_id = "model002_lod_naming"
    title = "LOD prim names must follow the LOD0, LOD1, ... convention"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "model"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        lod_prims = [p for p in stage.prims if _LOD_DETECT_RE.search(p.name)]
        if not lod_prims:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in lod_prims:
            if not _LOD_VALID_RE.fullmatch(prim.name):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"LOD prim name '{prim.name}' does not follow the "
                            "LOD0, LOD1, ... naming convention."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename to LOD0, LOD1, LOD2, etc.",
                    )
                )

        return RuleResult(messages=messages)
