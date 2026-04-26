import re

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class ProjectFileNamingRule(BaseRule):
    rule_id = "proj004_file_naming"
    title = "USD filename must match the project-configured naming pattern"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        if context.project_name is None:
            return False
        if context.config is None:
            return False
        return bool(context.config.project_config.get("file_name_pattern", ""))

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None or context.config is None:
            return RuleResult()

        pattern_str: str = context.config.project_config.get("file_name_pattern", "")
        if not pattern_str:
            return RuleResult()

        filename_stem = stage.path.stem
        try:
            pattern = re.compile(pattern_str)
        except re.error:
            return RuleResult()

        if pattern.fullmatch(filename_stem):
            return RuleResult()

        return RuleResult(messages=[
            LintMessage(
                rule_id=self.rule_id,
                severity=self.severity,
                message=(
                    f"Filename '{filename_stem}' does not match the project file naming pattern."
                ),
                path=stage.path,
                line=1,
                suggestion=f"Rename the file to match: {pattern_str}",
            )
        ])
