"""Load CC-01 contract examples and materialise RFC 6902-style negative patches."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

EXAMPLES = Path(__file__).resolve().parents[2] / "docs" / "decisions" / "examples"


def _strip_comments(value: Any) -> Any:
    """Drop ``_comment`` documentation keys; they are fixture notes, not wire data."""
    if isinstance(value, dict):
        return {k: _strip_comments(v) for k, v in value.items() if k != "_comment"}
    if isinstance(value, list):
        return [_strip_comments(v) for v in value]
    return value


def load(name: str) -> Any:
    return _strip_comments(json.loads((EXAMPLES / name).read_text()))


def _tokens(pointer: str) -> list[str]:
    if not pointer:
        return []
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def _step(value: Any, token: str) -> Any:
    return value[int(token)] if isinstance(value, list) else value[token]


def select(document: Any, pointer: str) -> Any:
    for token in _tokens(pointer):
        document = _step(document, token)
    return document


def materialise(case: dict[str, Any], patched: bool = True) -> Any:
    value = copy.deepcopy(select(load(case["base"]["file"]), case["base"]["pointer"]))
    if not patched:
        return value
    for patch in case["patches"]:
        *parents, last = _tokens(patch["path"])
        target = value
        for token in parents:
            target = _step(target, token)
        key: Any = int(last) if isinstance(target, list) else last
        if patch["op"] == "remove":
            del target[key]
        elif patch["op"] == "replace":
            _ = target[key]  # replace requires an existing member
            target[key] = copy.deepcopy(patch["value"])
        elif patch["op"] == "add":
            target[key] = copy.deepcopy(patch["value"])
        else:
            raise ValueError(f"unsupported op {patch['op']}")
    return value
