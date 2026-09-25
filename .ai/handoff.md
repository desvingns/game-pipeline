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

## Update — 2026-09-04: v0.4 dual-harness marketplace

- Completed gp-006: one `gp-dev` marketplace plugin is generated for Claude
  Code and Codex. Catalogs live at `.claude-plugin/marketplace.json` and
  `.agents/plugins/marketplace.json`; package trees live under
  `claude-plugins/gp-dev/` and `codex-plugins/gp-dev/`.
- Added `lib/build-marketplace.sh`, archive-before-replace generation,
  dimension-specific runtime fallbacks, bundled generator sources and
  `gp-bootstrap.sh` wrappers.
- Codex plugin validation and marketplace JSON checks pass. Claude validation
  passes with expected non-fatal warnings for internal lazy runbook frontmatter.
- User-facing installation instructions are in `docs/MARKETPLACE.md`; the
  standalone `install-codex.sh` path remains as a fallback.
- Next action: commit and push the v0.4 marketplace package after packaged
  generator smoke checks.

## Update — 2026-09-12: v1.0 shared backlog execution

- Completed gp-007 and the 60 approved improvements; implementation map is in
  docs/WORKFLOW.md. SPECS is shared by all projects and tools. Codex assignments
  route Luna xhigh / Sol xhigh / Astra high; recommended coordinator is Sol high.
- Claude owns its native model selection through the independent `claude` policy.
  Current model names are intentionally left for Claude to configure. No CLI bridge.
- Added portable workflow kernel, schemas, safe adoption/migration, claims,
  bounded context/ownership, recovery, evidence, fresh reviews, usage and previews.
- All 50 smoke tests and 18 real Godot/Blender integration checks pass; real Luna
  discovery passed. Package parity checks 290 files. See docs/VALIDATION-1.0.md.
- Both marketplace plugins are installed at 1.1.0. Claude requires restart; use a
  fresh Codex session to ensure refreshed guidance.
- Ground Truth was inspected read-only; no H12 implementation or runtime deployment
  occurred there. Existing games adopt/upgrade the generated runtime when requested.
- Final independent reviewer follow-up hit the host usage limit; previous findings
  were fixed. Live full-feature multi-agent, Claude dispatch, Android and image
  provider validation remain separate integration work, not claimed by fixtures.

## Update — 2026-09-12: v1.1 Codex chain mode

- Added marketplace `gp --feature --next --chain`: after one verified DONE, the
  Codex orchestrator checks the board and opens exactly one successor task with
  `create_thread`, local project environment and an empty transcript.
- Chain stops on an empty/not-ready board, REVIEW/BLOCKED/FAILED, human gate or
  unavailable project/task mapping. It never forks, sends a follow-up, changes
  model settings or bridges through the Codex CLI. Claude reports unsupported.
- Marketplace, source-parity and full smoke tests pass; both installed plugins
  are updated to 1.1.0. See docs/WORKFLOW.md and docs/USAGE.md.

## Update — 2026-09-12: v1.2 explicit Claude Code models (Claude Code)

- Completed gp-008: Claude tiers simple Sonnet 5 medium / complex Sonnet 5 xhigh /
  expert Opus 5 xhigh (full IDs). Spawns pass the tier model; effort is pinned per
  role in `.claude/agents/*.md` frontmatter from `claude.role_tiers` by
  `lib/claude.sh` + `lib/claude_agents.py` (preserved project policy wins).
- DECISION (user): role-default effort pinning, not per-tier agent copies; route
  and dispatch report applied effort beside the tier's (`tier_reasoning_effort`,
  `effort_source`), reasoning checks stay strict. 1.1 policies with an empty
  claude block fall back to defaults; `claude.mode: native` opts out.
- Fixed during validation: the adapter import left `__pycache__` in staged scripts
  that bootstrap deployed; bytecode writes are now disabled.
- 2026-09-13 follow-up (user-approved): 2D reviewer/verifier lost Bash (read-only
  now tool-enforced, packet carries diff/evidence); bootstrap merges project-scoped
  `.claude/settings.json` allow rules for installed scripts (`--lock` asks,
  art-gen keeps its prompt); `claude.max_turns` pins runner maxTurns 8.
- Docs for Claude Code 2.1.270 still list no per-spawn effort. The desktop app
  bundles 2.1.266; the npm `claude` on PATH is 2.1.197.
- Released 1.2.0: committed and pushed to origin/main; the Claude marketplace
  (Directory source D:\Pet\game-pipeline) and gp-dev plugin were refreshed.
  The Codex plugin install was not refreshed in this session.
- NEXT: live Claude dispatch check of one simple SPEC in a sandbox game; existing
  games need bootstrap `--force`/`--adopt` to receive frontmatter and settings.

## Update — 2026-09-13: v1.3 light execution profile (Claude Code)

- Completed gp-009: promoted the user's Codex-only `--feature --light` prototype
  from D:/Pet/Ground_Truth into the generator, generalized to Claude Code.
  `claim --profile light` -> one expert-tier developer (implementation+tests+one
  repair), then one simple-tier closer (reviewer, verifier). Immutable per run
  (`profile_mismatch` on mismatched recovery); `light_role_not_allowed`,
  `light_risk_requires_standard` (blender/replay_codec/concurrency/
  critical_lifecycle/data_loss), `light_profile_incompatible` (non-production);
  incompatible with `--batch`. `profiles.light`/`claude.profiles.light` optionally
  pin an explicit implementer/closer model, else derive from the expert/simple
  tier. In Claude Code, the closer's pinned frontmatter effort can exceed the
  simple tier's target — reported via `tier_reasoning_effort`/`effort_source`,
  reusing gp-008's honesty mechanism (refactored into `claude_effort_report`).
- Full smoke passes (58 tests), parity 296 files. Committed/pushed (`ecfda6e`);
  marketplace and gp-dev plugin refreshed to 1.3.0 (user must restart Claude).
- Re-adopted D:/Pet/Ground_Truth for both tools (`--force`): its hand-edited
  Codex prototype text was replaced by the canonical rendering (archived under
  its own `archive/gp-bootstrap/`); `pipeline/project.json` and
  `pipeline/model-policy.json` (including the project's own explicit
  `profiles.light` override) were preserved untouched; its 24 WIP-modified files
  were untouched. Ground_Truth's local `pipeline/tests/test_light_profile.py`
  still passes against the regenerated `.codex/scripts/gp_work.py`. Spot-checked
  Claude light routing directly against `.claude/scripts/gp_work.py` in that
  project (developer -> Opus 5/xhigh; reviewer -> Sonnet 5, honest xhigh-vs-medium
  mismatch reported).
- NEXT: live dispatch of a `--feature --light` assignment through either tool's
  native spawn (not just `route`/`policy` unit-level checks).

## 2026-09-25 — Claude: shared archive (v1.4.0)

- Every archive writer honours env `PET_ARCHIVE_ROOT` (set to `D:\Pet\archive`
  on the main machine): gp_work (gp-work, locks, claims), art-gen
  (art-attempts), Godot runner/visual (gp-exports, gp-shots), bootstrap staging
  (gp-bootstrap), build-marketplace (marketplace), install-codex
  (skills/<date>/codex-skills). Layout `<root>/<project>/<YYYY-MM-DD>/<sub>`;
  first folder per day logged in `<root>/INDEX.md`. Unset -> old `archive/`.
- `upgrade-preview` accepts a stage inside `PET_ARCHIVE_ROOT`. Tests pin the
  local archive (`PET_ARCHIVE_ROOT` popped/unset); new shared-archive tests:
  `SharedArchiveTests` (workflow) and `test_10` (pipeline). Full smoke passes,
  parity 298 files.
- NEXT: Ground_Truth still runs the 1.3.0 scripts; re-adopt with `--force` to
  pick this up.
