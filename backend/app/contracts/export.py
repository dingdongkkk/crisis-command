"""Generate ``contracts/schema/crisis-command.schema.json`` and ``contracts/openapi.json``.

Run from ``backend/``: ``uv run python -m app.contracts.export`` (writes files) or
``... --check`` (fails if the committed files are stale). Output is deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import ADAPTERS, SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "contracts" / "schema" / "crisis-command.schema.json"
OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi.json"
REF_TEMPLATE = "#/$defs/{model}"


def build_schema() -> dict[str, Any]:
    defs: dict[str, Any] = {}

    def merge(name: str, schema: dict[str, Any]) -> None:
        if name in defs and defs[name] != schema:
            raise RuntimeError(f"conflicting JSON Schema definitions for {name}")
        defs[name] = schema

    for name, adapter in sorted(ADAPTERS.items()):
        schema = adapter.json_schema(ref_template=REF_TEMPLATE, mode="validation")
        for def_name, definition in schema.pop("$defs", {}).items():
            merge(def_name, definition)
        if schema.get("$ref") == REF_TEMPLATE.format(model=name):
            continue  # The top-level model is already a named definition.
        merge(name, schema)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://crisis-command.local/schema/crisis-command.schema.json",
        "title": "CrisisCommandContracts",
        "description": (
            f"Crisis Command contract schema_version {SCHEMA_VERSION}. Generated from "
            "backend/app/contracts; do not edit by hand."
        ),
        "$defs": dict(sorted(defs.items())),
    }


def build_openapi() -> dict[str, Any]:
    from app.main import create_app

    return create_app().openapi()


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args(argv)
    outputs = {SCHEMA_PATH: render(build_schema()), OPENAPI_PATH: render(build_openapi())}
    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text() != text]
    if args.check:
        for path in stale:
            print(f"stale generated contract: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1 if stale else 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
