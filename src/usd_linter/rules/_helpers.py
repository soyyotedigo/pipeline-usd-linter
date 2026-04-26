"""Shared prim-traversal helpers for rule implementations."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedPrim


_QUOTED_STRING_RE = re.compile(r'"([^"]+)"')


def children_of(prims: list[ParsedPrim], parent_path: str) -> list[ParsedPrim]:
    """Return prims that are direct children of *parent_path*."""
    depth = parent_path.count("/") + 1
    prefix = parent_path + "/"
    return [p for p in prims if p.path.startswith(prefix) and p.path.count("/") == depth]


def descendants_of(prims: list[ParsedPrim], parent_path: str) -> list[ParsedPrim]:
    """Return all prims anywhere under *parent_path*."""
    prefix = parent_path + "/"
    return [p for p in prims if p.path.startswith(prefix)]


def root_prims(prims: list[ParsedPrim]) -> list[ParsedPrim]:
    """Return top-level prims (depth 1, path like /Name)."""
    return [p for p in prims if p.path.count("/") == 1]


def depth_of(prim_path: str) -> int:
    """Return the depth of a prim path (number of path components)."""
    return prim_path.count("/")


def extract_joint_names(raw_joints: str) -> list[str]:
    """Extract the terminal joint name from each quoted path in a Skeleton.joints value."""
    return [joint_path.rsplit("/", 1)[-1] for joint_path in _QUOTED_STRING_RE.findall(raw_joints)]
