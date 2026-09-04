# Agent / template change log

Append-only. Format: `.ai/changes/README.md`.

## 2026-09-04-initial-roster
- kind: agent
- target: templates/{common,art,godot}/agents/*.md
- change: create the initial 14-agent roster for v0.1.0
- why: founding brainstorm; the roster splits art into prompter / generator /
  validator / director / integrator so that "bad asset" and "broken asset" fail
  in different places
- breaking: no

## 2026-09-04-style-profiles
- kind: profile
- target: profiles/style/*.json, profiles/projection/*.json
- change: add four style profiles and two projection profiles, each pairing a
  prompt skeleton with machine-checkable rules
- why: the asset gate is a function of the style, so a style described as prose
  cannot be enforced; the projection multiplier must be known before the backlog
  is sized, not discovered during production
- breaking: no

## 2026-09-04-codex-deploy-01
- kind: script
- target: bootstrap.sh, lib/render.sh, lib/codex.sh
- change: Render in isolation, derive native adapters, preserve state and append memory; batch substitutions.
- why: Codex discovery and safe upgrades must be real behavior, not directory naming.
- breaking: no

## 2026-09-04-codex-deploy-02
- kind: script
- target: install-codex.sh
- change: Install the personal gp-dev skill and retain prior adapters.
- why: Make local Codex deployment repeatable without model or permission changes.
- breaking: no

## 2026-09-04-codex-deploy-03
- kind: agent
- target: skills/gp-dev/SKILL.md, templates/codex/SKILL.md.tmpl
- change: Add personal and per-game skill routing with capability-aware delegation.
- why: Expose discoverable Codex entry points backed by canonical role bodies.
- breaking: no

## 2026-09-04-codex-deploy-04
- kind: script
- target: templates/common/scripts/{{PREFIX}}-common.sh
- change: Share JSON escaping, native paths and dependency detection.
- why: Gate diagnostics must remain one JSON line on Windows and Unix.
- breaking: no

## 2026-09-04-codex-deploy-05
- kind: script
- target: templates/godot/scripts/{{PREFIX}}-runner-godot.sh
- change: Fail missing tests and archive stale exports; retain engine logs.
- why: A skipped test harness and a previous APK cannot prove a passing build.
- breaking: no

## 2026-09-04-codex-deploy-06
- kind: script
- target: templates/godot/scripts/{{PREFIX}}-sim-godot.sh
- change: Validate counters, process status and complete harness JSON for every run.
- why: Zero replays, malformed JSON and partial seed batches produced false confidence.
- breaking: no

## 2026-09-04-codex-deploy-07
- kind: script
- target: templates/godot/scripts/{{PREFIX}}-visual-godot.sh
- change: Require fresh captures and a nonempty shot list; use a rendering-capable display.
- why: Old files and headless dummy rendering cannot establish a new screenshot.
- breaking: no

## 2026-09-04-codex-deploy-08
- kind: script
- target: templates/art/scripts/{{PREFIX}}-art-gen.sh, templates/art/scripts/{{PREFIX}}-asset-validate.sh, templates/art/scripts/{{PREFIX}}-style-lock.sh
- change: Use shared error escaping and native interpreter paths.
- why: Quoted/control-character paths and disabled MSYS conversion broke gate output.
- breaking: no

## 2026-09-04-codex-deploy-09
- kind: script
- target: templates/art/scripts/gp_art_contract.py, templates/art/scripts/{{PREFIX}}-art-gen.py, templates/art/scripts/{{PREFIX}}-asset-validate.py
- change: Validate schemas and provenance/reference hashes; reject missing palettes and empty assets; retain attempts and condition edits on their source.
- why: Art production must verify its frozen inputs and preserve truthful provenance.
- breaking: no

## 2026-09-04-codex-deploy-10
- kind: runbook
- target: templates/common/commands/runtime/art.md, templates/common/commands/runtime/contract-art.md, templates/common/commands/runtime/contract-startup.md
- change: Route startup through the selected root doc and native art through host capabilities.
- why: Codex can invoke available image tools directly after human STYLE LOCK.
- breaking: no

## 2026-09-04-codex-deploy-11
- kind: doc
- target: templates/common/root/CLAUDE.md.tmpl
- change: Render the tool-aware root instruction name, skill invocation and memory location.
- why: Codex reads AGENTS.md and project-local memory.
- breaking: no

## 2026-09-04-fps-preset-expansion
- kind: script
- target: bootstrap.sh, lib/preset.py, templates/dimensions/3d/, profiles/
- change: compose 3D/Windows/Blender modules and enforce fresh build/runtime/art evidence
- why: user needs Godot desktop shooters to evaluate new models with this pipeline
- breaking: no (2D remains the default; bootstrap now requires Python 3 for preset JSON)

## 2026-09-04-whole-game-routing
- kind: runbook
- target: templates/common/commands/, templates/codex/, skills/gp-dev/
- change: complete whole-game briefs through staged work and inherit the session model
- why: installation alone does not fulfill a game request; role model switches distort results
- breaking: no (additive --build; explicit reference-sheet STYLE LOCK remains)

## 2026-09-04-blender-contracts
- kind: schema
- target: schemas/mesh-*.json, templates/dimensions/3d/scripts/gp_mesh.py
- change: bind exact artifacts and source inputs to mesh production provenance
- why: model/provider claims and a successful exporter do not prove valid runtime assets
- breaking: no (new mesh contracts; existing raster schemas remain unchanged)
