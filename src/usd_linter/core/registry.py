from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import LintContext
    from .models import LintMessage, RuleResult


class BaseRule(ABC):
    """Base class for all lint rules."""

    rule_id: str = "BASE000"
    title: str = "Base rule"
    severity: str = "error"

    @abstractmethod
    def applies(self, context: LintContext) -> bool:
        """Return True if this rule is relevant for the given context."""

    @abstractmethod
    def check(self, context: LintContext) -> RuleResult:
        """Run the check and return a RuleResult."""

    def fix(self, context: LintContext, message: "LintMessage") -> bool:  # noqa: F821
        """Attempt to auto-fix this finding in-place on the live USD stage.

        Override in subclasses that can safely repair the layer. Default returns False.
        Implementations must mutate context.pxr_stage (or its layer) directly and return
        True only when a change was successfully applied.
        """
        del context, message
        return False


class RuleRegistry:
    """Collects rules and filters them by context applicability."""

    def __init__(self) -> None:
        self._rules: list[BaseRule] = []

    def register(self, rule: BaseRule) -> None:
        self._rules.append(rule)

    @property
    def rules(self) -> list[BaseRule]:
        return list(self._rules)

    def get_applicable_rules(self, context: LintContext) -> list[BaseRule]:
        return [rule for rule in self._rules if rule.applies(context)]
