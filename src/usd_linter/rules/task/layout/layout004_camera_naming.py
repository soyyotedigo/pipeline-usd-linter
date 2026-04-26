import re

from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule

_DEFAULT_CAMERA_PATTERN = r"^cam_[a-zA-Z0-9_]+$"


class LayoutCameraNamingRule(BaseRule):
    rule_id = "layout004_camera_naming"
    title = "Camera prim names must match the camera naming pattern"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.task_type == "layout"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        pattern_str = _DEFAULT_CAMERA_PATTERN
        if context.config is not None:
            pattern_str = context.config.task_config.get("camera_name_pattern", _DEFAULT_CAMERA_PATTERN)
        pattern = re.compile(pattern_str)

        messages: list[LintMessage] = []
        for prim in stage.prims:
            if prim.type_name == "Camera" and not pattern.fullmatch(prim.name):
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Camera prim name '{prim.name}' does not match the camera naming pattern."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion="Rename to match task_layout.camera_name_pattern (default: cam_<name>).",
                    )
                )

        return RuleResult(messages=messages)
