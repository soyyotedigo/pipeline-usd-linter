# Using `usd-linter` in CI

Ready-to-copy snippets for hooking `pipeline-usd-linter` into the most common CI
and pre-commit setups. All examples assume the package is installable from your
internal index, a git ref, or the public release on PyPI.

---

## GitHub Actions: gate an asset repo

Use this as `.github/workflows/usd-lint.yml` in a repository full of `.usda` /
`.usdc` files. It fails the PR when any rule at or above `warning` severity
fires, and uploads the full report as a build artifact for triage.

```yaml
name: USD lint

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install usd-linter
        run: python -m pip install pipeline-usd-linter

      - name: Lint all assets
        run: |
          usd-linter assets/ \
            --config usd-lint.toml \
            --fail-on warning \
            --format json \
            > usd-lint-report.json

      - name: Upload lint report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: usd-lint-report
          path: usd-lint-report.json
```

The `--format json` output is stable and cheap to parse in downstream steps
(Slack notifications, GitHub annotations, dashboards).

---

## GitHub Actions: only fail on new findings

Useful when you introduce the linter into an older repo with pre-existing debt.
Lint the PR diff against the base branch instead of the whole tree:

```yaml
name: USD lint (diff)

on:
  pull_request:

jobs:
  lint-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install usd-linter
        run: python -m pip install pipeline-usd-linter

      - name: Lint changed USD files only
        run: |
          changed=$(git diff --name-only --diff-filter=ACMR \
            origin/${{ github.base_ref }}...HEAD \
            -- '*.usd' '*.usda' '*.usdc' '*.usdz')
          if [ -z "$changed" ]; then
            echo "No USD files changed."
            exit 0
          fi
          echo "$changed" | xargs -I {} usd-linter {} --fail-on warning
```

This lets teams adopt the linter without a one-shot cleanup of the whole repo.

---

## GitHub Actions: auto-fix and open a PR

Run `--fix` on a schedule and open a pull request when the linter repairs
anything. Works well for metadata that drifts as artists save new layers:

```yaml
name: USD auto-fix

on:
  schedule:
    - cron: "0 7 * * 1"  # Mondays 07:00 UTC
  workflow_dispatch:

jobs:
  autofix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: python -m pip install pipeline-usd-linter

      - name: Apply auto-fixes
        run: usd-linter assets/ --fix || true

      - name: Open PR if anything changed
        uses: peter-evans/create-pull-request@v6
        with:
          title: "chore(usd): apply automatic lint fixes"
          branch: chore/usd-autofix
          commit-message: "chore(usd): apply automatic lint fixes"
```

---

## Pre-commit hook

Run the linter on staged USD files before they land. Add this to
`.pre-commit-config.yaml` in the asset repo:

```yaml
repos:
  - repo: local
    hooks:
      - id: usd-linter
        name: usd-linter
        entry: usd-linter
        language: python
        additional_dependencies: ["pipeline-usd-linter"]
        files: \.usd[azc]?$
        args: ["--fail-on", "warning"]
```

Pre-commit passes each staged file to `entry` as a positional argument, which
matches `usd-linter`'s CLI contract directly.

---

## GitLab CI

```yaml
usd-lint:
  image: python:3.11-slim
  stage: test
  before_script:
    - pip install pipeline-usd-linter
  script:
    - usd-linter assets/ --config usd-lint.toml --fail-on warning --format json > usd-lint-report.json
  artifacts:
    when: always
    paths:
      - usd-lint-report.json
    expire_in: 1 week
```

---

## Docker one-liner

When your CI runner does not have Python but does have Docker, you can wrap the
linter in a lightweight image:

```dockerfile
# Dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir pipeline-usd-linter
WORKDIR /workspace
ENTRYPOINT ["usd-linter"]
```

Build once, then reuse everywhere:

```bash
docker build -t usd-linter:latest .
docker run --rm -v "$PWD:/workspace" usd-linter:latest assets/ --fail-on warning
```

---

## Minimal `usd-lint.toml` for an asset repo

A practical starting point that most studios can drop in with minor edits:

```toml
[lint]
format = "text"
fail_on = "warning"

[rules]
check_references = true
check_suspicious_over = true
allowed_root_prims = ["Asset", "Root"]
required_stage_metadata = ["defaultPrim", "upAxis"]
name_pattern = "^[A-Z][A-Za-z0-9_]*$"
max_hierarchy_depth = 12
max_stage_file_size_bytes = 52428800
max_prim_count = 15000
max_payload_count = 200

[task_rig]
joint_name_pattern = "^[a-zA-Z][a-zA-Z0-9_]*$"

[project_rules]
asset_prefix = "ASSET_"
allowed_prim_types = [
  "Xform",
  "Mesh",
  "Material",
  "Scope",
  "Skeleton",
  "SkelRoot",
  "Camera",
]
file_name_pattern = "^[a-z][a-z0-9_]*$"
forbidden_prim_types = ["DistantLight", "DomeLight"]
```

Tune the thresholds and patterns to match your pipeline, then commit the file
next to the repo's `README.md` so every contributor sees the contract.

---

## Exit codes reference

| Exit code | Meaning | How to react in CI |
|-----------|---------|--------------------|
| `0` | No findings, or every finding was repaired via `--fix`. | Allow merge. |
| `1` | Findings at or above `--fail-on` threshold. | Block merge, print the report. |
| `2` | Invalid target, unknown rule, or plugin load error. | Fail the job, mark as misconfiguration. |

Use `--fail-on none` to turn the linter into an advisory reporter that never
blocks the job — still useful when you want the artifact but not the gate.
