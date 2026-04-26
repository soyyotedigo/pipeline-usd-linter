<p align="center">
  <img src="docs/assets/OpenUSD_Dark_Horizontal.webp" alt="OpenUSD" width="420" />
</p>

<p align="center">
  CLI + Python library to validate USD files before they break the pipeline.<br/>
  <em>An ESLint for OpenUSD.</em>
</p>

<p align="center">
  <a href="https://github.com/soyyotedigo/pipeline-usd-linter-dev/actions/workflows/ci.yml">
    <img src="https://github.com/soyyotedigo/pipeline-usd-linter-dev/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue" alt="Python versions" />
  <img src="https://img.shields.io/badge/coverage-92%25-brightgreen" alt="Coverage 92%" />
  <img src="https://img.shields.io/badge/tests-117%20passing-brightgreen" alt="Tests" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT" />
</p>

`pipeline-usd-linter` runs technical checks on OpenUSD files and reports actionable findings. Designed for local use, export preflight, and CI pipelines — no Maya, Houdini, or Blender required.

## What it does

- validates `USDA`, `USDC`, and `USDZ` via `usd-core` / `pxr`
- detects broken references, payloads, sublayers, and `subLayers` cycles
- validates naming, `defaultPrim`, required metadata, and hierarchy depth
- flags singular xform stacks, `NaN`/`Inf` values, and zero/negative scales
- validates material bindings and unresolved shading targets
- runs contextual rules for `task` (rig, model, anim, layout, lookdev), `dcc` (maya, houdini, blender), and `project`
- supports performance budgets (file size, prim count, payloads)
- auto-repairs safe findings with `--fix`
- emits `text` or `json` output with useful exit codes for automation
- extensible through Python entry points (`usd_linter.rules`)

## Install

```bash
python -m pip install -e ".[dev]"
```

Verify:

```bash
usd-linter --version
usd-linter --help
```

## Quickstart

```bash
# Basic lint
usd-linter asset.usda

# Lint a directory
usd-linter assets/

# Contextual rules by task / DCC / project
usd-linter rig.usda --task rig --dcc maya --project demo

# JSON output for integrations
usd-linter asset.usda --format json --fail-on warning

# Run only one or more specific rules
usd-linter asset.usda --rules invalid_prim_name,unresolved_reference

# Auto-repair findings where safe
usd-linter asset.usda --fix
```

## Output

```
ERROR | invalid_prim_name | C:/assets/asset.usda:8 /BadRoot/badMesh | Prim name 'badMesh' does not match the studio naming pattern.
  -> Rename the prim to match rules.name_pattern.
WARNING | suspicious_over_prim | C:/assets/asset.usda:14 /BadRoot/Looks | Found a suspicious 'over' prim for 'Looks': the override is empty and has no authored content.
  -> Confirm the override is intentional, add authored content, or replace it with a concrete prim spec.

Summary: 1 file(s), 1 error(s), 1 warning(s), 0 info(s)
```

With `--fix`, repaired findings are reported as `FIXED` and do not produce a failing exit code:

```
FIXED | missing_required_metadata | asset.usda:1 | Stage metadata 'defaultPrim' is required but missing.
  -> Add the required stage metadata to the layer header.

Summary: 1 file(s), 1 error(s), 0 warning(s), 0 info(s), 1 fixed
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings (or all repaired via `--fix`) |
| `1` | Findings meet the `--fail-on` threshold |
| `2` | Usage error (missing target, unknown rule, invalid config) |

## CLI

```
usd-linter [target] [options]
```

| Flag | Description |
|------|-------------|
| `target` | File or directory to lint. Optional with `--list-rules` / `--explain`. |
| `--config PATH` | TOML file with studio configuration. |
| `--format text\|json` | Output format. |
| `--fail-on none\|info\|warning\|error` | Minimum severity that produces exit code 1. |
| `--task TYPE` | Enable task-specific rules (rig, model, anim, layout, lookdev). |
| `--dcc DCC` | Enable DCC-specific rules (maya, houdini, blender). |
| `--project NAME` | Enable project-specific rules. |
| `--rules a,b,c` | Temporary allow-list of rule IDs. |
| `--fix` | Auto-repair findings when the rule implements a safe fix. |
| `--list-rules` | List every registered rule and exit. |
| `--explain RULE_ID` | Print details for one rule and exit. |
| `--color` / `--no-color` | Force/disable colored output. |
| `--version` | Print the installed version. |

## Rules

47 built-in rules, organized by category. To list them all:

```bash
usd-linter --list-rules
usd-linter --explain singular_xform_matrix
```

### Core (always active)

| Rule ID | Severity | What it validates |
|---------|----------|-------------------|
| `invalid_prim_name` | error | Prim name against `name_pattern` |
| `invalid_root_prim` | error | `defaultPrim` references a valid root prim |
| `missing_required_metadata` | error | Stage has required metadata (`defaultPrim`, etc.) |
| `max_hierarchy_depth` | error | Hierarchy depth within the configured limit |
| `unresolved_reference` | error | References point to existing layers |
| `unresolved_payload` | error | Payloads point to existing layers |
| `unresolved_sublayer` | error | Sublayers point to existing layers |
| `sublayer_cycle` | error | No cycles in `subLayers` |
| `absolute_asset_path` | error | Asset paths are relative |
| `suspicious_over_prim` | warning | Detects empty `over` prims without composition |
| `zero_or_negative_scale` | error | No zero or negative scales |
| `nan_inf_values` | error | No `NaN` or `Inf` in xformOps |
| `singular_xform_matrix` | warning | Detects singular (det=0) xform stacks |
| `unresolved_material_target` | error | `material:binding` resolves to an existing material |

### Performance

| Rule ID | Severity | What it validates |
|---------|----------|-------------------|
| `perf001_stage_file_size` | warning | File size within budget |
| `perf002_prim_count` | warning | Prim count within budget |
| `perf003_payload_count` | warning | Payload count within budget |
| `perf004_unused_payload` | warning | Authored payloads actually compose into arcs |

### Task (`--task ...`)

- `rig`: skeleton, skel root, joint naming, mesh at root, duplicate joint names (5 rules)
- `model`: minimum geometry, LOD naming, no lights, no cameras (4 rules)
- `anim`: skel animation, skel root, no geometry (3 rules)
- `layout`: xform root, references present, camera naming (3 rules)
- `lookdev`: material present, `Looks` scope, mesh with binding (3 rules)

### DCC (`--dcc ...`)

- `maya`: namespace clean, shape node naming, transform-as-xform (3 rules)
- `houdini`: lopnet residue, primitive path (2 rules)
- `blender`: material naming, armature/skeleton (2 rules)

### Project (`--project ...`)

- `proj001_asset_name_prefix`, `proj002_allowed_prim_types`, `proj004_file_naming`, `proj005_forbidden_types`

## Configuration (TOML)

```toml
[lint]
format = "text"
fail_on = "warning"

[rules]
check_references = true
check_suspicious_over = true
allowed_root_prims = ["Asset", "Root", "World"]
required_stage_metadata = ["defaultPrim", "upAxis"]
name_pattern = "^[A-Z][A-Za-z0-9_]*$"
disabled_rules = ["suspicious_over_prim"]
max_hierarchy_depth = 8
max_stage_file_size_bytes = 52428800
max_prim_count = 10000
max_payload_count = 100

[task_rig]
# sub-config accessible from rules via context.config.task_config

[project_rules]
# sub-config accessible from rules via context.config.project_config
```

> When a `--config` file is passed, the `name_rule`, `root_prim_rule`, and `required_metadata_rule` core rules are disabled by default and only activate if you explicitly declare `name_pattern`, `allowed_root_prims`, or `required_stage_metadata`.

## Auto-fix (`--fix`)

`--fix` only applies changes when a rule declares a safe `fix()`. Today these rules have fixes:

| Rule ID | What it repairs |
|---------|-----------------|
| `missing_required_metadata` | Adds `defaultPrim` when missing and there is exactly one defined root prim |

Rules without `fix()` still report as before. The design lets critique-only rules coexist with fixable ones without breaking the flow.

## Plugins (entry points)

External studios can contribute rules without forking. In the studio package's `pyproject.toml`:

```toml
[project.entry-points."usd_linter.rules"]
my_studio_rule = "my_studio_lint.rules:MyRule"
```

Each entry point must resolve to:

- a `BaseRule` subclass,
- a `BaseRule` instance, or
- a zero-argument factory returning a `BaseRule` instance.

Duplicate rule IDs make the linter fail on startup.

## Using it in CI

See [`docs/examples/usage-in-ci.md`](docs/examples/usage-in-ci.md) for ready-to-copy GitHub Actions and GitLab CI snippets that gate asset repos on `usd-linter`.

## GitHub Actions

The repo ships with CI that runs on every push/PR across `ubuntu-latest` and `windows-latest`, with Python 3.10/3.11/3.12:

- `ruff check .`
- `mypy src/`
- `pytest`
- CLI smoke tests (`text`, `json`, contextual, exit code 2)

## Development

```bash
python -m pip install -e ".[dev]"
ruff check src/ tests/
mypy src/
pytest --cov=usd_linter
```

See [`docs/architecture.md`](docs/architecture.md) for the detailed data flow and [`docs/PLAN.MD`](docs/PLAN.MD) for the roadmap.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT. See [LICENSE](LICENSE).
