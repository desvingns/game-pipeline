# Changelog

All notable changes to game-pipeline. SemVer: PATCH = wording, MINOR = additive
(new agents, new profiles, new optional sections), MAJOR = renames or JSON-shape
changes.

## [0.1.0] — 2026-09-04

First working skeleton. Structurally mirrors `claude-mobile-pipeline`; the domain
layer is new.

### Added

- `bootstrap.sh` — copy, render, strip conditionals, rename, memory, version
  stamp. Flags for engine, harness, style profile, projection, UI language.
- `lib/render.sh` — vendored from cmp with the platform axis replaced by an
  `engine:` axis; `tool:` and `if` axes unchanged.
- `lib/detect.sh` — Godot 4 and Pillow-capable Python detection.
- **Style profile catalogue** — `cel-shaded-outline`, `flat-vector`, `pixel-art`,
  `painterly`. Each pairs a prompt skeleton with machine-checkable rules, because
  the asset gate is a function of the style.
- **Projection profiles** — `top-down-34` (default) and `iso-2to1`, each carrying
  the art-backlog multiplier the planner must apply.
- **Schemas** — `prompt-spec` (provider-neutral, field vocabulary aligned with
  Codex Desktop's `image_gen` so rendering to it is lossless) and `provenance`.
- **Art subsystem** — `art-gen` provider adapter (`gemini`, `codex-native`,
  `manual`), a real Pillow-based asset validator, and `style-lock` for freezing
  and verifying the reference sheet.
- **Godot gates** — build/test/export, replay determinism, balance corridor,
  headless screenshots.
- **14 agents** — architect, game-designer, level-designer, economy, docs;
  art-director, art-prompter, asset-integrator; developer, animator, tester,
  runner, reviewer, verifier.
- **Orchestrator** `/{{PREFIX}}` with nine lazily-loaded runbooks and two shared
  contracts (`startup`, `art`).
- Root doc templates, three memory memos, both boards, `docs/DESIGN.md`.

### Known gaps

- No audio profile or gate.
- No on-device performance gate (needs a connected device).
- No playtest agent, no `vfx`/`ui` specialists, no knowledge/improve loop.
- No `--bench` mode for model comparison.
- Codex `.codex/` adapters are not emitted; `--tool=codex` only changes
  `AGENT_DIR`.
- The `unity` engine axis exists in the render engine but has no templates.
