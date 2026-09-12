# USAGE — bootstrapping a game pipeline

`bootstrap.sh` renders the templates into **the current directory**. Run it from
inside the game repository you want to equip, not from inside `game-pipeline`.

```bash
cd /path/to/my-game
/path/to/game-pipeline/bootstrap.sh \
  --prefix=td \
  --project-name="Signal Defense" \
  --project-description="A 2D tower defense about holding a relay station." \
  --package=com.example.signaldefense
```

## Windows 3D FPS

```bash
bash /path/to/game-pipeline/bootstrap.sh --preset=3d-fps-windows \
  --tool=codex --prefix=fp --project-name="My FPS" \
  --genre=arena --network=offline --non-interactive
```

Then invoke `$fp --build <brief>`. No Android package is needed. See
[3D-WINDOWS.md](3D-WINDOWS.md) for Blender specs, harness APIs and delivery checks.
Python 3 is required by bootstrap; mesh/gate validation uses its standard library.

## Flags

| Flag | Default | What it does |
|---|---|---|
| `--prefix=` | *asked* | Command name. `--prefix=td` gives you `/td`. Lowercase, up to 8 chars. |
| `--project-name=` | *asked* | Human name of the game. |
| `--package=` | *asked for Android* | Android package id; unnecessary for Windows. |
| `--preset=` | `2d-android` | `2d-android` or `3d-fps-windows`. |
| `--genre=` | preset default | 3D: `arena`, `tactical`, `horde`. |
| `--network=` | `offline` | 3D: `offline`, `coop`, `competitive`. |
| `--project-description=` | placeholder | One sentence. |
| `--engine=` | `godot` | Only `godot` is implemented. |
| `--tool=` | `claude` | Codex creates `.codex/`, `.agents/skills/<prefix>/`, `AGENTS.md` and a thin Claude import. Claude creates `.claude/` and `CLAUDE.md`. |
| `--style-profile=` | preset default | 2D: raster catalogue; 3D: `stylized-3d`. Frozen in the project. |
| `--projection=` | preset default | 2D: `top-down-34` or `iso-2to1`; 3D: `perspective-fps`. |
| `--ui-lang=` | `en` | Language of user-facing strings and manual check lists. |
| `--memory-path=` | derived | Codex defaults to the game's `.ai/memory`; Claude uses its project memory directory. |
| `--dry-run` | off | Print what would be created and exit. |
| `--force` | off | Upgrade generated runtime files, archiving previous versions. Preserve custom root instructions, project state, boards, frozen art and memory. |
| `--skip-memory` | off | Do not write memory files. |
| `--non-interactive` | off | Fail instead of prompting for missing values. |
| `--no-git` | off | Suppress the not-a-git-repo warning. |

## Choosing the projection deliberately

`--projection` is not cosmetic. `top-down-34` needs two drawn facings per animated
unit; `iso-2to1` needs four plus mirrors, and every one of them must be animated
separately. That is a 4x multiplier on the art backlog, applied by the planner
from the moment you bootstrap. Pick `iso-2to1` because the game needs depth, not
because it sounds nicer.

## Codex Desktop and CLI

### Marketplace installation

The recommended shared installation is the `game-pipeline` marketplace. It
provides the same `gp-dev` entry point across Codex and Claude Code and keeps a
bundled generator copy in the plugin package:

```bash
# Codex
codex plugin marketplace add /d/Pet/game-pipeline
codex plugin add gp-dev@game-pipeline

# Claude Code
claude plugin marketplace add D:/Pet/game-pipeline
claude plugin install gp-dev@game-pipeline
```

Use `https://github.com/desvingns/game-pipeline.git` instead of the local path
for a git marketplace. Reopen the tool session after installing. In Claude use
`/gp`; in Codex use `$gp-dev` for bootstrap and the generated `$<prefix>` skill
for project work. See [MARKETPLACE.md](MARKETPLACE.md) for the source layout,
refresh and validation commands.

### Standalone Codex entry point

From the generator, run `bash install-codex.sh`. This installs the personal
`$gp-dev` entry point under `${CODEX_HOME:-$HOME/.codex}/skills/gp-dev/` and records
the generator's absolute location. `--skills-dir=/path/to/skills` overrides that
destination. Reinstall after moving the generator or updating the personal adapter.
Previous personal adapters are copied into the sibling `archive/` directory.

Example request in Codex:

```text
$gp-dev install this pipeline into D:/Pet/my-game with prefix td,
project name Signal Defense and package com.example.signaldefense
```

Generated games expose `$td --gates`, `$td --style`, `$td --feature --next` and the
other selectors. Prefix underscores become hyphens in the skill name only; script
and board paths retain the original prefix. Skills normally refresh automatically;
reopen the project/session if the selector does not show the new skill.

Native Codex agent TOML files declare role defaults; per-assignment routing uses
pipeline/model-policy.json (Luna xhigh / Sol xhigh / Astra high). Claude Code
selects its native models independently. Both adapters use the rendered Markdown
role bodies. A harness without named-agent support can dispatch the same
body through its available collaboration tool. Workflows requiring independent
review report a limitation when delegation is unavailable. This installer does
not change global models, permissions, trust or feature flags.

The `codex-native` shell adapter renders a provider-neutral prompt. The host agent
uses its available image tool, then `--register <returned-path> --attempt <n>` writes
provenance. If no native image tool is available, the external-file path remains
available. STYLE LOCK still requires explicit human approval.

Run `--force` only for an intended upgrade. Each run retains staging plus copies
of replaced files under `archive/gp-bootstrap/`. It does not render or rewrite
unrelated existing agent files. Custom `AGENTS.md`/`CLAUDE.md` are preserved; the
generated instructions remain in the reported archive path for manual merging.
Frozen style profiles and schemas are preserved and need a deliberate migration
when a later release changes their contracts.

Official references: [skill discovery](https://learn.chatgpt.com/docs/build-skills)
and [native subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## What you get

```
.claude/agents/            15 specialists
.claude/commands/td.md     the orchestrator, plus td-runtime/ runbooks
.claude/scripts/           gate scripts (bash interface, python where pixels are involved)
SPECS/                    shared code board: backlog / done (status in card)
art/cards/                 art board: backlog / active / done
art/style/profiles/        the frozen style + projection profiles
art/schemas/               prompt-spec and provenance contracts
art/style/reference/       where the locked reference sheet goes
art/prompts/               generated prompt-specs
assets/inbox/              raw generated images awaiting validation
CLAUDE.md STATE.md ROADMAP.md DOCUMENTATION.md
```

## After bootstrap

1. Put a Godot 4 project under `game/` (with `project.godot`).
2. `/td --style` — build the style bible and lock the reference sheet. Do this
   first: everything visual is downstream of it, and art or scenes made before
   STYLE LOCK have to be redone.
3. `/td --design <the core loop>`.

## Environment

| Variable | Purpose |
|---|---|
| `GODOT_BIN` | Pin the Godot executable. Prefer a console/headless build on Windows. |
| `GP_PYTHON` | Pin the interpreter used for image analysis. It must have Pillow. |
| `GEMINI_API_KEY` | Enables scripted image generation in a Claude session. |
| `GP_GEMINI_IMAGE_MODEL` | Override the image model. Default `gemini-3.1-flash-image`. |
| `GP_ART_PROVIDER` | Override the provider: `gemini`, `codex-native`, `manual`. |
| `GP_PROJECT_DIR` | Where the Godot project lives. Default `game`. |
| `GP_SHOT_RENDERER` | Screenshot renderer. Default `gl_compatibility`; requires a real or virtual display. |

Model choice is a cost decision, not a quality-only one. The flash tier is the
default because an asset is normally generated two or three times before it is
accepted, and paying pro-tier prices for attempt one is waste. Switch to
`gemini-3-pro-image` for tier-A key art, where a handful of assets carry the
whole visual identity.

A `429` from the image API means quota, not a misconfiguration — the gate reports
it as `generation_failed` with the API's own message, so the difference is visible
rather than guessed at.

Godot and Blender need not exist at bootstrap; Python 3 is required to read
the preset catalogue. Runtime gates report `error_kind`
(`godot_not_found`, `python_missing`) so a missing dependency never masquerades as
a broken game.

The 2D build gate requires a gdUnit4 test harness; its absence reports
`test_harness_missing`. Simulation validates the harness JSON with standard-library
Python and requires at least two replay runs. Screenshots and exports archive an
existing output before attempting capture/build, so stale files cannot pass.
Screenshot capture deliberately does not use `--headless`: Godot disables
rendering in that mode. A rendering-capable runner is required for the visual gate.
See [RenderingServer](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html).

## Verifying a change to the templates

Run `bash tests/smoke.sh` for the regression suite (Python 3.11+ and Pillow).
It renders both tools into directories containing spaces, checks native adapters,
upgrade preservation, error JSON, fake-engine failure cases and the art contract.
Fixtures and logs remain under `out/regression-*/`; no network or real engine is
used. This proves generator/gate behavior, not a real Godot export or image model.

The 3D groups also cover selective composition, configuration migration refusal,
binary GLB inspection, fresh peer receipts and process deadlines. Optional
`python tests/test_fps_integration.py` uses real GODOT_BIN/BLENDER_BIN executables
and installed export templates, preserves evidence, and opens rendering windows.
See [validation evidence and limits](VALIDATION-0.3.md).

```bash
bash -n bootstrap.sh && bash -n lib/*.sh
python -m json.tool profiles/style/cel-shaded-outline.json > /dev/null

mkdir -p /tmp/gp-smoke && cd /tmp/gp-smoke
/path/to/game-pipeline/bootstrap.sh --prefix=td --project-name=Smoke \
  --package=com.smoke.td --non-interactive --skip-memory --no-git
grep -rn '{{\|<!-- engine:\|<!-- tool:\|<!-- if ' .claude art || echo "clean"
```

The final grep must print `clean`. A leaked marker means a template authored two
inline conditional blocks on one line, which the greedy inline `sed` pass merges.

## Existing projects, shared backlog and model routing (v1)

See [WORKFLOW.md](WORKFLOW.md) for the full execution contract, schemas and command
examples. Use --adopt to preserve and connect an existing project; preview with
--dry-run. Add --blender-assets to enable Blender assets independently of 2D/3D.
All code tasks live in SPECS/. An absent board is discovered/migrated by a simple
subagent (Codex Luna xhigh; Claude native choice); an empty backlog is reported.

The recommended Codex chat orchestrator is GPT-5.6 Sol with high reasoning.
Specialists use explicit project policy, while Claude maintains its own current
models under claude.tiers. --status, --doctor, --resume, --metrics, --spec ID and
--track NAME support existing backlog work. One SPEC per run remains the default.
