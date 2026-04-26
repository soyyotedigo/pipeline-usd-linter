from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule
from .._helpers import root_prims


class ProjectAssetNamePrefixRule(BaseRule):
    rule_id = "proj001_asset_name_prefix"
    title = "Root prim name must start with the project-configured asset prefix"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        if context.project_name is None:
            return False
        if context.config is None:
            return False
        return bool(context.config.project_config.get("asset_prefix", ""))

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        prefix: str = context.config.project_config.get("asset_prefix", "")
        if not prefix:
            return RuleResult()

        messages: list[LintMessage] = []
        for prim in root_prims(stage.prims):
            if not prim.name.startswith(prefix):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Root prim '{prim.name}' does not start with the required "
                            f"project prefix '{prefix}'."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=f"Rename root prim to start with '{prefix}'.",
                    )
                )

        return RuleResult(messages=messages)
