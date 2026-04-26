from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class UnusedPayloadRule(BaseRule):
    rule_id = "perf004_unused_payload"
    title = "Authored payloads should compose into the stage"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        parsed_stage = context.parsed_stage
        semantic_stage = context.semantic_stage
        if parsed_stage is None or semantic_stage is None or not semantic_stage.authored_payloads:
            return RuleResult()

        prim_lines = {prim.path: prim.line for prim in parsed_stage.prims}
        messages: list[LintMessage] = []
        for payload in semantic_stage.authored_payloads:
            if payload.has_composed_arc:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        f"Payload '{_format_payload(payload.asset_path, payload.target_prim_path)}' "
                        f"authored on {payload.prim_path} does not compose any payload arc "
                        "into the stage."
                    ),
                    path=parsed_stage.path,
                    line=prim_lines.get(payload.prim_path, 1),
                    prim_path=payload.prim_path,
                    suggestion=(
                        "Remove the unused payload or fix its target layer/defaultPrim so it "
                        "contributes composed data."
                    ),
                )
            )

        return RuleResult(messages=messages)


def _format_payload(asset_path: str, prim_path: str) -> str:
    asset_path = asset_path or "<current layer>"
    return f"{asset_path}{prim_path}" if prim_path else asset_path
