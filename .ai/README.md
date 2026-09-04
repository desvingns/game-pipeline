# `.ai/` — shared cross-tool workspace

Git-tracked. Both Claude Code and Codex CLI read and write here; git is the
transport between them.

```
.ai/handoff.md              live session state: DONE / DECISIONS / NEXT / OWNER / BLOCKERS
.ai/memory/MEMORY.md        index of durable framework knowledge
.ai/memory/*.md             one fact per file
.ai/tasks/INDEX.md          task index; only ACTIVE entries are read at session start
.ai/changes/agent-skill-log.md   append-only log of agent/template edits
.ai/changes/sync-state.json      per-adapter cursor into that log
```

## Protocol

**At session start** — read `AGENTS.md`, then `.ai/handoff.md`, then
`.ai/memory/MEMORY.md`, then `.ai/tasks/INDEX.md` and only the tasks listed under
ACTIVE. Historical task files are audit records, opened on demand, never
bulk-loaded.

**During** — keep your task file's STATUS current. Log every agent, runbook,
profile or script edit as one append-only entry in
`.ai/changes/agent-skill-log.md`.

**At hand-off** — rewrite `.ai/handoff.md` and commit it with your work. Do not
touch files another tool lists under IN PROGRESS.

## Why a change log with a cursor

A sync that re-reads the whole system to find what moved costs the same whether
one file changed or none did. An append-only log plus a per-adapter cursor means
a sync reads only what happened since it last ran. `sync-state.json` is written by
the sync tooling and by nothing else.
