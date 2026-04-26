# Docs

This folder explains how `usd-linter` is organized and how execution flows through the codebase.

## Public Documents

| File | Purpose |
|------|---------|
| `architecture.md` | High-level architecture, execution flow, parser behavior, rule system, and code map. |
| `rules.md` | Reference for every built-in rule: severity, behavior, configuration, and limits. |
| `examples/usage-in-ci.md` | Ready-to-copy GitHub Actions, GitLab, pre-commit, and Docker snippets. |

Planning notes and evaluation reports stay in the dev repo and are not part of the public sync.

## Recommended Reading Order

1. Start with `architecture.md` to understand the current implementation.
2. Read `rules.md` to see what the linter actually checks today.
3. Skim `examples/usage-in-ci.md` if you plan to enable the linter in your own pipeline.
