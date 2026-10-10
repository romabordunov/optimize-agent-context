#!/usr/bin/env python3
"""Summarize Codex usage without emitting conversation or tool content."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


class SafeError(Exception):
    """Error whose message contains no source content."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report only Codex task IDs, models, timestamps, call counts, and usage."
        )
    )
    parser.add_argument("source", type=Path, help="One Codex JSONL file or a directory")
    parser.add_argument("--since", help="Inclusive ISO 8601 lower timestamp")
    parser.add_argument("--until", help="Inclusive ISO 8601 upper timestamp")
    parser.add_argument(
        "--total-only",
        action="store_true",
        help="Emit one aggregate with task IDs instead of per-task records",
    )
    return parser.parse_args()


def parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SafeError("invalid_timestamp") from exc
    if parsed.tzinfo is None:
        raise SafeError("timestamp_requires_timezone")
    return parsed


def source_files(source: Path) -> list[Path]:
    source = source.expanduser().resolve()
    if source.is_file():
        return [source]
    if source.is_dir():
        files = sorted(path for path in source.rglob("*.jsonl") if path.is_file())
        if files:
            return files
        raise SafeError("no_jsonl_files")
    raise SafeError("source_not_found")


def empty_usage() -> dict[str, int]:
    return {field: 0 for field in TOKEN_FIELDS}


def safe_usage(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    usage = empty_usage()
    found = False
    for field in TOKEN_FIELDS:
        field_value = value.get(field)
        if isinstance(field_value, int) and not isinstance(field_value, bool):
            usage[field] = field_value
            found = True
    return usage if found else None


def add_usage(target: dict[str, int], addition: dict[str, int]) -> None:
    for field in TOKEN_FIELDS:
        target[field] += addition[field]


def usage_delta(
    current: dict[str, int], previous: dict[str, int]
) -> dict[str, int] | None:
    if any(current[field] < previous[field] for field in TOKEN_FIELDS):
        return None
    return {field: current[field] - previous[field] for field in TOKEN_FIELDS}


def read_task(path: Path, since: datetime | None, until: datetime | None) -> dict[str, object] | None:
    task_id: str | None = None
    current_model: str | None = None
    models: set[str] = set()
    first_time: str | None = None
    last_time: str | None = None
    calls = 0
    usage = empty_usage()
    previous_total_usage: dict[str, int] | None = None

    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise SafeError("invalid_jsonl") from exc
                if not isinstance(record, dict):
                    continue
                record_type = record.get("type")
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    continue

                if record_type == "session_meta":
                    candidate = payload.get("id")
                    # Forked rollout files may embed parent history, including a
                    # second session_meta record. The first record identifies the
                    # file/task being measured; inherited metadata must not
                    # overwrite it.
                    if task_id is None and isinstance(candidate, str):
                        task_id = candidate
                    continue

                if record_type == "turn_context":
                    candidate = payload.get("model")
                    if isinstance(candidate, str):
                        current_model = candidate
                    continue

                if record_type != "event_msg" or payload.get("type") != "token_count":
                    continue
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                event_usage = safe_usage(info.get("last_token_usage"))
                cumulative_usage = safe_usage(info.get("total_token_usage"))
                timestamp = record.get("timestamp")
                if event_usage is None or not isinstance(timestamp, str):
                    continue
                if cumulative_usage is not None:
                    if previous_total_usage == cumulative_usage:
                        continue
                    if previous_total_usage is not None:
                        event_usage = (
                            usage_delta(cumulative_usage, previous_total_usage)
                            or event_usage
                        )
                    previous_total_usage = cumulative_usage
                event_time = parse_timestamp(timestamp)
                if since is not None and event_time < since:
                    continue
                if until is not None and event_time > until:
                    continue

                calls += 1
                add_usage(usage, event_usage)
                first_time = first_time or timestamp
                last_time = timestamp
                if current_model is not None:
                    models.add(current_model)
    except OSError as exc:
        raise SafeError("source_unreadable") from exc

    if calls == 0:
        return None
    return {
        "task_id": task_id,
        "models": sorted(models),
        "time": {"from": first_time, "to": last_time},
        "calls": calls,
        "usage": usage,
    }


def merge_tasks(tasks: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[tuple[str | None, int], dict[str, object]] = {}
    known: dict[str, dict[str, object]] = {}
    unknown_index = 0
    for task in tasks:
        task_id = task["task_id"]
        if isinstance(task_id, str):
            target = known.get(task_id)
            if target is None:
                known[task_id] = task
                merged[(task_id, 0)] = task
                continue
        else:
            unknown_index += 1
            merged[(None, unknown_index)] = task
            continue

        target["models"] = sorted(set(target["models"]) | set(task["models"]))
        target["calls"] = int(target["calls"]) + int(task["calls"])
        add_usage(target["usage"], task["usage"])
        target_time = target["time"]
        task_time = task["time"]
        target_time["from"] = min(target_time["from"], task_time["from"])
        target_time["to"] = max(target_time["to"], task_time["to"])
    return sorted(merged.values(), key=lambda item: (item["time"]["from"], item["task_id"] or ""))


def total(tasks: list[dict[str, object]]) -> dict[str, object]:
    usage = empty_usage()
    models: set[str] = set()
    calls = 0
    starts: list[str] = []
    ends: list[str] = []
    for task in tasks:
        add_usage(usage, task["usage"])
        models.update(task["models"])
        calls += int(task["calls"])
        starts.append(task["time"]["from"])
        ends.append(task["time"]["to"])
    return {
        "models": sorted(models),
        "time": {"from": min(starts) if starts else None, "to": max(ends) if ends else None},
        "calls": calls,
        "usage": usage,
    }


def main() -> int:
    args = parse_args()
    try:
        since = parse_timestamp(args.since) if args.since else None
        until = parse_timestamp(args.until) if args.until else None
        if since is not None and until is not None and since > until:
            raise SafeError("invalid_time_range")
        tasks = [
            task
            for path in source_files(args.source)
            if (task := read_task(path, since, until)) is not None
        ]
        tasks = merge_tasks(tasks)
    except SafeError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2

    summary = total(tasks)
    if args.total_only:
        output = {
            "task_ids": [task["task_id"] for task in tasks],
            **summary,
        }
    else:
        output = {"tasks": tasks, "total": summary}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
