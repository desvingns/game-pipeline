# contract-startup — read this before any mode

Binding for every runbook. Cheap, and it is what keeps parallel sessions from
overwriting each other.

## 1. Orient

Read, in this order, and stop reading as soon as the mode's needs are met:

1. `CLAUDE.md` — stack, layer contract, paths, commands.
2. `STATE.md` — what is done, in flight, blocked.
3. The relevant board: `{{AGENT_DIR}}/specs/` for code work, `art/cards/` for art work.
4. For any mode that touches something visible: `art/style/style-bible.json`.

Do not bulk-read `DOCUMENTATION.md`; open the section you need.

## 2. Establish the environment honestly

Do not assume a tool exists. The gate scripts report `error_kind` when the engine
or interpreter is missing, and that answer is the truth:

- `godot_not_found` — Godot 4 is not installed or `GODOT_BIN` is not set.
- `python_missing` — no interpreter with Pillow; the asset gate cannot run.
- `not_style_locked` — no frozen reference sheet; no production art may be made.

Report the condition and stop the affected part of the run. Never substitute a
hand-written approximation for a gate that could not run, and never report a gate
as passing because it did not fail.

## 3. Scope

One mode per invocation, one item per mode. Work discovered along the way goes to
the board as a new card; it does not join the current run. A run that grows while
executing cannot be reviewed, because nobody agreed to what it became.

## 4. Human gates

These stop and wait, always, including under `--unattended`:

- **STYLE LOCK** — freezing the reference sheet sets the visual direction of
  every asset that follows.
- **SPEC approval** — before implementation begins.
- **`git push`** — outward-facing.
- **Replacing an existing asset or content file** — name the file and the reason.

Advisory gates (which of two equivalent approaches, whether to file a follow-up)
may proceed on the recommended default under `--unattended`, and every such
decision is listed at the end of the run.

## 5. Close-out

Every mode that changed anything ends with:

1. The gate JSON lines, quoted verbatim.
2. `{{PREFIX}}-docs` to refresh `STATE.md` and append history.
3. A plain statement of what was not done and why.
