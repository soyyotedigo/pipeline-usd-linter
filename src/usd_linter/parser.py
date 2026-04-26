from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import os
import re
import sys


PRIM_DECLARATION_RE = re.compile(r'^\s*(def|over|class)\s+(?:(\w+)\s+)?"([^"]+)"')
ASSIGNMENT_RE = re.compile(r"^\s*(\w+)\s*=\s*(.+?)\s*$")
ASSET_REFERENCE_RE = re.compile(r"@([^@\r\n]+)@")
REFERENCE_FIELD_RE = re.compile(r"\breferences\b")
PAYLOAD_FIELD_RE = re.compile(r"\bpayload(?:s)?\b")
SUBLAYERS_FIELD_RE = re.compile(r"^\s*subLayers\s*=")
# Attribute capture inside prim scopes
TYPED_ATTR_RE = re.compile(
    r"^\s*(?:uniform\s+|custom\s+|varying\s+)?(\w+(?:\[\])?)\s+([\w:]+)\s*=\s*(.+?)\s*$"
)
RELATION_RE = re.compile(r"^\s*rel\s+([\w:]+)\s*=\s*(<[^>]+>)\s*$")
VARIANT_SET_RE = re.compile(r'^\s*variantSet\s+"([^"]+)"')


class ParseError(ValueError):
    """Raised when a USD layer cannot be parsed."""


@dataclass(slots=True)
class ParsedPrim:
    name: str
    specifier: str
    path: str
    line: int
    type_name: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    prim_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AssetReference:
    raw_path: str
    line: int


@dataclass(slots=True)
class ParsedStage:
    path: Path
    prims: list[ParsedPrim] = field(default_factory=list)
    stage_metadata: dict[str, str] = field(default_factory=dict)
    asset_references: list[AssetReference] = field(default_factory=list)
    asset_payloads: list[AssetReference] = field(default_factory=list)
    sublayers: list[AssetReference] = field(default_factory=list)
    variant_sets: list[str] = field(default_factory=list)


def parse_stage(file_path: Path) -> ParsedStage:
    file_path = file_path.resolve()
    pxr_stage = open_stage(file_path)
    return parse_opened_stage(file_path, pxr_stage)


def open_stage(file_path: Path):
    return _open_stage_with_pxr(file_path.resolve())


def parse_opened_stage(file_path: Path, pxr_stage) -> ParsedStage:
    file_path = file_path.resolve()
    root_layer = pxr_stage.GetRootLayer()
    try:
        with suppress_pxr_diagnostics():
            text = root_layer.ExportToString()
    except Exception as exc:  # pragma: no cover - depends on pxr runtime behavior
        raise ParseError("Could not export USD stage to text through pxr.") from exc

    stage = _parse_stage_from_text(file_path, text)
    _merge_root_sublayers(stage, getattr(root_layer, "subLayerPaths", []))
    _merge_sublayers_from_source(stage, file_path)
    return stage


def _open_stage_with_pxr(file_path: Path):
    try:
        from pxr import Usd
    except ImportError as exc:
        raise ParseError(
            "usd-core is required. Install it with: pip install usd-core"
        ) from exc

    try:
        with suppress_pxr_diagnostics():
            stage = Usd.Stage.Open(str(file_path))
    except Exception as exc:  # pragma: no cover - depends on pxr runtime behavior
        raise ParseError(f"Failed to open USD layer with pxr: {file_path}") from exc

    if stage is None:
        raise ParseError(f"Failed to open USD layer with pxr: {file_path}")

    return stage


@contextmanager
def suppress_pxr_diagnostics():
    """Silence pxr/OpenUSD C++ warnings written directly to stderr.

    pxr emits Tf warnings (missing references, unresolved layers) at the C++ layer,
    bypassing Python's sys.stderr. We dup() the underlying fd to /dev/null around
    the call so structured lint output stays clean.
    """
    stderr_fd = 2
    try:
        saved_fd = os.dup(stderr_fd)
    except OSError:
        yield
        return

    try:
        sys.stderr.flush()
    except (ValueError, OSError):
        pass

    devnull_fd = None
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        try:
            yield
        finally:
            try:
                sys.stderr.flush()
            except (ValueError, OSError):
                pass
            os.dup2(saved_fd, stderr_fd)
    finally:
        if devnull_fd is not None:
            os.close(devnull_fd)
        os.close(saved_fd)


def _parse_stage_from_text(file_path: Path, text: str) -> ParsedStage:
    stage = ParsedStage(path=file_path)
    active_stack: list[ParsedPrim] = []
    pending_prims: deque[ParsedPrim] = deque()
    qualifier_prim: ParsedPrim | None = None
    in_qualifier = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # --- Stage-level metadata (before any prim scope) ---
        if not active_stack and not pending_prims and not in_qualifier:
            assignment = ASSIGNMENT_RE.match(stripped)
            if assignment is not None:
                key, value = assignment.groups()
                stage.stage_metadata[key] = _clean_assignment_value(value)

        # --- Composition arcs and sublayers ---
        if SUBLAYERS_FIELD_RE.match(stripped):
            _append_asset_paths(stage.sublayers, line, line_number)
        elif REFERENCE_FIELD_RE.search(stripped):
            _append_asset_paths(stage.asset_references, line, line_number)
        elif PAYLOAD_FIELD_RE.search(stripped):
            _append_asset_paths(stage.asset_payloads, line, line_number)

        # --- Variant set declarations (anywhere) ---
        vs_match = VARIANT_SET_RE.match(line)
        if vs_match is not None:
            vs_name = vs_match.group(1)
            if vs_name not in stage.variant_sets:
                stage.variant_sets.append(vs_name)

        # --- Prim qualifier block ( ... ) ---
        if in_qualifier:
            if ")" in stripped:
                in_qualifier = False
                qualifier_prim = None
            else:
                assignment = ASSIGNMENT_RE.match(stripped)
                if assignment is not None and qualifier_prim is not None:
                    key, value = assignment.groups()
                    qualifier_prim.prim_metadata[key] = _clean_assignment_value(value)
            continue

        # --- Prim declaration ---
        prim_match = PRIM_DECLARATION_RE.match(line)
        if prim_match is not None:
            specifier, type_name, prim_name = prim_match.groups()
            parent_path = active_stack[-1].path if active_stack else ""
            prim_path = f"{parent_path}/{prim_name}" if parent_path else f"/{prim_name}"
            prim = ParsedPrim(
                name=prim_name,
                specifier=specifier,
                path=prim_path,
                line=line_number,
                type_name=type_name,
            )
            stage.prims.append(prim)
            pending_prims.append(prim)
            if "(" in stripped and ")" not in stripped.split("(", 1)[1]:
                in_qualifier = True
                qualifier_prim = prim
            _open_pending_prims(stripped, pending_prims, active_stack)
            _close_prim_scopes(stripped, active_stack, pending_prims)
            continue

        if stripped.startswith("{"):
            _open_pending_prims(stripped, pending_prims, active_stack)
            continue

        if stripped.startswith("}"):
            _close_prim_scopes(stripped, active_stack, pending_prims)
            continue

        # --- Prim-level attributes (inside an active prim scope) ---
        if active_stack:
            rel_match = RELATION_RE.match(stripped)
            if rel_match is not None:
                attr_name, attr_value = rel_match.group(1), rel_match.group(2)
                active_stack[-1].attributes[attr_name] = attr_value
            else:
                attr_match = TYPED_ATTR_RE.match(stripped)
                if attr_match is not None:
                    attr_name = attr_match.group(2)
                    attr_value = attr_match.group(3)
                    active_stack[-1].attributes[attr_name] = _clean_assignment_value(attr_value)

    return stage


def _open_pending_prims(
    line: str,
    pending_prims: deque[ParsedPrim],
    active_stack: list[ParsedPrim],
) -> None:
    for _ in range(min(line.count("{"), len(pending_prims))):
        active_stack.append(pending_prims.popleft())


def _close_prim_scopes(
    line: str,
    active_stack: list[ParsedPrim],
    pending_prims: deque[ParsedPrim],
) -> None:
    for _ in range(line.count("}")):
        if active_stack:
            active_stack.pop()
        elif pending_prims:
            pending_prims.pop()


def _clean_assignment_value(value: str) -> str:
    cleaned = value.rstrip(",").strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        return cleaned[1:-1]
    return cleaned


def _append_asset_paths(target: list[AssetReference], line: str, line_number: int) -> None:
    for match in ASSET_REFERENCE_RE.finditer(line):
        target.append(AssetReference(raw_path=match.group(1), line=line_number))


def _merge_root_sublayers(stage: ParsedStage, sublayer_paths: object) -> None:
    if not isinstance(sublayer_paths, (list, tuple)):
        return

    existing = {sublayer.raw_path for sublayer in stage.sublayers}
    for raw_path in sublayer_paths:
        if not isinstance(raw_path, str) or raw_path in existing:
            continue
        stage.sublayers.append(AssetReference(raw_path=raw_path, line=1))
        existing.add(raw_path)


def _merge_sublayers_from_source(stage: ParsedStage, file_path: Path) -> None:
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    existing = {sublayer.raw_path for sublayer in stage.sublayers}
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        if not SUBLAYERS_FIELD_RE.match(line.strip()):
            continue
        for match in ASSET_REFERENCE_RE.finditer(line):
            raw_path = match.group(1)
            if raw_path in existing:
                continue
            stage.sublayers.append(AssetReference(raw_path=raw_path, line=line_number))
            existing.add(raw_path)
