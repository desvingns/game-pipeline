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
Honor existing scope approval, preserve the human STYLE LOCK gate, and inherit
the session model for all roles. Do not create a second baseline game or require
a paired experiment. Existing builds can be compared manually by the user.
