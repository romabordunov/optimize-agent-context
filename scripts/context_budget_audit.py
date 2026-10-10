#!/usr/bin/env python3
"""Produce a bounded, metadata-first context audit for one project."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md", "SKILLS_INDEX.md", "WORKSPACE_INDEX.md"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure likely context surfaces without printing their contents."
    )
    parser.add_argument("target", type=Path, help="Project or workspace directory")
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def iter_files(root: Path, max_depth: int):
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS and not name.startswith(".") and depth < max_depth
        ]
        for filename in filenames:
            yield current_path / filename


def line_count(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def git_status_metrics(root: Path) -> dict[str, int] | None:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--short", "--", "."],
        check=False,
        capture_output=True,
        text=False,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    return {"entries": len(lines), "output_bytes": len(result.stdout)}


def audit(root: Path, max_depth: int, limit: int) -> dict[str, object]:
    instruction_files: list[dict[str, object]] = []
    large_files: list[dict[str, object]] = []

    for path in iter_files(root, max_depth):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        relative = str(path.relative_to(root))
        if path.name in INSTRUCTION_NAMES:
            instruction_files.append(
                {"path": relative, "bytes": size, "lines": line_count(path)}
            )
        large_files.append({"path": relative, "bytes": size})

    instruction_files.sort(key=lambda item: str(item["path"]))
    large_files.sort(key=lambda item: (-int(item["bytes"]), str(item["path"])))

    return {
        "target": str(root),
        "max_depth": max_depth,
        "instruction_files": instruction_files[:limit],
        "largest_files": large_files[:limit],
        "git_status": git_status_metrics(root),
        "notes": [
            "File size is a candidate signal, not proof that content is unnecessary.",
            "Output byte counts are local proxies and are not exact billing tokens.",
        ],
    }


def render_text(report: dict[str, object]) -> str:
    lines = [f"Target: {report['target']}", f"Max depth: {report['max_depth']}"]
    lines.append("\nInstruction surfaces:")
    for item in report["instruction_files"]:
        lines.append(f"- {item['path']}: {item['bytes']} bytes, {item['lines']} lines")
    lines.append("\nLargest files (metadata only):")
    for item in report["largest_files"]:
        lines.append(f"- {item['path']}: {item['bytes']} bytes")
    status = report["git_status"]
    if status is not None:
        lines.append(
            f"\nScoped git status: {status['entries']} entries, {status['output_bytes']} output bytes"
        )
    lines.append("\nNotes:")
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.max_depth < 0 or args.limit < 1:
        raise SystemExit("--max-depth must be >= 0 and --limit must be >= 1")
    root = args.target.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    report = audit(root, args.max_depth, args.limit)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
