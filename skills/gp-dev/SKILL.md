---
name: gp-dev
description: Install or run game-pipeline for Godot 2D Android games or Blender-based 3D Windows shooters when the user invokes $gp-dev, /gp, or asks to make a game through this pipeline. Use project-local workflows after installation.
---

This is the reusable entry point for the game-pipeline generator. It is not a
game or a game engine. Read `generator-root.txt` beside this skill to locate the
installed generator; if unavailable, use the current repository only when it
contains `bootstrap.sh` and `templates/common/commands/`.

If the current repository has `.codex/.gp-version`, read its `prefix`, then
`.codex/commands/<prefix>.md` and only the requested runbook and contracts. Use
the project's `.agents/skills/<prefix-with-underscores-replaced-by-hyphens>/SKILL.md`
for Codex delegation and image-generation instructions. Preserve all supplied
selectors and modifiers. Read project memory, never another game's memory.

For installation into a game repository, read the generator's `docs/USAGE.md`.
Use Bash to run its absolute `bootstrap.sh` path from the target game directory
with `--tool=codex --non-interactive` and the user's prefix, project name and
selected preset. Infer --preset=3d-fps-windows for a Windows 3D shooter using
Blender; use --genre=arena|tactical|horde from the brief and --network=offline
unless actual multiplayer is requested (coop|competitive). The default
2d-android preset requires an Android package id; Windows does not.
Ask only for required values or the target directory that
cannot be inferred from the request. Do not bootstrap into the generator itself.
Preview with `--dry-run` first. Use `--force` only for an explicitly requested
upgrade; it archives replaced pipeline files and preserves state, boards and art.

After installing, verify that `AGENTS.md`, the project skill, runtime manifest,
native role adapters and gate scripts exist. Invoke the build and style-lock
checks and report their JSON truthfully. Missing Godot, game project, test addon,
reference sheet or simulation harness is a readiness gap, not a successful gate.
Tell the user the exact project skill invocation. Codex normally discovers new
skills automatically; if absent from the selector, reopen the project/session.

When working on the generator itself, follow its `AGENTS.md` and `.ai/` protocol.
Change templates and validate generated output for both tools. Never apply a
game's feature/design runbook to the generator repository.

For a whole-game request, bootstrap if needed and continue with the project's
--build workflow; installation alone does not satisfy a request to make a game.
Honor existing scope approval, preserve the human STYLE LOCK gate, and use the project model policy for each bounded assignment. Do not create a second baseline game or require
a paired experiment. Existing builds can be compared manually by the user.

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
