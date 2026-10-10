# Measurement guide

## What to measure

- **Tool-output bytes:** UTF-8 byte length returned to the model. This is a stable local proxy, not an exact token bill.
- **Tool calls:** Count calls needed to reach the stopping condition.
- **Files loaded:** Count instruction and source files whose contents entered context.
- **Task quality:** Check completeness, source fidelity, project isolation, privacy, and required approvals.

Label exact local counts as **Observed**, conclusions drawn from them as **Inferred**, future changes as **Proposed**, and missing evidence as **Unknown**.

## Representative tests

Use three to five real, non-sensitive tasks from the target project. Include at least:

1. project orientation or routing;
2. a scoped search or source lookup;
3. a status or validation check;
4. one task involving a large registry, report, export, or log when the project has one.

Run the same prompts and success checks before and after each change. Avoid synthetic tasks that favor the intended optimization.

## Acceptance criteria

Accept an optimization only when all are true:

- token-facing output is lower for at least one representative task;
- no representative task requires more work overall without a documented reason;
- the same factual and validation requirements are met;
- no private or cross-project material is exposed;
- the change is reversible and its scope is clear.

Do not claim exact token or monetary savings from byte counts alone. Report the byte reduction and, if useful, a clearly labeled estimate.

## Common interventions

- Change unconditional workspace-index reads to conditional routing when the target is already known.
- Replace full-file reads with `rg`, field selection, line ranges, or a project parser.
- Add a result limit to JSON or structured search output.
- Replace repeated prose in root instructions with a short route to a task-specific skill.
- Keep generated exports and diagnostics outside project roots or in ignored intake folders when the project rules permit it.
- Scope `git status`, tests, and inventories to the active project.

## Audit script

Run:

```bash
python3 scripts/context_budget_audit.py /absolute/path/to/project
```

Useful options:

```bash
python3 scripts/context_budget_audit.py /absolute/path/to/project --max-depth 3 --limit 15 --json
```

The script reads directory metadata and counts lines only in likely instruction files. It does not print file contents, modify files, estimate billing tokens, or decide that a large file is wasteful.

## Actual Codex usage

Run `python3 scripts/codex_token_usage.py <jsonl-or-directory>` to measure
Codex JSONL usage. The script uses changes in cumulative `total_token_usage` to
ignore repeated snapshots and falls back to `last_token_usage` if a counter
resets. Use timezone-aware ISO 8601 values with `--since` and `--until` for an
inclusive period. The output is a privacy-safe JSON object containing only task
IDs, models, timestamps, call counts, and usage fields. Treat cached input as
usage, not as proven monetary savings; pricing depends on the confirmed
execution and billing mode. Use `--total-only` when only the aggregate is
needed; it retains task IDs and all usage fields while omitting duplicated
per-task structures.
