---
description: Game dev orchestrator for {{PROJECT_NAME}} — design, art, build, gates.
---

Game development orchestrator for the {{PROJECT_NAME}} repository. Use for ALL {{PROJECT_NAME}} work.

This command is a compact router. The detailed workflow is loaded lazily; do not preload other
modes.

**Cross-platform invariant.** Every shell command runs through Bash (Git Bash on Windows, native
bash elsewhere), never PowerShell. Resolve repository paths dynamically.

## Runtime resolution

Resolve `RUNTIME_ROOT` to the first available location:

1. `${GP_RUNTIME_ROOT}`, only when the harness explicitly provides it.
2. `${CLAUDE_PLUGIN_ROOT}/commands/{{PREFIX}}-runtime` for a plugin install.
3. `{{AGENT_DIR}}/commands/{{PREFIX}}-runtime` for a generated project.

If no candidate contains `manifest.tsv`, stop and report the missing runtime package. Never guess a
workflow from memory.

## Lazy-loading protocol

1. Parse the selector using the table below.
2. If no selector is present, infer it from the user's request: a whole new game
   selects --build, a bounded implementation selects --feature. Ask only when
   the intent remains ambiguous. Do not make the user learn selectors first.
3. Read exactly one `<mode>.md` from `RUNTIME_ROOT`.
4. Parse its first `<!-- gp-runtime-contracts: ... -->` line and read exactly those
   `contract-<name>.md` files, once each.
5. Execute `contract-startup.md` first, then the selected runbook.

## Mode dispatch

| Selector | Runbook | What it does |
|---|---|---|
| `--build` | `build.md` | complete a game brief through staged design, assets, code and delivery |
| `--discuss` | `discuss.md` | read-only brainstorm, no writes |
| `--style` | `style.md` | build the style bible, assemble the reference sheet, STYLE LOCK |
| `--design` | `design.md` | mechanics, core loop, feel, content data |
| `--level` | `level.md` | maps, paths, wave tables |
| `--art` | `art.md` | one ART card end to end: prompt-spec, generate, validate, review, integrate |
| `--animate` | `animate.md` | rig + AnimationPlayer tracks + procedural juice |
| `--feature` | `feature.md` | SPEC to shipped: develop, review, test, gates, verify, docs |
| `--balance` | `balance.md` | tune content numbers against the balance gate |
| `--gates` | `gates.md` | run every applicable gate and report |
| `--adopt` | `work.md` | map an existing project's architecture and real checks |
| `--doctor` | `work.md` | inspect required tools and qualification gaps |
| `--status` | `work.md` | report the shared board, readiness and inconsistencies |
| `--resume` | `work.md` | resume a saved run, checking stale evidence |
| `--metrics` | `work.md` | observed model usage, retries and unknowns |

Unknown or conflicting selectors are an error: show this table and ask the user to choose one.

## Modifiers

- `--next` — with `--feature` or `--art`, take the top item from the corresponding board instead of
  a free-text description.
- `--chain` — Codex only, and only with `--feature --next`: after a verified DONE,
  create one fresh Codex task in the same saved project with the same command.
  Stop on an empty/not-ready board, REVIEW/BLOCKED/FAILED result, a human gate
  or unavailable task creation. Never fork or reuse the current transcript.
- `--spec ID`, `--track NAME` — select a ready SPEC or track in SPECS/.
- `--preview` — show selection, prerequisites, proposed files, model routing and checks before writes.
- `--light` — with `--feature`, a cost-aware execution shape for both tools: one expert-tier
  developer owns implementation, its focused tests and up to one repair pass (no separate
  tester/architect assignment), then one simple-tier closer completes reviewer and verifier
  sequentially. Claim with `work.sh claim --profile light`; the recorded profile is immutable
  for that run. Mandatory final gates, manual evidence, acceptance mapping and ART dependencies
  are unchanged. Blender, replay-codec, concurrency, critical-lifecycle and data-loss risks
  require the standard profile. Incompatible with `--batch`.
- `--batch N` — explicitly authorized bounded sequence; default is one SPEC.
- `--unattended` — declares nobody is watching. Advisory gates proceed on their recommended default
  and are listed in a "decisions taken while unattended" summary. Existing scope
  approval persists. Unapproved STYLE LOCK, material scope changes and outward
  actions still require the corresponding authorization from contract-startup.md.

## Non-negotiables in every mode

<!-- engine:2d -->
- **The layer contract.** `sim/` is deterministic and engine-free; `render/` and `ui/` read
  simulation state and never write it; `content/` is data. A change that needs an exception raises
  it with the user instead of taking one.
<!-- /engine:2d -->
<!-- engine:3d -->
- **The layer contract.** `domain/` is deterministic and engine-free; `world/`
  owns physics/navigation. Human and bot input share production code. Read
  {{ROOT_DOC}} and contract-3d.md. Pure replay does not prove physics determinism.
<!-- /engine:3d -->
- **No art before STYLE LOCK.** Production assets are not generated until the reference sheet is
  approved and frozen.
- **Provenance travels with every generated asset.** No exceptions for images produced inside an
  agent session — the agent writes the record itself.
- **Gates report, agents do not.** A pass claimed without the gate's JSON line is not a pass.
- **Reviewers warn, they never fix.**
- **Use the project model policy.** Codex routes bounded assignments to Luna xhigh,
  Sol xhigh or Astra high; Claude Code to Sonnet 5 medium, Sonnet 5 xhigh or Opus 5
  xhigh (effort pinned per role agent). Actual spawn settings must match the
  assignment; report unavailable models. Keep image/audio providers explicit. Load
  contract-work for delegation and boards.

Directory names in the default layer examples are mapped through
pipeline/project.json for existing projects. Keep the engine-free deterministic
logical domain contract intact regardless of its directory name. Preserve the
project's explicit use-case, repository, mapper and composition boundaries.
