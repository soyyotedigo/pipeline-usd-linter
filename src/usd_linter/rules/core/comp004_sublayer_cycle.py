from pathlib import Path

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from ._composition import read_sublayers_from_source, resolve_asset_path


class SublayerCycleRule(BaseRule):
    rule_id = "sublayer_cycle"
    title = "Sublayers must not introduce dependency cycles"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        cycle = _find_sublayer_cycle(stage.path)
        if cycle is None:
            return RuleResult()

        cycle_text = " -> ".join(path.name for path in cycle)
        return RuleResult(
            messages=[
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Sublayer cycle detected: {cycle_text}.",
                    path=stage.path,
                    line=1,
                    suggestion="Break the recursive subLayer dependency chain.",
                )
            ]
        )


def _find_sublayer_cycle(root_path: Path) -> list[Path] | None:
    visited: set[Path] = set()
    stack: list[Path] = []
    stack_set: set[Path] = set()

    def visit(layer_path: Path) -> list[Path] | None:
        if layer_path in stack_set:
            start_index = stack.index(layer_path)
            return stack[start_index:] + [layer_path]
        if layer_path in visited:
            return None

        visited.add(layer_path)
        stack.append(layer_path)
        stack_set.add(layer_path)

        for raw_path, _line in read_sublayers_from_source(layer_path):
            resolved = resolve_asset_path(layer_path.parent, raw_path)
            if resolved is None or not resolved.exists():
                continue
            cycle = visit(resolved)
            if cycle is not None:
                return cycle

        stack.pop()
        stack_set.remove(layer_path)
        return None

    return visit(root_path)
