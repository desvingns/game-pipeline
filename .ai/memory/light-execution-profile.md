---
description: --feature --light profile — one expert implementer, one simple closer, both tools
---

- `claim --profile light` records the profile on the run, immutable across
  resume/recovery (mismatched recovery fails `profile_mismatch`).
- `route()` maps developer -> expert tier ("implementer"), reviewer/verifier ->
  simple tier ("closer"), for whichever tool the request names; an explicit
  `profiles.light.{implementer,closer}` (Codex) or
  `claude.profiles.light.{implementer,closer}` (Claude) overrides the derived
  tier. The two tools' overrides are separate blocks — never share model names
  (Codex "gpt-*", Claude "claude-*").
- Roles outside developer/reviewer/verifier -> `light_role_not_allowed`;
  Blender/replay_codec/concurrency/critical_lifecycle/data_loss risk ->
  `light_risk_requires_standard`; scope != production -> `light_profile_incompatible`.
  `--batch` is forbidden with `--light`.
- Limits (`profiles.light`, tool-neutral): max_concurrent_agents 1,
  max_attempts_per_stage 2, context_chars 12000 by default; every field is
  optional and falls back to the generator default.
- In Claude Code, a role's pinned frontmatter effort can exceed light's target
  (e.g. reviewer/verifier default to the complex tier's xhigh, light wants the
  simple tier's medium) — reported via `tier_reasoning_effort`/`effort_source`,
  same honesty mechanism as [[claude-effort-frontmatter]] for standard tiers.
- Origin: promoted from a user prototype in D:/Pet/Ground_Truth (Codex-only)
  to the canonical generator, generalized to Claude, 2026-09-13 (gp-009).
