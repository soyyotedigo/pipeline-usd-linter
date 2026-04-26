from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from .._helpers import descendants_of


class SuspiciousOverRule(BaseRule):
    rule_id = "suspicious_over_prim"
    title = "Over prims may indicate stale composition edits"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        has_composition_arcs = bool(
            stage.asset_references or stage.asset_payloads or stage.sublayers
        )
        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.specifier != "over":
                continue
            has_authored_content = bool(
                prim.attributes or prim.prim_metadata or descendants_of(stage.prims, prim.path)
            )
            if has_composition_arcs and has_authored_content:
                continue

            reason = (
                "the layer has no references, payloads, or sublayers to justify an override"
                if not has_composition_arcs
                else "the override is empty and has no authored content"
            )
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Found a suspicious 'over' prim for '{prim.name}': {reason}."
                    ),
                    path=stage.path,
                    line=prim.line,
                    prim_path=prim.path,
                    suggestion=(
                        "Confirm the override is intentional, add authored content, or replace it "
                        "with a concrete prim spec."
                    ),
                )
            )

        return RuleResult(messages=messages)
