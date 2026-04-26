# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `--fix` flag to auto-repair safe findings in-place. First implementation: `missing_required_metadata` writes `defaultPrim` when there is exactly one defined root prim.
- `--list-rules` flag to print every registered rule with its ID, severity, scope, and title.
- `--explain RULE_ID` flag to inspect a single rule (title, severity, scope, module, docstring).
- `BaseRule.fix(context, message)` hook for rule authors. Defaults to no-op; override to opt in.
- `LintMessage.fixed` field so JSON consumers and the text renderer can distinguish repaired findings.
- `FIXED` prefix and `N fixed` counter in the text report summary.
- Two new semantic rules that consume `SemanticStage`:
  - `singular_xform_matrix` (warning): flags xform stacks with singular world matrices.
  - `unresolved_material_target` (error): flags `material:binding` relationships pointing to prims that are not defined materials.
- Cross-platform CI matrix: `ubuntu-latest` and `windows-latest` across Python 3.10, 3.11, and 3.12.
- `mypy` strict type checking on `src/`, wired into CI.
- `pytest-cov` configured; project currently at ~92% coverage.
- `tests/smoke/check_exit_code_2.py` replaces a bash heredoc so CLI smoke tests run unchanged on Windows.
- `.usdc` binary coverage: `tests/test_runner.py` now generates `.usdc` fixtures dynamically and runs the full pipeline against them.
- Five new `test_semantic.py` cases: payload without composed arc, unresolved material target, singular xform stack, variant set without authored selection, inspect_stage path-only invocation.
- `LICENSE` file (MIT).
- Metadata in `pyproject.toml`: classifiers, keywords, project URLs, and `pytest-cov` / `mypy` in `[dev]` extras.
- `docs/examples/usage-in-ci.md` with GitHub Actions, pre-commit, and Docker snippets for asset repos.

### Changed

- `parser.open_stage()`, `parser.parse_opened_stage()`, and `semantic.inspect_stage()` now wrap `pxr` calls in a `suppress_pxr_diagnostics()` context manager so OpenUSD C++ warnings never pollute stderr.
- `runner._parse_file()` returns the live `pxr` stage alongside the parsed and semantic stages so fixes can author into the root layer.
- `LintReport.should_fail()` ignores messages marked as `fixed`, so `--fix` runs return exit code 0 when every finding was repaired.
- README fully rewritten in English and expanded with rule tables, CLI reference, `--fix` behavior, exit codes, plugin instructions, and CI usage examples.
- All user-facing documentation (`docs/PLAN.MD`, `docs/rules.md`, `docs/implementation-checklist.md`) translated to English.

### Fixed

- Seven real type errors surfaced by the new `mypy` strict configuration (`config.py`, `meta001_missing_metadata.py`).

## [0.1.0] - 2026-04-01

### Added

- Initial release with CLI, TOML configuration, rule registry, and engine.
- Core rules for naming, references, payloads, sublayers, `subLayers` cycles, absolute asset paths, metadata, suspicious `over` prims, root prim validation, max hierarchy depth.
- Transform rules: zero/negative scale, `NaN`/`Inf` values.
- Performance rules: file size, prim count, payload count, unused payloads.
- Contextual rules for `task` (rig, model, anim, layout, lookdev), `dcc` (maya, houdini, blender), and `project`.
- JSON and text output formats.
- Exit codes 0/1/2.
- Plugin system via `usd_linter.rules` Python entry points.
- Real integration coverage for `.usdc` and `.usdz` parsing through `pxr`.

### Fixed

- Windows text output no longer crashes on Unicode arrow rendering in suggestions.
- The basic TOML parser now supports integer values such as `max_hierarchy_depth`.
