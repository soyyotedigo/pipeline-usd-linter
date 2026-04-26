import re

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule

_ABSOLUTE_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\|file://)")


class AbsoluteAssetPathRule(BaseRule):
    rule_id = "absolute_asset_path"
    title = "Asset paths must be relative, not absolute"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        messages: list[LintMessage] = []
        sources = (
            ("reference", stage.asset_references),
            ("payload", stage.asset_payloads),
            ("sublayer", stage.sublayers),
        )
        for arc_kind, asset_refs in sources:
            for asset in asset_refs:
                if _ABSOLUTE_PATH_RE.match(asset.raw_path) is None:
                    continue
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Absolute {arc_kind} path '{asset.raw_path}' is not portable "
                            "across machines."
                        ),
                        path=stage.path,
                        line=asset.line,
                        suggestion=(
                            "Rewrite the path relative to this layer "
                            "(e.g., './assets/foo.usda')."
                        ),
                    )
                )

        return RuleResult(messages=messages)
