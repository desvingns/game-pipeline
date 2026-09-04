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

## Flags

| Flag | Default | What it does |
|---|---|---|
| `--prefix=` | *asked* | Command name. `--prefix=td` gives you `/td`. Lowercase, up to 8 chars. |
| `--project-name=` | *asked* | Human name of the game. |
| `--package=` | *asked* | Android package id. |
| `--project-description=` | placeholder | One sentence. |
| `--engine=` | `godot` | Only `godot` is implemented. |
| `--tool=` | `claude` | `claude` writes `.claude/`, `codex` writes `.codex/`. |
| `--style-profile=` | `cel-shaded-outline` | Which style profile is frozen into the project. |
| `--projection=` | `top-down-34` | `top-down-34` or `iso-2to1`. Drives art cost. |
| `--ui-lang=` | `en` | Language of user-facing strings and manual check lists. |
| `--memory-path=` | derived | Where cross-session memory lives. |
| `--dry-run` | off | Print what would be created and exit. |
| `--force` | off | Overwrite an existing pipeline. |
| `--skip-memory` | off | Do not write memory files. |
| `--non-interactive` | off | Fail instead of prompting for missing values. |
| `--no-git` | off | Suppress the not-a-git-repo warning. |

## Choosing the projection deliberately

`--projection` is not cosmetic. `top-down-34` needs two drawn facings per animated
unit; `iso-2to1` needs four plus mirrors, and every one of them must be animated
separately. That is a 4x multiplier on the art backlog, applied by the planner
from the moment you bootstrap. Pick `iso-2to1` because the game needs depth, not
because it sounds nicer.

## What you get

```
.claude/agents/            14 specialists
.claude/commands/td.md     the orchestrator, plus td-runtime/ runbooks
.claude/scripts/           gate scripts (bash interface, python where pixels are involved)
.claude/specs/             code board: backlog / active / done
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

Model choice is a cost decision, not a quality-only one. The flash tier is the
default because an asset is normally generated two or three times before it is
accepted, and paying pro-tier prices for attempt one is waste. Switch to
`gemini-3-pro-image` for tier-A key art, where a handful of assets carry the
whole visual identity.

A `429` from the image API means quota, not a misconfiguration — the gate reports
it as `generation_failed` with the API's own message, so the difference is visible
rather than guessed at.

Missing tools are not fatal at bootstrap. The gates report `error_kind`
(`godot_not_found`, `python_missing`) so a missing dependency never masquerades as
a broken game.

## Verifying a change to the templates

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
