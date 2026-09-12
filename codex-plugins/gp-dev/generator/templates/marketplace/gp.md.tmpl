---
description: Game Pipeline orchestrator (/gp) for Godot 2D Android and Godot 3D Windows FPS projects.
argument-hint: --build|--discuss|--style|--design|--level|--art|--animate|--feature|--balance|--gates <args>
---

Game Pipeline is the front door for the current game repository. It bootstraps a
new pipeline when the `gp-dev` skill is selected, then routes work to the
dimension-specific project runtime and agents.

**Cross-platform invariant.** Every shell command runs through Bash (Git Bash on
Windows, native bash elsewhere), never PowerShell.

## Startup and runtime resolution

1. Read the project root instructions (`CLAUDE.md` or `AGENTS.md`) and the
   matching `.claude/.gp-version` or `.codex/.gp-version` stamp.
2. A generated project runtime is authoritative: use
   `<agent-dir>/commands/<prefix>-runtime/` when its `manifest.tsv` exists.
3. If the generated runtime is unavailable, use the plugin fallback matching
   the stamp's `dimension`: `${GP_RUNTIME_ROOT}` when explicitly set, then
   `${CLAUDE_PLUGIN_ROOT}/commands/gp-runtime/<dimension>/` for Claude. Codex
   uses the packaged references beside the `gp-dev` skill.
4. If neither runtime contains `manifest.tsv`, stop and report the missing
   pipeline package. Never invent a workflow from memory.

## Lazy-loading protocol

1. Parse exactly one selector from the table below.
2. If no selector is present, infer it from the request: a whole new game uses
   `--build`; a bounded implementation uses `--feature`; an open design question
   uses `--discuss`.
3. Read exactly one selected runbook and the contracts declared by its first
   `gp-runtime-contracts` marker. Execute `contract-startup.md` first.
4. Preserve the runbook's structured output, human gates, write boundaries and
   selected dimension. Do not preload every runbook.

## Mode dispatch

| Selector | Runbook | Purpose |
|---|---|---|
| `--build` | `build.md` | complete one approved game brief |
| `--discuss` | `discuss.md` | read-only architecture/design options |
| `--style` | `style.md` | style profile, references and STYLE LOCK |
| `--design` | `design.md` | mechanics, loop, feel and content |
| `--level` | `level.md` | maps, routes, waves and encounter pacing |
| `--art` | `art.md` | one asset card from prompt-spec to integration |
| `--animate` | `animate.md` | rigs, clips and procedural feedback |
| `--feature` | `feature.md` | approved SPEC through implementation and gates |
| `--balance` | `balance.md` | tune content against the applicable gate |
| `--gates` | `gates.md` | run every applicable deterministic gate |
| `--adopt`, `--doctor`, `--status`, `--resume`, `--metrics` | `work.md` | shared SPECS execution and diagnostics |

Unknown or conflicting selectors are an error. Show this table and ask for one
selector.

## Modifiers and invariants

- `--next` selects the next item from the relevant board for `--feature` or
  `--art`.
- `--unattended` allows advisory defaults but never approves STYLE LOCK, scope
  changes or outward actions that still require a human gate.
- The selected architecture is binding: 2D keeps engine-free deterministic
  `sim/`; 3D keeps pure seeded rules in `domain/`, Godot physics/navigation in
  `world/`, and shared human/bot commands in `input/`.
- No art enters production before the actual reference sheet is approved and
  frozen. Every generated image and 3D mesh carries provenance.
- Gates report; agents do not claim a pass without the gate JSON. Reviewers warn
  and never fix.
- Model policy is project-local: Codex Luna xhigh / Sol xhigh / Astra high;
  Claude selects native models independently. Do not add a second baseline game,
  paired implementation, model benchmark or experiment protocol.

The `--build` workflow delivers one game through the selected preset and ends
with the package path, controls, gate evidence, visual review and known limits.

All projects use SPECS/. For missing boards, delegate discovery before creating it.
Read contract-work.md for --spec ID, --track NAME, --preview, --batch N and native
model dispatch. Never silently create another per-tool board.
