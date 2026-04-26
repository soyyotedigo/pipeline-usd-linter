from ....core.context import LintContext
from ....core.models import LintMessage, RuleResult
from ....core.registry import BaseRule


class BlenderArmatureSkeletonRule(BaseRule):
    rule_id = "blender003_armature_skeleton"
    title = "Skeleton prims must have a SkelRoot ancestor"
    severity = "warning"

    def applies(self, context: LintContext) -> bool:
        return context.target_dcc == "blender"

    def check(self, context: LintContext) -> RuleResult:
        stage = context.parsed_stage
        if stage is None:
            return RuleResult()

        skel_root_paths = {p.path for p in stage.prims if p.type_name == "SkelRoot"}
        messages: list[LintMessage] = []

        for prim in stage.prims:
            if prim.type_name != "Skeleton":
                continue
            parts = prim.path.split("/")
            ancestor_paths = {
                "/".join(parts[:i]) for i in range(1, len(parts))
            }
            if not ancestor_paths & skel_root_paths:
                messages.append(
                    LintMessage(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Skeleton prim '{prim.name}' has no SkelRoot ancestor. "
                            "Blender armature exports sometimes omit the required SkelRoot wrapper."
                        ),
                        path=stage.path,
                        line=prim.line,
                        prim_path=prim.path,
                        suggestion=(
                            "Wrap the Skeleton in a SkelRoot prim, or update to a Blender version "
                            "that correctly exports SkelRoot."
                        ),
                    )
                )

        return RuleResult(messages=messages)
