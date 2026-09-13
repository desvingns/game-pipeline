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

## 2026-09-04-marketplace
- kind: plugin
- target: lib/build-marketplace.sh, templates/marketplace/, claude-plugins/gp-dev/, codex-plugins/gp-dev/, .claude-plugin/marketplace.json, .agents/plugins/marketplace.json
- change: Package one gp-dev marketplace plugin for Claude Code and Codex with generated runtime adapters and a bundled generator/bootstrap source.
- why: Make Game Pipeline discoverable and installable from the Codex and Claude Code plugin marketplaces while preserving one canonical production workflow.
- breaking: no (standalone install-codex.sh and generated project workflows remain available)

## 2026-09-12-gp007-001
- kind: script
- target: bootstrap.sh
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-chain-001
- kind: runbook
- target: templates/marketplace/SKILL.md.tmpl
- change: Define Codex-only sequential chain sessions with empty transcripts and explicit stop states.
- why: Continue approved ready SPECS one per fresh Codex task.
- breaking: no

## 2026-09-12-gp007-chain-002
- kind: runbook
- target: templates/marketplace/gp.md.tmpl
- change: Expose the --chain modifier in the marketplace router and reject it in Claude Code.
- why: Make the requested chain invocation discoverable in the marketplace command.
- breaking: no

## 2026-09-12-gp007-chain-003
- kind: runbook
- target: templates/common/commands/runtime/contract-work.md
- change: Specify native create_thread, local project targeting, duplicate guards and termination conditions.
- why: Keep chain behavior consistent in generated projects and marketplace fallbacks.
- breaking: no

## 2026-09-12-gp007-chain-004
- kind: doc
- target: docs/WORKFLOW.md
- change: Document sequential Codex chain usage and its boundaries against --batch.
- why: Give users an auditable command contract and recovery expectations.
- breaking: no

## 2026-09-12-gp007-chain-005
- kind: script
- target: tests/test_marketplace.py
- change: Verify Codex retains create_thread while Claude receives only the unsupported result.
- why: Catch accidental cross-tool chain leakage during package rendering.
- breaking: no

## 2026-09-12-gp007-002
- kind: script
- target: lib/build-marketplace.sh
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-003
- kind: script
- target: lib/check-parity.py
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-004
- kind: script
- target: lib/codex.sh
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-005
- kind: schema
- target: schemas/work-assignment.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-006
- kind: schema
- target: schemas/work-evidence.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-007
- kind: schema
- target: schemas/work-migration.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-008
- kind: schema
- target: schemas/work-model-policy.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-009
- kind: schema
- target: schemas/work-project.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-010
- kind: schema
- target: schemas/work-result.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-011
- kind: schema
- target: schemas/work-run.schema.json
- change: Define and validate the versioned shared execution payload.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-012
- kind: doc
- target: skills/gp-dev/SKILL.md
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-013
- kind: doc
- target: templates/codex/SKILL.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-014
- kind: agent
- target: templates/common/agents/{{PREFIX}}-backlog-discovery.md
- change: Apply shared SPECS and native model policy while preserving game contracts.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-015
- kind: runbook
- target: templates/common/commands/runtime/animate.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-016
- kind: runbook
- target: templates/common/commands/runtime/art.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-017
- kind: runbook
- target: templates/common/commands/runtime/build.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-018
- kind: runbook
- target: templates/common/commands/runtime/contract-startup.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-019
- kind: runbook
- target: templates/common/commands/runtime/contract-work.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-020
- kind: runbook
- target: templates/common/commands/runtime/feature.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-021
- kind: runbook
- target: templates/common/commands/runtime/manifest.tsv
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-022
- kind: runbook
- target: templates/common/commands/runtime/work.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-023
- kind: runbook
- target: templates/common/commands/{{PREFIX}}.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-024
- kind: doc
- target: templates/common/pipeline/model-policy.json
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-025
- kind: doc
- target: templates/common/root/CLAUDE.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-026
- kind: script
- target: templates/common/scripts/gp_work.py
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-027
- kind: script
- target: templates/common/scripts/{{PREFIX}}-work.sh
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-028
- kind: doc
- target: templates/common/specs/README.md
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-029
- kind: doc
- target: templates/dimensions/3d/root/CLAUDE.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-030
- kind: doc
- target: templates/dimensions/3d/root/DOCUMENTATION.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-031
- kind: runbook
- target: templates/dimensions/3d/runtime/animate.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-032
- kind: runbook
- target: templates/dimensions/3d/runtime/art.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-033
- kind: runbook
- target: templates/dimensions/3d/runtime/feature.md
- change: Route the shared backlog workflow through bounded native assignments and verified evidence.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-034
- kind: script
- target: templates/dimensions/3d/scripts/gp_mesh.py
- change: Implement and validate portable adoption, dispatch, execution or packaging behavior.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-035
- kind: agent
- target: templates/godot/agents/{{PREFIX}}-developer-godot.md
- change: Apply shared SPECS and native model policy while preserving game contracts.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-036
- kind: doc
- target: templates/marketplace/SKILL.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp007-037
- kind: doc
- target: templates/marketplace/gp.md.tmpl
- change: Document the shared SPECS workflow and independent tool policies.
- why: Deliver the approved universal backlog and model-budget workflow.
- breaking: yes (legacy code boards migrate to SPECS through discovery)

## 2026-09-12-gp008-001
- kind: profile
- target: templates/common/pipeline/model-policy.json
- change: Set Claude tiers to Sonnet 5 medium / Sonnet 5 xhigh / Opus 5 xhigh and add role_tiers.
- why: The user requested concrete Claude Code subagent models and reasoning effort.
- breaking: no

## 2026-09-12-gp008-002
- kind: schema
- target: schemas/work-model-policy.schema.json
- change: Describe claude.mode (tiered|auto|native), tiers, role_tiers and orchestrator.
- why: Validate the explicit Claude policy shape.
- breaking: no

## 2026-09-12-gp008-003
- kind: script
- target: templates/common/scripts/gp_work.py
- change: Route Claude assignments to tier models and report the frontmatter-applied effort separately.
- why: Claude Code accepts a per-spawn model but no per-spawn effort.
- breaking: no (dispatch gains effort_source and tier_reasoning_effort for Claude)

## 2026-09-12-gp008-004
- kind: script
- target: lib/claude.sh, lib/claude_agents.py, bootstrap.sh
- change: Pin model and effort into Claude role frontmatter from the effective project policy.
- why: Frontmatter is the only place Claude Code reads subagent effort.
- breaking: no

## 2026-09-12-gp008-005
- kind: runbook
- target: templates/common/commands/runtime/contract-work.md
- change: Document Claude tiers, per-role effort pinning and spawn-time model passing.
- why: The orchestrator must pass the model parameter and report applied effort.
- breaking: no

## 2026-09-12-gp008-006
- kind: runbook
- target: templates/common/commands/{{PREFIX}}.md
- change: State the Claude Code tier models in the model-policy invariant.
- why: Keep the router consistent with the explicit Claude policy.
- breaking: no

## 2026-09-12-gp008-007
- kind: agent
- target: templates/common/agents/{{PREFIX}}-backlog-discovery.md
- change: Name the Claude simple tier (Sonnet 5 / medium) for discovery.
- why: Replace the former native-choice wording.
- breaking: no

## 2026-09-12-gp008-008
- kind: doc
- target: templates/marketplace/SKILL.md.tmpl, templates/marketplace/gp.md.tmpl, templates/dimensions/3d/root/CLAUDE.md.tmpl
- change: Document the explicit Claude Code tiers in marketplace and 3D root instructions.
- why: Keep packaged guidance consistent with the policy.
- breaking: no

## 2026-09-13-gp008-009
- kind: agent
- target: templates/godot/agents/{{PREFIX}}-reviewer-godot.md, templates/godot/agents/{{PREFIX}}-verifier-godot.md
- change: Remove Bash so Claude read-only roles are tool-enforced; read changed files, diff and evidence from the packet.
- why: Read-only was not enforced for 2D reviewer/verifier in Claude Code.
- breaking: no (the coordinator supplies diff and evidence paths)

## 2026-09-13-gp008-010
- kind: script
- target: lib/claude.sh, lib/claude_settings.py, bootstrap.sh
- change: Merge project-scoped .claude/settings.json allow rules for installed work and gate scripts.
- why: Unattended Claude runs stalled on permission prompts for the pipeline's own scripts.
- breaking: no (existing settings are preserved and archived before change)

## 2026-09-13-gp008-011
- kind: script
- target: templates/common/scripts/gp_work.py, lib/claude_agents.py, templates/common/pipeline/model-policy.json
- change: Add claude.max_turns and pin maxTurns in role frontmatter (runner: 8).
- why: Bound the mechanical runner role.
- breaking: no

## 2026-09-13-gp008-012
- kind: runbook
- target: templates/common/commands/runtime/contract-work.md
- change: Pass CHANGED_FILES, diff and evidence to shell-less read-only roles; document canonical script invocation for allow rules.
- why: Keep reviewer independence and permission matching explicit.
- breaking: no

## 2026-09-13-gp009-001
- kind: script
- target: templates/common/scripts/gp_work.py
- change: Add the light execution profile (profile_config/claude_effort_report/light_model), route/claim/assign/context_packet/resume/metrics/CLI support, generalized to both tools.
- why: Promote the user's Codex-only prototype (D:/Pet/Ground_Truth) into the generator and extend it to Claude Code.
- breaking: no (profiles.light/claude.profiles.light are additive; missing entries derive from the expert/simple tier)

## 2026-09-13-gp009-002
- kind: schema
- target: schemas/work-model-policy.schema.json
- change: Describe profiles.light and claude.profiles.light (optional implementer/closer + limits).
- why: Keep the schema consistent with the new policy shape.
- breaking: no

## 2026-09-13-gp009-003
- kind: runbook
- target: templates/common/commands/runtime/feature.md, templates/dimensions/3d/runtime/feature.md, templates/common/commands/runtime/contract-work.md, templates/common/commands/{{PREFIX}}.md
- change: Document --light claim/dispatch/close semantics and the tier-derivation mapping for both tools.
- why: The orchestrator must claim with --profile light and honor its guards.
- breaking: no

## 2026-09-13-gp009-004
- kind: doc
- target: templates/marketplace/SKILL.md.tmpl, skills/gp-dev/SKILL.md, templates/marketplace/gp.md.tmpl, docs/WORKFLOW.md, docs/USAGE.md
- change: Document the light execution profile for packaged installs and usage docs.
- why: Keep installed guidance consistent with the policy.
- breaking: no
