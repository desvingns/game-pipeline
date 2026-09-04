# Handoff

_Updated: 2026-09-04 — Codex._

## DONE

- v0.2.0 working tree: real Codex skills/root instructions/native role adapters,
  staged bootstrap upgrades, append-only memory, gate-truth fixes and art contract
  checks. Review: `docs/REVIEW-2026-09-04.md`; task: `.ai/tasks/gp-004.md`.
- Personal `gp-dev` installed at `C:/Users/Admin/.codex/skills/gp-dev`; sandbox
  generated at `D:/Pet/game-pipeline/out/codex-demo`. Both skills are discovered
  and enabled by local Codex CLI 0.153.1 app-server.
- Nine regression groups pass under Windows Git Bash. Independent sandbox
  `$gp --gates` reports `project_missing`, without claiming readiness.

## DECISIONS

- Keep one canonical template system with thin adapters. Codex roles inherit
  session model settings; no global model, trust or permission configuration changed.
- Codex native art runs through the host image tool when available, then file
  registration. External-file fallback remains; STYLE LOCK requires human approval.
- Preserve project state, boards, frozen art and custom instructions on upgrade;
  archive replaced runtime files. Memory stays append-only.
- Screenshot capture requires rendering; Godot `--headless` disables it.

## NEXT

1. Complete the real art/game vertical slice (gp-001), including one asset,
   approved style, rig, actual screenshot, Android export and device launch.
2. Implement and validate real Godot/gdUnit4 harnesses (gp-002) in a game repo.
3. Verify live image-provider behavior (gp-003); no live generation was run here.
4. Add profile rule coverage, provenance v2 image binding, cross-platform CI and
   bounded engine execution as prioritized in the review.

## OWNER

Unassigned — follow-up game vertical slice and engine harness integration.

## BLOCKERS / LIMITS

- The sandbox is a pipeline installation, not a game; `game/project.godot` and
  an approved reference sheet are absent. Godot is not on the tested PATH.
- Regression tests use a fake engine and generated pixel fixtures. Real engine,
  Android, native named-agent feature workflows and image quality remain unverified.
- Changes are local; no commit/push was performed in this turn.

## Update — 2026-09-04: v0.3 Windows FPS expansion

- User approved extending one generator and excluded paired model experiments.
- Completed gp-005: selected 2D/Android and 3D/Windows/Blender presets, FPS/network
  modules, whole-game build routing, inherited role models, production and runtime
  gates. See docs/3D-WINDOWS.md and docs/VALIDATION-0.3.md.
- Real Godot/Blender integration passed 18 checks, including exported executable
  smoke and expected failure paths. Personal gp-dev has been updated.
- The generated integration scene is a test fixture, not a full FPS or network
  game. Follow-up real user game creation happens in a separate repository.
- Existing v0.2 working changes were preserved; no commit/push performed.
