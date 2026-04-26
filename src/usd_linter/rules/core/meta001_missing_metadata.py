from typing import Any

from ...core.context import LintContext
from ...core.models import LintMessage, RuleResult
from ...core.registry import BaseRule


class MissingMetadataRule(BaseRule):
    rule_id = "missing_required_metadata"
    title = "Stage must contain required metadata fields"
    severity = "error"

    def applies(self, context: LintContext) -> bool:
        return True

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        required: tuple[str, ...] = ("defaultPrim",)
        if context.config is not None:
            required = context.config.required_stage_metadata

        messages: list[LintMessage] = []
        for metadata_key in required:
            if metadata_key in stage.stage_metadata:
                continue
            messages.append(
                LintMessage(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Stage metadata '{metadata_key}' is required but missing.",
                    path=stage.path,
                    line=1,
                    suggestion="Add the required stage metadata to the layer header.",
                )
            )

        return RuleResult(messages=messages)

    def fix(self, context: LintContext, message: LintMessage) -> bool:
        if "'defaultPrim'" not in message.message:
            return False

        pxr_stage: Any = context.pxr_stage
        semantic_stage = context.semantic_stage
        if pxr_stage is None or semantic_stage is None:
            return False

        root_prims = [
            prim for prim in semantic_stage.prims
            if prim.path.count("/") == 1 and prim.defined and not prim.abstract
        ]
        if len(root_prims) != 1:
            return False

        candidate = root_prims[0]
        try:
            from pxr import Sdf
        except ImportError:
            return False

        try:
            target_prim = pxr_stage.GetPrimAtPath(candidate.path)
            if not target_prim or not target_prim.IsValid():
                return False
            pxr_stage.SetDefaultPrim(target_prim)
            root_layer = pxr_stage.GetRootLayer()
            if root_layer is None:
                return False
            if not Sdf.Path.IsValidIdentifier(candidate.name):
                return False
            root_layer.Save()
        except Exception:
            return False

        return True
