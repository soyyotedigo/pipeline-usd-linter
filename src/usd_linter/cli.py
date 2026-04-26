import argparse
from importlib.metadata import PackageNotFoundError, version
import json
import sys
from pathlib import Path
from typing import Sequence

from .config import ConfigError, SUPPORTED_FAIL_ON, SUPPORTED_OUTPUT_FORMATS, load_config
from .core.models import LintMessage, LintReport
from .core.registry import BaseRule
from .runner import run_linter
from .runner import LinterExecutionError
from .rules import RulePluginError, create_default_registry

_ANSI = {
    "error":      "\033[31m",   # red
    "warning":    "\033[33m",   # yellow
    "info":       "\033[36m",   # cyan
    "ok":         "\033[32m",   # green
    "fixed":      "\033[32m",   # green
    "rule_id":    "\033[34m",   # blue
    "location":   "\033[2m",    # dim
    "suggestion": "\033[90m",   # dark gray
    "reset":      "\033[0m",
}


def _c(text: str, key: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{_ANSI.get(key, '')}{text}{_ANSI['reset']}"


def _resolve_color(force_color: bool, no_color: bool) -> bool:
    if no_color:
        return False
    if force_color:
        return True
    return sys.stdout.isatty()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usd-linter",
        description="Run USD pipeline lint checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  usd-linter asset.usda\n"
            "  usd-linter assets/ --task rig --dcc maya\n"
            "  usd-linter asset.usda --format json --fail-on warning"
        ),
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=None,
        help="File or directory to lint. Optional when using --list-rules or --explain.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML config file with studio lint settings.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=sorted(SUPPORTED_OUTPUT_FORMATS),
        default=None,
        help="Report format.",
    )
    parser.add_argument(
        "--fail-on",
        choices=sorted(SUPPORTED_FAIL_ON),
        default=None,
        help="Lowest severity that should produce a failing exit code.",
    )
    parser.add_argument(
        "--task",
        dest="task_type",
        default=None,
        help="Task type context (e.g. rig, model, anim).",
    )
    parser.add_argument(
        "--dcc",
        dest="target_dcc",
        default=None,
        help="Target DCC context (e.g. maya, blender).",
    )
    parser.add_argument(
        "--project",
        dest="project_name",
        default=None,
        help="Project name context for project-specific rules.",
    )
    parser.add_argument(
        "--rules",
        dest="enabled_rules",
        default=None,
        help=(
            "Comma-separated rule IDs to run. Other rules are skipped "
            "after normal context/config filtering."
        ),
    )
    parser.add_argument(
        "--fix",
        dest="apply_fixes",
        action="store_true",
        default=False,
        help="Attempt to auto-fix findings in-place. Only rules that implement fix() act.",
    )
    parser.add_argument(
        "--list-rules",
        dest="list_rules",
        action="store_true",
        default=False,
        help="List every registered rule (id, severity, applicability) and exit.",
    )
    parser.add_argument(
        "--explain",
        dest="explain_rule",
        default=None,
        metavar="RULE_ID",
        help="Print the title, severity, and applicability of RULE_ID and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument(
        "--color",
        dest="force_color",
        action="store_true",
        default=False,
        help="Force colored output even when stdout is not a TTY.",
    )
    color_group.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        default=False,
        help="Disable colored output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    use_color = _resolve_color(args.force_color, args.no_color)

    if args.list_rules:
        return _handle_list_rules(use_color)

    if args.explain_rule is not None:
        return _handle_explain_rule(args.explain_rule, use_color)

    if args.target is None:
        print("ERROR: target is required (or use --list-rules / --explain)")
        return 2

    try:
        config = load_config(
            target=args.target,
            config_path=args.config,
            output_format=args.output_format,
            fail_on=args.fail_on,
            task_type=args.task_type,
            target_dcc=args.target_dcc,
            project_name=args.project_name,
            enabled_rules=args.enabled_rules,
        )
        report = run_linter(config, apply_fixes=args.apply_fixes)
    except (ConfigError, LinterExecutionError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if config.output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _render_text_report(report, use_color)

    return 1 if report.should_fail(config.fail_on) else 0


def _handle_list_rules(use_color: bool) -> int:
    try:
        registry = create_default_registry()
    except RulePluginError as exc:
        print(f"ERROR: {exc}")
        return 2

    rules = sorted(registry.rules, key=lambda r: r.rule_id)
    print(f"Registered rules ({len(rules)}):\n")
    for rule in rules:
        rule_id = _c(rule.rule_id, "rule_id", use_color)
        severity = _c(rule.severity.upper(), rule.severity, use_color)
        scope = _c(_describe_scope(rule), "location", use_color)
        print(f"  {severity:18} {rule_id:42} [{scope}] {rule.title}")
    return 0


def _handle_explain_rule(rule_id: str, use_color: bool) -> int:
    try:
        registry = create_default_registry()
    except RulePluginError as exc:
        print(f"ERROR: {exc}")
        return 2

    rule = next((r for r in registry.rules if r.rule_id == rule_id), None)
    if rule is None:
        print(f"ERROR: Unknown rule id '{rule_id}'. Run 'usd-linter --list-rules' to see all.")
        return 2

    print(_c(rule.rule_id, "rule_id", use_color))
    print(f"  Title:      {rule.title}")
    print(f"  Severity:   {_c(rule.severity.upper(), rule.severity, use_color)}")
    print(f"  Scope:      {_describe_scope(rule)}")
    module = type(rule).__module__
    print(f"  Module:     {module}")
    docstring = (type(rule).__doc__ or "").strip()
    if docstring:
        print("  Doc:")
        for line in docstring.splitlines():
            print(f"    {line}")
    return 0


def _describe_scope(rule: BaseRule) -> str:
    module = type(rule).__module__
    if ".rules.task." in module:
        category = module.split(".rules.task.", 1)[1].split(".", 1)[0]
        return f"task:{category}"
    if ".rules.dcc." in module:
        category = module.split(".rules.dcc.", 1)[1].split(".", 1)[0]
        return f"dcc:{category}"
    if ".rules.project." in module:
        return "project"
    if ".rules.performance." in module:
        return "performance"
    if ".rules.core." in module:
        return "core"
    return "external"


def _render_text_report(report: LintReport, use_color: bool) -> None:
    if not report.messages:
        print(_c(f"OK: no issues found in {report.files_scanned} file(s).", "ok", use_color))
        return

    for message in report.messages:
        print(_format_message(message, use_color))
        if message.suggestion:
            print(_c(f"  -> {message.suggestion}", "suggestion", use_color))

    counts = report.counts()
    errors   = _c(f"{counts['error']} error(s)",    "error",   use_color) if counts["error"]   else f"{counts['error']} error(s)"
    warnings = _c(f"{counts['warning']} warning(s)", "warning", use_color) if counts["warning"] else f"{counts['warning']} warning(s)"
    infos    = _c(f"{counts['info']} info(s)",       "info",    use_color) if counts["info"]    else f"{counts['info']} info(s)"
    fixed_count = sum(1 for m in report.messages if m.fixed)
    summary = f"\nSummary: {report.files_scanned} file(s), {errors}, {warnings}, {infos}"
    if fixed_count:
        summary += f", {_c(f'{fixed_count} fixed', 'fixed', use_color)}"
    print(summary)


def _format_message(message: LintMessage, use_color: bool) -> str:
    location = ""
    if message.path is not None:
        location = str(message.path)
        if message.line is not None:
            location = f"{location}:{message.line}"
    if message.prim_path:
        location = f"{location} {message.prim_path}".strip()

    severity_label = "FIXED" if message.fixed else message.severity.upper()
    severity_key = "fixed" if message.fixed else message.severity
    parts = [
        _c(severity_label, severity_key, use_color),
        _c(message.rule_id, "rule_id", use_color),
    ]
    if location:
        parts.append(_c(location, "location", use_color))
    parts.append(message.message)
    return " | ".join(parts)


def _get_version() -> str:
    try:
        return version("pipeline-usd-linter")
    except PackageNotFoundError:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
