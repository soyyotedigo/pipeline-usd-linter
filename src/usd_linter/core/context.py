from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import LinterConfig
    from ..parser import ParsedStage
    from ..semantic import SemanticStage


@dataclass(slots=True)
class LintContext:
    """Per-file runtime context passed to every rule."""

    file_path: Path
    parsed_stage: ParsedStage | None = None
    semantic_stage: SemanticStage | None = None
    config: LinterConfig | None = None
    task_type: str | None = None
    target_dcc: str | None = None
    project_name: str | None = None
    pxr_stage: object | None = None
