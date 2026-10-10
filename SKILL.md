---
name: optimize-agent-context
description: Audit and reduce avoidable token use in Codex or Claude workspaces while preserving project isolation, evidence quality, privacy, and required approvals. Use when asked to optimize agent context, reduce token or tool-output costs, review AGENTS.md or CLAUDE.md loading, benchmark an agent workflow, or apply context-budget rules across one or more projects.
license: MIT
---

# Optimize Agent Context

Reduce repeated context and oversized tool output only where the saving is observable and does not weaken the result.

## Scope check first

This skill is an audit tool. If it was invoked inside an ordinary task (research,
writing, analysis) rather than a request to audit or measure context use, apply
only the Operating rules below and continue the task. Do not run
`context_budget_audit.py`, do not open the references, and do not measure.
Loading the audit workflow has its own context and tool-call overhead, so reserve
it for explicit audits or benchmarks.

## Workflow

1. Identify the exact project and read its applicable `AGENTS.md` or `CLAUDE.md`. Do not inspect neighboring projects merely to compare them.
2. Establish the task boundary, sensitive paths, permitted writes, expected result, and stopping condition.
3. Run `scripts/context_budget_audit.py <project>` for a metadata-only starting picture. Treat its findings as candidates, not proof of waste.
4. Separate context into:
   - always loaded: short rules needed on nearly every task;
   - routed: project or task instructions loaded after the target is known;
   - queried: indexes, registries, reports, exports, and logs accessed only through bounded search or parsers.
5. Measure representative tasks before changing anything. Record input command, output bytes, tool calls, and whether the answer remained complete.
6. Prefer the smallest reversible intervention: conditional routing, scoped paths, bounded output, deterministic parsers, or removal of duplicated instructions.
7. Repeat the same tasks and compare. Accept a change only when token-facing output falls and the result still passes its original quality and safety checks.
8. Report observed measurements separately from inferred savings and proposed follow-up work.

For a long task that may continue in a fresh context, read
[references/long-task-handoff.md](references/long-task-handoff.md). Use its
opt-in schema and require a 5/5 quality gate before continuation. Never treat a
handoff as permission to delete the original task or discard source evidence.

## Operating rules

- Keep root instructions lean. Put detailed procedures in skills or references that load only when invoked.
- When the current directory and request already identify the project, do not load a workspace-wide index unless routing is ambiguous or the task spans projects.
- Scope searches and status commands to the target path. Add result limits or line ranges before broadening.
- Query large registries, raw exports, logs, and reports with a deterministic tool before reading full artifacts.
- Batch independent read-only checks. Keep dependent steps, approvals, and mutations sequential.
- Stop when the stated result is demonstrated. Do not keep exploring for marginal savings.
- Never trade source fidelity, privacy, project isolation, security checks, or user approvals for a lower token count.
- Do not modify instructions or move files during an audit unless the user authorized implementation.

For metric definitions, test design, and acceptance criteria, read [references/measurement.md](references/measurement.md).

For actual Codex usage, run `python3 scripts/codex_token_usage.py <jsonl-or-directory>`.
Add `--since` and `--until` for an inclusive time range. The script emits only
task IDs, models, timestamps, call counts, and usage fields; it never emits
messages, prompts, or tool results. Add `--total-only` when the aggregate is
enough and per-task records would only enlarge tool output.

## Deliverable

Give the user:

1. the largest verified sources of avoidable context;
2. changes applied or proposed, with their scope;
3. before-and-after measurements for representative tasks;
4. safeguards preserved;
5. remaining uncertainty and the next highest-value test.
