from dataclasses import dataclass, field
from pathlib import Path


SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


@dataclass(slots=True)
class LintMessage:
    rule_id: str
    message: str
    severity: str = "error"
    path: Path | None = None
    line: int | None = None
    prim_path: str | None = None
    layer: str | None = None
    suggestion: str | None = None
    fixed: bool = False

    def to_dict(self) -> dict[str, object | None]:
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity,
            "path": str(self.path) if self.path is not None else None,
            "line": self.line,
            "prim_path": self.prim_path,
            "layer": self.layer,
            "suggestion": self.suggestion,
            "fixed": self.fixed,
        }


@dataclass(slots=True)
class RuleResult:
    """Result of a single rule check. Passed is derived: no messages = passed."""

    messages: list[LintMessage] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.messages) == 0


@dataclass(slots=True)
class LintReport:
    target: Path
    messages: list[LintMessage] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def has_errors(self) -> bool:
        return any(message.severity == "error" for message in self.messages)

    def counts(self) -> dict[str, int]:
        counts = {"error": 0, "warning": 0, "info": 0}
        for message in self.messages:
            counts[message.severity] += 1
        return counts

    def should_fail(self, fail_on: str) -> bool:
        if fail_on == "none":
            return False

        threshold = SEVERITY_ORDER[fail_on]
        return any(
            SEVERITY_ORDER[message.severity] >= threshold and not message.fixed
            for message in self.messages
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "target": str(self.target),
            "files_scanned": self.files_scanned,
            "summary": self.counts(),
            "messages": [message.to_dict() for message in self.messages],
        }
