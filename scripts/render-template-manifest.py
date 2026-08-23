#!/usr/bin/env python3
"""Render the exact provenance manifest for one reviewed repository template."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SKIP_PARTS = {
    ".build",
    ".dart_tool",
    ".gradle",
    ".pytest_cache",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}


def template_files(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise RuntimeError(f"template directory missing: {root}")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError(f"template symlink is forbidden: {path}")
        if path.is_file():
            files[relative.as_posix()] = path.read_bytes()
    if not files:
        raise RuntimeError(f"template contains no files: {root}")
    return files


def render(root: Path, source: str, template: str) -> bytes:
    files = template_files(root)
    document = {
        "files": {
            path: hashlib.sha256(content).hexdigest()
            for path, content in sorted(files.items())
        },
        "schema": "ores.otel.repository-template/v1",
        "source": source,
        "template": template,
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--source", default="ores-otel/.github")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = render(args.template_root.resolve(), args.source, args.template_id)
    output = args.output.resolve()
    if args.check:
        if not output.is_file() or output.read_bytes() != payload:
            raise RuntimeError(f"template provenance manifest is stale: {output}")
        print(f"template provenance manifest is current: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(f"rendered template provenance manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
