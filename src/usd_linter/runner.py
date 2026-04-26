from pathlib import Path

from .config import LinterConfig
from .core.context import LintContext
from .core.engine import LintEngine
from .core.models import LintMessage, LintReport
from .core.registry import RuleRegistry
from .parser import ParseError, ParsedStage, open_stage, parse_opened_stage
from .rules import RulePluginError, create_default_registry
from .semantic import SemanticStage, inspect_stage


class LinterExecutionError(RuntimeError):
    """Raised when the linter cannot inspect the requested target."""


def run_linter(
    config: LinterConfig,
    registry: RuleRegistry | None = None,
    *,
    apply_fixes: bool = False,
) -> LintReport:
    if registry is None:
        try:
            registry = create_default_registry()
        except RulePluginError as exc:
            raise LinterExecutionError(str(exc)) from exc

    engine = LintEngine(registry)
    files = _collect_target_files(config.target, config.include_patterns)
    report = LintReport(target=config.target, files_scanned=len(files))
    rule_by_id = {rule.rule_id: rule for rule in registry.rules}

    for file_path in files:
        try:
            stage, semantic_stage, pxr_stage = _parse_file(file_path)
        except ParseError as exc:
            if len(files) == 1:
                raise LinterExecutionError(f"{file_path}: {exc}") from exc
            report.messages.append(_parse_error_message(file_path, exc))
            continue

        context = LintContext(
            file_path=file_path,
            parsed_stage=stage,
            semantic_stage=semantic_stage,
            config=config,
            task_type=config.task_type,
            target_dcc=config.target_dcc,
            project_name=config.project_name,
            pxr_stage=pxr_stage if apply_fixes else None,
        )

        results = engine.run(context)
        for result in results:
            for message in result.messages:
                if apply_fixes:
                    rule = rule_by_id.get(message.rule_id)
                    if rule is not None and rule.fix(context, message):
                        message.fixed = True
                report.messages.append(message)

    report.messages.sort(key=_message_sort_key)
    return report


def _parse_file(file_path: Path) -> tuple[ParsedStage, SemanticStage, object]:
    pxr_stage = open_stage(file_path)
    return (
        parse_opened_stage(file_path, pxr_stage),
        inspect_stage(file_path, pxr_stage),
        pxr_stage,
    )


def _collect_target_files(target: Path, include_patterns: tuple[str, ...]) -> list[Path]:
    if not target.exists():
        raise LinterExecutionError(f"Target does not exist: {target}")

    if target.is_file():
        if not _matches_include_patterns(target, include_patterns):
            raise LinterExecutionError(
                f"Unsupported file type for {target}. Expected one of: {', '.join(include_patterns)}"
            )
        return [target.resolve()]

    if not target.is_dir():
        raise LinterExecutionError(f"Target is not a file or directory: {target}")

    files: set[Path] = set()
    for pattern in include_patterns:
        files.update(path.resolve() for path in target.rglob(pattern) if path.is_file())

    if not files:
        raise LinterExecutionError(
            f"No USD files found under {target} matching: {', '.join(include_patterns)}"
        )

    return sorted(files)


def _matches_include_patterns(path: Path, include_patterns: tuple[str, ...]) -> bool:
    return any(path.match(pattern) for pattern in include_patterns)


def _parse_error_message(file_path: Path, exc: ParseError) -> LintMessage:
    return LintMessage(
        rule_id="parse_error",
        severity="error",
        message=f"Could not parse USD layer: {exc}",
        path=file_path,
        line=1,
        suggestion="Fix the layer so OpenUSD can open it, then rerun the linter.",
    )


def _message_sort_key(message: LintMessage) -> tuple[str, int, str]:
    path = str(message.path) if message.path is not None else ""
    line = message.line or 0
    return (path, line, message.rule_id)
