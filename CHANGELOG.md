# Changelog

All notable changes to game-pipeline. SemVer: PATCH = wording, MINOR = additive
(new agents, new profiles, new optional sections), MAJOR = renames or JSON-shape
changes.

## [0.4.0] — 2026-09-04

### Added

- A `game-pipeline` marketplace catalog for Claude Code and Codex with the
  `gp-dev` plugin, following the dual-harness layout used by
  `mobile-pipeline`.
- Reproducible `lib/build-marketplace.sh` generation for both plugin trees,
  dimension-specific runtime fallbacks, plugin manifests and a bundled
  generator/bootstrap wrapper.
- Marketplace installation documentation and regression checks for manifest
  validity, runtime selection, placeholder rendering and generator parity.

### Changed

- The Game Pipeline front door is available as `/gp` in Claude Code and
  `$gp-dev` in Codex. Generated game projects still select their own prefix and
  dimension-specific roles after bootstrap.

## [0.3.0] — 2026-09-04

### Added

- Selectively composed `2d-android` and `3d-fps-windows` presets; Windows does not
  require an Android package. Arena/tactical/horde and offline/co-op/competitive
  modules load only the selected context. Python 3 reads the preset catalogue.
- A whole-game `--build` workflow, staged SPEC/ART boards and scope-aware approval
  reuse. STYLE LOCK remains an explicit human approval of actual references.
- 3D-specific roles, architecture, memory and root documentation. Pure domain
  replay stays distinct from Godot physics/navigation scenario checks.
- Reproducible Blender recipes, GLB/blend/previews, metric/bone/material/texture/
  geometry/animation checks, byte-bound provenance and generated-image registration.
- Bounded Godot/Blender processes, tool version pins, real unit/replay/scenario
  hosts, fresh rendered screenshots/frame metrics, a Windows export preset and
  exported-main-scene smoke. Network scenarios require distinct fresh peer logs.
- Regression coverage across both tools/presets and optional real Godot/Blender
  integration fixtures with retained evidence. See `docs/VALIDATION-0.3.md`.

### Changed

- All role models inherit the session, including Claude roles; no silent stronger
  or cheaper model substitutions. Personal gp-dev recognizes Windows/Blender briefs
  and continues into game creation after installation.
- In-place preset/genre/network switches fail before writes to avoid mixing
  frozen art, instructions and append-only memory. Same-profile upgrades preserve
  user state and QA settings and archive replaced runtime files.
- No paired model experiment or mandatory second baseline implementation. The
  founding benchmark proposal is marked superseded by the user's chosen workflow.

## [0.2.0] — 2026-09-04

### Added

- Personal Codex entry point `$gp-dev` and repeatable `install-codex.sh`.
- Project skills, `AGENTS.md`, native TOML specialist adapters and tool-aware
  startup routing. Native image tools run in the host session with file registration.
- Regression coverage for both tools, update preservation, gate failures and art provenance.
- Standard-library validation for prompt specs, provenance and frozen reference hashes.

### Fixed

- Bootstrap validates non-interactive arguments, renders in isolation, archives
  replaced runtime files, preserves game state/art/custom instructions, and appends
  memory index entries. Placeholder rendering uses one sed pass per file.
- Gate error strings are JSON-escaped. Missing tests, insufficient replay runs,
  failed/malformed/partial simulation runs, stale screenshots/exports and empty shot
  lists cannot report success. Runtime logs are retained.
- Screenshot capture uses a rendering-capable display instead of Godot's
  rendering-disabled `--headless` mode.
- Locked palettes are mandatory, empty images fail, prompt-spec and reference
  hashes are verified, and edit requests include their source and edit goal.
- Art attempts retain previous outputs; Codex registrations identify their operator.

### Remaining scope

- A game still supplies its Godot project, gdUnit4 addon and simulation/capture
  harnesses. No real engine export or paid image generation is claimed by the tests.
- Advanced profile rules, Android device performance and a complete real-art
  vertical slice remain follow-up work; see `docs/REVIEW-2026-09-04.md`.

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
