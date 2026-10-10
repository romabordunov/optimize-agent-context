# Optimize Agent Context

A reusable agent skill for finding and reducing avoidable context use in Codex or
Claude workspaces without weakening source quality, privacy, project isolation,
or approval boundaries.

The central idea is simple: reduce repeated reads and oversized tool output only
when the saving is measurable and the result still passes the same quality and
safety checks.

## Important boundary

This is an audit skill, not a prompt to load into every task.

For ordinary research, writing, or coding work, the agent should apply only the
short operating rules in `SKILL.md`. It should load the measurement references
and run the scripts only when the user explicitly requests an audit, benchmark,
or context optimization. The audit itself adds context and tool calls.

## Package contents

```text
optimize-agent-context/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- measurement.md
|   `-- long-task-handoff.md
`-- scripts/
    |-- context_budget_audit.py
    `-- codex_token_usage.py
```

- `SKILL.md` contains the routing rules, audit workflow, safeguards, and expected
  deliverable.
- `references/measurement.md` defines the metrics, test design, and acceptance
  criteria.
- `references/long-task-handoff.md` provides an optional protocol for continuing
  a long task in a fresh context.
- `scripts/context_budget_audit.py` reports bounded project metadata without
  printing file contents.
- `scripts/codex_token_usage.py` summarizes usage events from Codex JSONL logs
  without emitting prompts, messages, or tool output.

## Install

Copy the whole `optimize-agent-context` directory into a skills directory scanned
by your agent. Common locations include a project-local `.agents/skills/` folder
or the Codex user skills directory at `~/.codex/skills/`.

The folder name must stay `optimize-agent-context`, and `SKILL.md` must remain at
its root. `agents/openai.yaml` provides optional Codex UI metadata; other agents
can ignore it.

## Use

Example requests:

```text
Use $optimize-agent-context to audit this workspace for avoidable context use.
```

```text
Benchmark the current retrieval workflow before and after a bounded-context change.
```

```text
Review the AGENTS.md and CLAUDE.md loading strategy without changing any files.
```

The default audit command is:

```bash
python3 scripts/context_budget_audit.py /absolute/path/to/project
```

To summarize Codex usage from one rollout file or a directory of JSONL files:

```bash
python3 scripts/codex_token_usage.py /path/to/jsonl-or-directory --total-only
```

Both scripts support `--help`.

## Requirements

- Python 3.10 or newer.
- Git is optional. The project audit includes scoped Git status metadata only
  when the target is a Git worktree.
- The usage script expects Codex JSONL event logs. It does not estimate usage for
  other agent runtimes.

## Privacy and measurement limits

- The project audit reads directory metadata and counts lines only in likely
  instruction files. It does not print file contents.
- The Codex usage script emits task IDs, models, timestamps, call counts, and
  usage fields. It does not emit conversation or tool content.
- Tool-output bytes are a local proxy, not an exact token or billing measure.
- Uncached input is not the same as new information.
- Before-and-after comparisons should use the same tasks and success criteria.
- Run the tools locally on data you are authorized to inspect.

## License

MIT. See `LICENSE`.
