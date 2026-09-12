# Shared SPEC board — {{PROJECT_NAME}}

Both Codex and Claude Code use SPECS/. Never create a per-tool board.
Code: SPECS/backlog and SPECS/done. Art: art/cards/backlog, active, done.
Unfinished code stays in backlog with BACKLOG, ACTIVE, REVIEW or BLOCKED status.
DONE moves the card to done and updates all Markdown links and index status.
Existing board documents/ID schemes remain authoritative. Read contract-work.md.

One Markdown file per bounded task. Example:

```markdown
# SPEC-042 — Frost tower slows enemies in radius

Status: **BACKLOG**

## Goal
Apply a bounded slow effect without changing command/replay semantics.

## Dependencies
- SPEC-041

## Acceptance criteria
1. The effect applies and expires at the configured tick.
2. Multiple towers apply the strongest slow without stacking.

## Exclusions
New tower art is owned by ART-018; upgrades are another SPEC.

## Completion evidence
Filled with real commands, results and artifacts when implemented.

<!-- gp-meta {"dependencies":["SPEC-041"],"gates":["unit","replay"],"art":["ART-018"],"acceptance_ids":["AC1","AC2"]} -->
```

The optional gp-meta JSON gives exact machine fields without replacing Markdown:
id, track, dependencies, prerequisites (existing local paths), gates, art,
acceptance_ids, context, evidence and evidence_sha256. Completion fields are
written by work.sh close. Imported legacy completion documents remain supported;
inspect their evidence before considering a dependency satisfied. Empty acceptance
never qualifies a task as ready. No placeholder or missing tool becomes a pass.

If SPECS is absent, delegate discovery first; migration archives sources, preserves
text and repairs links. A present empty backlog is reported, not populated with
invented work. Work discovered mid-run becomes a separate proposed card.
