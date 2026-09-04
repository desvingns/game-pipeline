# Change log format

One append-only entry per agent, runbook, profile, schema or script edit. A sync
reads only entries newer than its cursor in `sync-state.json`, so the cost of
propagating a change is proportional to the change, not to the size of the system.

## Entry

```markdown
## 2026-09-04-short-slug
- kind: agent | runbook | profile | schema | script | doc
- target: templates/art/agents/{{PREFIX}}-art-director.md
- change: one sentence, in the imperative
- why: the observation that prompted it
- breaking: no | yes (what downstream must change)
```

Entries are never edited or removed once written. A mistaken entry is corrected by
a later entry that says so.
