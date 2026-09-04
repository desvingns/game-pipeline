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

Unknown or conflicting selectors are an error: show this table and ask the user to choose one.

## Modifiers

- `--next` — with `--feature` or `--art`, take the top item from the corresponding board instead of
  a free-text description.
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
- **Roles inherit the session model.** Do not switch models between production
  roles without the user's request. Keep image/audio providers explicit.
