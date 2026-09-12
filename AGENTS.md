# AGENTS.md — working on `game-pipeline`

Canonical instructions for any AI tool working **on this repository**. Read by Codex CLI natively;
imported by `CLAUDE.md` for Claude Code via `@AGENTS.md`. Single source of truth — do not duplicate
these rules elsewhere.

## What this repo is

`game-pipeline` (gp) is a **generator**, not a game. `bootstrap.sh` renders the `templates/` tree
plus a user-chosen `PREFIX` into a ready-to-use agent pipeline for one **game repository**:
2D/Android or 3D FPS/Windows (Godot 4; Blender for 3D). Specialist agents, an orchestrator, gate scripts, an art
subsystem, and cross-session memory. The thing edited here is the *template system*.

Sibling generator: [`claude-mobile-pipeline`](https://github.com/desvingns/mobile-pipeline) (cmp),
which does the same for mobile **applications**. gp vendored cmp's framework (`lib/render.sh`, the bootstrap skeleton,
the `.ai/` protocol, the spec board, the change-log + cursor) and then diverged. Port *semantics*
between them, never syntax. Design rationale: `docs/DESIGN.md`.

## Golden rules (invariants — do not break)

1. **Cross-platform Bash for every shell script.** Linux, macOS, Windows Git Bash. Never PowerShell.
   Shebang `#!/usr/bin/env bash`.
2. **Never `sed -i`.** GNU and BSD `sed` differ. Write to a temp file and `mv` (see `lib/render.sh`).
3. **Bash is the interface, Python may be the implementation.** Image analysis cannot be done in
   bash. A gate that needs pixels is a thin bash wrapper emitting exactly one JSON line over a
   Python + Pillow implementation, and it degrades to a structured `"error_kind"` result when
   Python or Pillow is missing — never to a silent pass. No `jq` dependency anywhere.
4. **Markdown-first.** Agents, memory, handoff, style bibles and the change-log are plain markdown
   or plain JSON so any tool can read them without a custom parser.
5. **Placeholders.** `{{KEY}}` in file *content* and `{{PREFIX}}` in file *names* are substituted by
   `bootstrap.sh`. Content renders before filenames are renamed. New placeholders must be added to
   the vars file in `bootstrap.sh`.
6. **Conditional blocks.** `<!-- engine:X -->…<!-- /engine:X -->`, `<!-- tool:X -->…<!-- /tool:X -->`
   and `<!-- if COND -->…<!-- /if -->` are trimmed by `lib/render.sh`. Author **at most one inline
   block per line** — the inline `sed` pass is greedy.
7. **Memory is append-only.** Generated memory files are never overwritten by bootstrap.
8. **Structured payloads.** Pipeline agents return exactly one structured payload (JSON or a named
   block) with no prose around it. Deterministic scripts emit exactly one JSON line.
9. **SemVer.** PATCH = wording/typos; MINOR = new agents or optional sections (additive); MAJOR =
   renames or JSON-shape changes. Bump `VERSION` + `CHANGELOG.md` for any release.

## Domain rules specific to games (do not soften)

- **The architecture contract is selected by dimension.** In 2D, simulation remains engine-free
  and deterministic. Game logic runs in logical coordinates, knows
  nothing about pixels, projection, or nodes, and replays identically from a seed. Rendering is a
  separate layer. In 3D, `domain/` contains the same pure seeded rules; `world/` owns Godot physics,
  collision and navigation; human and bot input share production commands. The replay gate covers
  pure rules only. Engine physics requires scenario assertions with agreed tolerances, not an
  unsupported promise of bit-identical replay. Do not move physics into domain/ or weaken 2D rules.
- **The asset gate is a function of the style.** Style is never free-form prose. gp ships a
  catalogue of **style profiles** under `profiles/style/` (prompt skeleton + machine rules); a game
  spec *instantiates* a profile, never invents one. Adding a new style means adding its validation
  rules too.
- **Projection is a profile** (`profiles/projection/`). For 2D it determines facings and art-card
  multipliers. For 3D it defines metric axes and camera requirements; count meshes, rigs and clips.
- **Provenance is mandatory.** Every generated image carries a provenance record (prompt-spec hash,
  provider, model, params, timestamp, reference-sheet hash). Missing provenance fails the asset
  gate exactly like a broken alpha channel. When an image is produced inside an agent session
  rather than by a script, the *agent* writes the record.
- **STYLE LOCK is a hard human gate.** No art card enters production before the reference sheet is
  approved and frozen.
- **3D provenance binds exact bytes.** Preserve Blender recipes, declared dependencies, frozen
  mesh specs, tool versions, profile/reference hashes and output digests in `art/builds/` plus a
  sibling provenance record. Machine checks do not replace visual/animation/collision review.
- **Selected context only.** Compose dimension/platform/art/genre/network modules at bootstrap;
  do not burden generated games with unrelated instructions. All projects share SPECS/.
  Codex dispatch uses the project model policy (Luna xhigh / Sol xhigh / Astra high).
  Claude Code uses its own entries (Sonnet 5 medium / Sonnet 5 xhigh / Opus 5 xhigh);
  its effort is pinned per role agent frontmatter because a spawn cannot set it.
- **One production workflow.** `--build` completes one approved game brief. Do not add a mandatory
  second baseline implementation, paired-run protocol or model benchmark system.

## Repository map

```
bootstrap.sh              # entry point: parse args -> copy -> render -> strip -> rename -> memory -> stamp
lib/build-marketplace.sh  # emits the Claude Code and Codex marketplace adapters
lib/claude.sh             # Claude adapter: model/effort/maxTurns frontmatter, project permissions
lib/codex.sh              # Codex adapter: native TOML role definitions
lib/detect.sh             # OS / git / godot / python detection, path sanitising
lib/prompts.sh            # interactive prompt helpers
lib/render.sh             # placeholder replacement + conditional-block trimming (the render engine)
profiles/style/*.json     # style profiles: prompt skeleton + machine-checkable rules
profiles/projection/*.json# projection profiles: facings, sorting, art-card multipliers
schemas/*.schema.json     # prompt-spec and provenance contracts
templates/common/         # engine-neutral: design agents, orchestrator, memory, root docs, spec board
templates/godot/          # Godot 4 specialists + gate scripts + memory
templates/dimensions/3d/  # FPS role/runtime overrides, Blender and actual Godot harness templates
profiles/presets/         # supported dimension/platform/art combinations
profiles/genres/          # arena, tactical, horde (only selected text is installed)
profiles/network/         # offline, coop, competitive (only selected text is installed)
profiles/qa/              # FPS behavioral checks and rendered performance limits
.claude-plugin/           # Claude Code marketplace catalog
.agents/plugins/          # Codex marketplace catalog
claude-plugins/            # generated Claude Code plugin tree
codex-plugins/             # generated Codex plugin tree
templates/art/            # art subsystem: agents, generation adapters, validator, profiles
docs/                     # DESIGN (rationale), USAGE, ARCHITECTURE, ART-PIPELINE
.ai/                      # shared cross-tool workspace (memory / handoff / tasks / changes)
AGENTS.md / CLAUDE.md     # this file (canonical) + thin Claude import
```

## Dual-tool model

gp is driven by **both Claude Code and Codex CLI**. Pattern: one canonical source + thin per-tool
adapters. Agent prose stays tool-neutral; genuinely tool-specific lines are isolated behind
`<!-- tool:claude -->` / `<!-- tool:codex -->`. `{{AGENT_DIR}}` resolves to `.claude` or `.codex`.

The art channel is where the two tools genuinely differ, and it is handled by the provider adapter,
not by the agents:

| Session | Provider | Mode |
|---|---|---|
| Claude Code | `gemini` (Nano Banana family) | scripted, `GEMINI_API_KEY` |
| Codex Desktop | `codex-native` (`image_gen`) | agent invokes the available native tool and registers the returned path; external-file fallback when unavailable |
| any | `manual` | any web tool; the file is dropped into `assets/inbox/` |

Every provider consumes the same provider-neutral `prompt-spec.json` and must produce the same
provenance record. Swapping a model touches one script.

## How to work & verify

- Trace a change end-to-end through `bootstrap.sh` (copy -> render -> strip -> rename) before
  editing.
- **Dry run:** `./bootstrap.sh --dry-run --prefix=td --project-name=Demo --package=com.demo.td`
- **Lint:** `bash -n <script>` clean for any touched `.sh`; `python -m py_compile` for any `.py`.
- **Smoke test:** bootstrap into a throwaway dir, then grep the output for leaked
  `<!-- engine:* -->`, `<!-- tool:* -->`, `<!-- if * -->` or `{{...}}` markers.
- Style and projection profiles must stay valid JSON: `python -m json.tool <file>`.
- `bash tests/smoke.sh` covers both tools/presets and invalid/stale evidence. Optional real-tool
  integration uses `python tests/test_fps_integration.py` with GODOT_BIN and BLENDER_BIN.
