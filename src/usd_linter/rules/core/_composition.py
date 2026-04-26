from pathlib import Path
import re


_ASSET_REFERENCE_RE = re.compile(r"@([^@\r\n]+)@")
_SUBLAYERS_FIELD_RE = re.compile(r"^\s*subLayers\s*=")


def resolve_asset_path(base_dir: Path, raw_path: str) -> Path | None:
    asset_path = raw_path.split("[", maxsplit=1)[0]
    if "://" in asset_path or asset_path.startswith(("<", "$", "anon:")):
        return None

    candidate = Path(asset_path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()


def read_sublayers_from_source(file_path: Path) -> list[tuple[str, int]]:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    sublayers: list[tuple[str, int]] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        if not _SUBLAYERS_FIELD_RE.match(line.strip()):
            continue
        for match in _ASSET_REFERENCE_RE.finditer(line):
            sublayers.append((match.group(1), line_number))
    return sublayers
