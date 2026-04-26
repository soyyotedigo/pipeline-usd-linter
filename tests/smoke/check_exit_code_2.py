"""Smoke check used by CI: missing target must exit with code 2."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        ["usd-linter", "tests/fixtures/does_not_exist.usda"],
        check=False,
    )
    if result.returncode != 2:
        print(
            f"Expected exit code 2 for missing target, got {result.returncode}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
