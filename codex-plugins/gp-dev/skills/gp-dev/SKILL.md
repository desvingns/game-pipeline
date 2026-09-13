---
name: gp-dev
description: Install or run game-pipeline for Godot 2D Android games or Blender-based 3D Windows shooters. Use for $gp-dev, /gp, or any request to build a game through this pipeline.
---

# Game Pipeline marketplace bridge

Use this skill when the user asks to create, extend, test or review a Godot game
through the Game Pipeline. The pipeline supports the `2d-android` and
`3d-fps-windows` presets; the latter uses Blender for reproducible 3D assets and
Godot for the Windows game and harness.

## Resolve the generator

1. If the current repository contains `bootstrap.sh` and `templates/common/`,
   treat it as the generator only when the user explicitly asks to work on the
   generator. Never bootstrap a game into that repository.
2. For a new game, resolve the packaged `scripts/gp-bootstrap.sh` first. In the
   Claude plugin its path is `${CLAUDE_PLUGIN_ROOT}/scripts/gp-bootstrap.sh`.
   In Codex, use the same script from the installed `gp-dev` plugin directory.
3. A standalone install may instead provide `generator-root.txt` beside this
   skill; read it and use the recorded absolute generator path.
4. `GP_GENERATOR_ROOT` is an explicit fallback. A missing generator is a
   readiness problem; do not claim that bootstrap or a gate succeeded.

## Install a project pipeline

Read the generator's `docs/USAGE.md`. Preview first with `--dry-run`, then run
the absolute `bootstrap.sh` path from the target game directory with
`--tool=claude` or `--tool=codex`, the user's prefix and project name.

- Infer `--preset=3d-fps-windows` for a Windows 3D shooter using Blender.
- Use `--genre=arena|tactical|horde` when the brief supports it.
- Use `--network=offline` unless actual multiplayer is requested; then choose
  `coop` or `competitive`.
- The default `2d-android` preset requires an Android package id. Windows does
  not.
- Use `--force` only for an explicitly requested upgrade; the generator archives
  replaced files and preserves state, boards, style lock and memory.

After bootstrap, verify the root instructions, project skill, runtime manifest,
native role adapters and gate scripts. Read only the generated project's
selected runbook and contracts. A missing Godot, Blender, game project, test
addon, reference sheet or harness is reported as a readiness gap, never as a
passing gate.

## Run an existing project

Read the generated `.gp-version`, root instructions and project memory. In
Claude use `/gp`; in Codex use the generated `$<prefix>` skill for project work
and `$gp-dev` for generator/bootstrap routing. Preserve all selectors and
modifiers. Continue a whole-game request through `--build` until the approved
brief is delivered.

The production workflow is single-track: do not create a second baseline game,
paired experiment or model benchmark. Existing non-pipeline builds may be
compared manually by the user.

## Shared backlog execution and existing projects

For an existing game use bootstrap --adopt (preview with --dry-run), preserving
its source, architecture, tests, documents and custom configurations. Read the
project's contract-work.md and pipeline/project.json. All projects and both tools
use SPECS/. If absent, dispatch the backlog-discovery specialist before creating
it: Codex gpt-5.6-luna / xhigh; Claude Code its simple tier (Sonnet 5 / medium).
Migrate actual tasks with their text, IDs, evidence and links; report an empty
backlog explicitly. Never fabricate tasks or silently create a competing board.

Use --feature --next, --spec ID, --track NAME, --preview, --resume RUN, --status,
--doctor and --metrics as applicable. One task per run unless explicitly authorized
otherwise. Delegate bounded tasks using pipeline/model-policy.json: Codex Luna xhigh,
Sol xhigh, Astra high by difficulty; Claude Code Sonnet 5 medium, Sonnet 5 xhigh,
Opus 5 xhigh (claude.tiers; effort pinned per role agent via claude.role_tiers). Keep
the primary chat model unchanged; recommended Codex orchestrator is Sol high. Use the
shared script for claims, ownership, checkpoints, actual gate evidence and close-out.
`--feature --light` (both tools) is a cost-aware profile: one expert-tier developer
owns implementation/tests/repairs, one simple-tier closer runs reviewer then verifier;
claim with `--profile light`; forbidden for Blender/critical-lifecycle/concurrency/
replay-codec/data-loss risk and incompatible with --batch. See docs/WORKFLOW.md in
the generator.


## Codex chain mode

`--chain` is valid only with `--feature --next --chain`. It runs one SPEC per
fresh Codex task: complete and close the current SPEC as DONE with fresh evidence,
then inspect `work.sh status`. Stop on an empty or not-ready board, REVIEW,
BLOCKED, FAILED, a human gate, or missing evidence.

When another task is ready, use the native Codex app `list_projects` to resolve
the current saved project, then `create_thread` with `environment: {type: "local"}`
and the prompt `Run gp --feature --next --chain in the current project.` Pass only
the chain id and iteration metadata; omit model/reasoning overrides. This must be
a new task with an empty transcript. Never use `fork_thread` or
`send_message_to_thread`, and never use a CLI bridge. Create at most one successor
for each completed run. If task creation or project mapping is unavailable,
return `chain_unavailable` and stop in the current session.
