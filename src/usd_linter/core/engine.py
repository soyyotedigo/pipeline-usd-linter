from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import LintContext
    from .models import RuleResult
    from .registry import RuleRegistry


class LintEngine:
    """Runs applicable rules from a registry against a context."""

    def __init__(self, registry: RuleRegistry) -> None:
        self.registry = registry

    def run(self, context: LintContext) -> list[RuleResult]:
        results: list[RuleResult] = []

        for rule in self.registry.get_applicable_rules(context):
            if context.config and not context.config.is_rule_enabled(rule.rule_id):
                continue
            result = rule.check(context)
            results.append(result)

        return results
