# Long-task handoff

Use this opt-in protocol when a long task should continue in a fresh context.
Do not delete, rewrite, or automatically compact the original task.

## Preconditions

- Confirm the project, permitted writes, stopping condition, and authoritative files.
- Measure the current task with `scripts/codex_token_usage.py`.
- Obtain authorization before creating a separate Codex task.
- Do not hand off during an unresolved approval, destructive mutation, or active error investigation.
- Exclude secrets, private source text, and unrelated project context.

## Handoff schema

Include only task-critical state:

```text
Objective:
Authoritative sources:
Observed evidence:
Decisions:
Files and external effects:
Constraints and permissions:
Risks and unknowns:
Rejected or superseded claims:
Open work:
Next action:
```

Preserve exact identifiers, paths, error codes, counts, timestamps, and statuses.
Label inference and uncertainty explicitly. Keep source material available; the
handoff is an index and continuation state, not a replacement for evidence.

## Quality gate

Before using the handoff for work, test whether a fresh task can answer:

1. What is the objective and stopping condition?
2. What is completed, in progress, and not started?
3. Which evidence, decisions, files, and external effects must be preserved?
4. Which safety, privacy, source, and project boundaries still apply?
5. What is the next authorized action, and what remains unknown?

Require 5/5 correct answers. Fail the handoff if it invents a fact, drops an
authorization boundary, treats inference as evidence, or cannot identify the
next action. Repair and re-run the gate before continuing.

## Measurement

After the first completed turn in the fresh task, record:

- model calls and all reported usage fields;
- whether the five answers remained correct;
- repeated file reads or rediscovery caused by missing context;
- new errors, omissions, or manual corrections.

Accept the handoff only when continuity passes 5/5, no safeguard is weakened,
and token-facing usage falls without compensating rework. Report total usage,
cached input, and task quality separately; do not infer monetary savings.

## Stop conditions

- The handoff would expose sensitive or cross-project material.
- Critical evidence cannot be referenced without copying private source text.
- Work depends on unresolved live state or an approval request.
- The fresh task needs substantial rediscovery or fails any quality probe.
