import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    tomllib = None


DEFAULT_INCLUDE_PATTERNS = ("*.usd", "*.usda", "*.usdc", "*.usdz")
DEFAULT_ALLOWED_ROOT_PRIMS = ("Asset", "Root", "World")
DEFAULT_REQUIRED_STAGE_METADATA = ("defaultPrim",)
DEFAULT_NAME_PATTERN = r"^[A-Z][A-Za-z0-9_]*$"
DEFAULT_MAX_STAGE_FILE_SIZE_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_PRIM_COUNT = 10_000
DEFAULT_MAX_PAYLOAD_COUNT = 100
SUPPORTED_OUTPUT_FORMATS = frozenset({"text", "json"})
SUPPORTED_FAIL_ON = frozenset({"none", "info", "warning", "error"})


class ConfigError(ValueError):
    """Raised when the linter config is invalid."""


@dataclass(slots=True)
class LinterConfig:
    target: Path
    config_path: Path | None = None
    output_format: str = "text"
    fail_on: str = "error"
    include_patterns: tuple[str, ...] = DEFAULT_INCLUDE_PATTERNS
    name_pattern: str = DEFAULT_NAME_PATTERN
    allowed_root_prims: tuple[str, ...] = DEFAULT_ALLOWED_ROOT_PRIMS
    required_stage_metadata: tuple[str, ...] = DEFAULT_REQUIRED_STAGE_METADATA
    enable_references_rule: bool = True
    enable_suspicious_over_rule: bool = True
    enable_name_rule: bool = True
    enable_root_prim_rule: bool = True
    enable_required_metadata_rule: bool = True
    task_type: str | None = None
    target_dcc: str | None = None
    project_name: str | None = None
    # New general toggles
    disabled_rules: tuple[str, ...] = ()
    enabled_rules: tuple[str, ...] | None = None
    max_hierarchy_depth: int = 8
    max_stage_file_size_bytes: int = DEFAULT_MAX_STAGE_FILE_SIZE_BYTES
    max_prim_count: int = DEFAULT_MAX_PRIM_COUNT
    max_payload_count: int = DEFAULT_MAX_PAYLOAD_COUNT
    # Task-specific sub-config (populated from [task_rig], [task_model], etc.)
    task_config: dict = field(default_factory=dict)
    # Project-specific sub-config (populated from [project_rules])
    project_config: dict = field(default_factory=dict)

    def is_rule_enabled(self, rule_id: str) -> bool:
        if self.enabled_rules is not None and rule_id not in self.enabled_rules:
            return False
        if rule_id in self.disabled_rules:
            return False
        if rule_id == "unresolved_reference":
            return self.enable_references_rule
        if rule_id == "suspicious_over_prim":
            return self.enable_suspicious_over_rule
        if rule_id == "invalid_prim_name":
            return self.enable_name_rule
        if rule_id == "invalid_root_prim":
            return self.enable_root_prim_rule
        if rule_id == "missing_required_metadata":
            return self.enable_required_metadata_rule
        return True


def load_config(
    target: Path,
    config_path: Path | None = None,
    output_format: str | None = None,
    fail_on: str | None = None,
    task_type: str | None = None,
    target_dcc: str | None = None,
    project_name: str | None = None,
    enabled_rules: str | tuple[str, ...] | None = None,
) -> LinterConfig:
    raw_config = _load_toml_config(config_path) if config_path is not None else {}
    lint_config = _read_table(raw_config, "lint")
    rules_config = _read_table(raw_config, "rules")
    task_sub_key = f"task_{task_type}" if task_type else None
    task_sub_config = _read_table(raw_config, task_sub_key) if task_sub_key else {}
    project_sub_config = _read_table(raw_config, "project_rules") if project_name else {}

    if "enabled" in rules_config or "disabled" in rules_config:
        raise ConfigError(
            "rules.enabled and rules.disabled are no longer supported. Use declarative "
            "keys like rules.name_pattern, rules.allowed_root_prims, "
            "rules.required_stage_metadata, rules.check_references, and "
            "rules.check_suspicious_over."
        )

    resolved_output_format = output_format or lint_config.get("format", "text")
    resolved_fail_on = fail_on or lint_config.get("fail_on", "error")

    _validate_choice(resolved_output_format, SUPPORTED_OUTPUT_FORMATS, "format")
    _validate_choice(resolved_fail_on, SUPPORTED_FAIL_ON, "fail_on")
    if not isinstance(resolved_output_format, str):
        raise ConfigError("lint.format must be a string.")
    if not isinstance(resolved_fail_on, str):
        raise ConfigError("lint.fail_on must be a string.")

    include_patterns = _read_string_list(
        lint_config.get("include_patterns", DEFAULT_INCLUDE_PATTERNS),
        field_name="lint.include_patterns",
    )
    has_config_file = config_path is not None

    enable_references_rule = _read_bool(
        rules_config.get("check_references", not has_config_file),
        field_name="rules.check_references",
    )
    enable_suspicious_over_rule = _read_bool(
        rules_config.get("check_suspicious_over", not has_config_file),
        field_name="rules.check_suspicious_over",
    )

    name_pattern = rules_config.get("name_pattern", DEFAULT_NAME_PATTERN)
    if not isinstance(name_pattern, str):
        raise ConfigError("rules.name_pattern must be a string.")

    try:
        re.compile(name_pattern)
    except re.error as exc:
        raise ConfigError(f"Invalid rules.name_pattern regex: {exc}") from exc

    enable_name_rule = (not has_config_file) or ("name_pattern" in rules_config)
    enable_root_prim_rule = (not has_config_file) or ("allowed_root_prims" in rules_config)
    enable_required_metadata_rule = (not has_config_file) or (
        "required_stage_metadata" in rules_config
    )

    allowed_root_prims: tuple[str, ...] = DEFAULT_ALLOWED_ROOT_PRIMS
    if enable_root_prim_rule:
        allowed_root_prims = _read_string_list(
            rules_config.get("allowed_root_prims", DEFAULT_ALLOWED_ROOT_PRIMS),
            field_name="rules.allowed_root_prims",
        )

    required_stage_metadata: tuple[str, ...] = DEFAULT_REQUIRED_STAGE_METADATA
    if enable_required_metadata_rule:
        required_stage_metadata = _read_string_list(
            rules_config.get("required_stage_metadata", DEFAULT_REQUIRED_STAGE_METADATA),
            field_name="rules.required_stage_metadata",
        )

    disabled_rules = _read_string_list(
        rules_config.get("disabled_rules", ()),
        field_name="rules.disabled_rules",
    )
    resolved_enabled_rules = _read_optional_rule_filter(enabled_rules)
    _validate_rule_ids(resolved_enabled_rules)

    max_hierarchy_depth = _read_int(
        rules_config.get("max_hierarchy_depth", 8),
        field_name="rules.max_hierarchy_depth",
    )
    max_stage_file_size_bytes = _read_non_negative_int(
        rules_config.get("max_stage_file_size_bytes", DEFAULT_MAX_STAGE_FILE_SIZE_BYTES),
        field_name="rules.max_stage_file_size_bytes",
    )
    max_prim_count = _read_non_negative_int(
        rules_config.get("max_prim_count", DEFAULT_MAX_PRIM_COUNT),
        field_name="rules.max_prim_count",
    )
    max_payload_count = _read_non_negative_int(
        rules_config.get("max_payload_count", DEFAULT_MAX_PAYLOAD_COUNT),
        field_name="rules.max_payload_count",
    )

    return LinterConfig(
        target=target.resolve(),
        config_path=config_path.resolve() if config_path is not None else None,
        output_format=resolved_output_format,
        fail_on=resolved_fail_on,
        include_patterns=include_patterns,
        name_pattern=name_pattern,
        allowed_root_prims=allowed_root_prims,
        required_stage_metadata=required_stage_metadata,
        enable_references_rule=enable_references_rule,
        enable_suspicious_over_rule=enable_suspicious_over_rule,
        enable_name_rule=enable_name_rule,
        enable_root_prim_rule=enable_root_prim_rule,
        enable_required_metadata_rule=enable_required_metadata_rule,
        task_type=task_type,
        target_dcc=target_dcc,
        project_name=project_name,
        disabled_rules=disabled_rules,
        enabled_rules=resolved_enabled_rules,
        max_hierarchy_depth=max_hierarchy_depth,
        max_stage_file_size_bytes=max_stage_file_size_bytes,
        max_prim_count=max_prim_count,
        max_payload_count=max_payload_count,
        task_config=dict(task_sub_config),
        project_config=dict(project_sub_config),
    )


def _load_toml_config(config_path: Path) -> dict[str, object]:
    try:
        data = _parse_toml(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file does not exist: {config_path}") from exc
    except ValueError as exc:
        raise ConfigError(f"Invalid TOML config in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a TOML table at the top level.")
    return data


def _read_table(raw_config: dict[str, object], key: str) -> dict[str, object]:
    table = raw_config.get(key, {})
    if not isinstance(table, dict):
        raise ConfigError(f"{key} must be a TOML table.")
    return table


def _read_string_list(value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ConfigError(f"{field_name} must be a list of strings.")

    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ConfigError(f"{field_name} must only contain non-empty strings.")
        items.append(item)
    return tuple(items)


def _read_optional_rule_filter(value: str | tuple[str, ...] | None) -> tuple[str, ...] | None:
    if value is None:
        return None

    if isinstance(value, str):
        items = tuple(part.strip() for part in value.split(",") if part.strip())
    else:
        items = _read_string_list(value, field_name="--rules")

    if not items:
        raise ConfigError("--rules must include at least one rule id.")
    return tuple(dict.fromkeys(items))


def _validate_rule_ids(rule_ids: tuple[str, ...] | None) -> None:
    if rule_ids is None:
        return

    from .rules import RulePluginError, get_supported_rule_ids

    try:
        supported = set(get_supported_rule_ids())
    except RulePluginError as exc:
        raise ConfigError(str(exc)) from exc
    unknown = sorted(set(rule_ids) - supported)
    if not unknown:
        return

    supported_text = ", ".join(sorted(supported))
    unknown_text = ", ".join(unknown)
    raise ConfigError(
        f"Unknown rule id(s): {unknown_text}. Supported rule ids: {supported_text}."
    )


def _validate_choice(value: object, choices: frozenset[str], field_name: str) -> None:
    if not isinstance(value, str) or value not in choices:
        supported = ", ".join(sorted(choices))
        raise ConfigError(f"{field_name} must be one of: {supported}.")


def _read_bool(value: object, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be a boolean.")
    return value


def _read_int(value: object, *, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{field_name} must be an integer.")
    return value


def _read_non_negative_int(value: object, *, field_name: str) -> int:
    integer = _read_int(value, field_name=field_name)
    if integer < 0:
        raise ConfigError(f"{field_name} must be greater than or equal to 0.")
    return integer


def _parse_toml(text: str) -> dict[str, object]:
    if tomllib is not None:
        result: dict[str, object] = tomllib.loads(text)
        return result
    return _parse_basic_toml(text)


def _parse_basic_toml(text: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_table: dict[str, object] = data

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", maxsplit=1)[0].strip()
        if not line:
            continue

        if line.startswith("["):
            if not line.endswith("]"):
                raise ValueError(f"Invalid table header on line {line_number}")
            table_name = line[1:-1].strip()
            if not table_name:
                raise ValueError(f"Empty table header on line {line_number}")
            table = data.setdefault(table_name, {})
            if not isinstance(table, dict):
                raise ValueError(f"Table {table_name!r} is defined more than once")
            current_table = table
            continue

        if "=" not in line:
            raise ValueError(f"Invalid assignment on line {line_number}")

        key, raw_value = line.split("=", maxsplit=1)
        key = key.strip()
        if not key:
            raise ValueError(f"Missing key on line {line_number}")
        current_table[key] = _parse_basic_toml_value(raw_value.strip(), line_number)

    return data


def _parse_basic_toml_value(raw_value: str, line_number: int) -> object:
    if raw_value.startswith("["):
        if not raw_value.endswith("]"):
            raise ValueError(f"Invalid list value on line {line_number}")
        inner = raw_value[1:-1].strip()
        if not inner:
            return []
        return [
            _parse_basic_toml_string(part.strip(), line_number)
            for part in inner.split(",")
            if part.strip()
        ]

    if raw_value in {"true", "false"}:
        return raw_value == "true"

    if re.fullmatch(r"[-+]?\d+", raw_value):
        return int(raw_value)

    return _parse_basic_toml_string(raw_value, line_number)


def _parse_basic_toml_string(raw_value: str, line_number: int) -> str:
    if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in {'"', "'"}:
        return raw_value[1:-1]
    if any(character.isspace() for character in raw_value):
        raise ValueError(f"Unsupported bare value on line {line_number}")
    return raw_value
