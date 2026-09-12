# Shared execution contract

## Board and authority

Every project and both tools use `SPECS/{backlog,done}/`. ACTIVE, BLOCKED and REVIEW
remain in backlog until all acceptance passes. Read the existing board rules;
preserve its index, ID scheme, order and scope. Planning alone is not approval;
the user's request to implement the selected approved scope remains authorization.

If SPECS/ is absent, **spawn backlog-discovery before creating it**: Codex must
select gpt-5.6-luna / xhigh explicitly. Claude uses its simple tier (Sonnet 5 /
medium by default). Pass only candidate paths from `work.sh discover` and the
discovery role. Wait for migration and validate its result. If delegation/model is
unavailable, report the limitation; do not silently perform a claimed simple-tier task.
A present empty board or a discovery with no tasks means backlog_empty: tell the
user clearly and stop implementation. Never create filler tasks.

Use `work.sh next [--track H] [--spec ID]`; choose by dependencies/evidence and
external readiness, not lexical filename order. Check the actual prerequisites.
Reserve with `claim --spec ID --owner <session-id>` before writing. One SPEC per
run. Optional `--batch N` requires user-authorized batch execution; keep N bounded,
stop at a human gate/blocker, and preserve each project's session restrictions.


## Chain modifier

`--chain` is unsupported in Claude Code. Report `chain_unsupported_in_claude`
and stop; this modifier opens successor tasks only through Codex.


## Models and native dispatch

Read `pipeline/model-policy.json` once. Codex: simple Luna xhigh, complex Sol xhigh,
expert Astra high. Claude Code (`claude.tiers`): simple Sonnet 5 medium, complex
Sonnet 5 xhigh, expert Opus 5 xhigh. Assign by bounded subtask, not role name or S/M
card size. Blender, new algorithms, replay codecs and critical concurrency/lifecycle
can go straight to expert. Independent review uses a suitable floor for the reviewed
risk. Never substitute one provider's models in the other tool. Do not edit global
model settings. Recommended Codex chat orchestrator: Sol high; the user's selected
primary model remains unchanged by this skill.


Claude Code accepts a per-spawn model but no per-spawn effort. Each role agent pins
`model` and `effort` in frontmatter from its `claude.role_tiers` default; the spawn
passes the tier model. The descriptor's `reasoning_effort` is the effort that actually
applies and `tier_reasoning_effort` is the tier's value; report a difference, never
hide it. Missing Claude entries use the generator defaults; `claude.mode: native`
leaves model and effort to the session. After editing Claude tiers or role_tiers,
re-run bootstrap `--force` so the role frontmatter matches the policy.

Bootstrap merges `.claude/settings.json` allow rules for this project's work and gate
scripts. Invoke them as `bash .claude/scripts/<prefix>-<name>.sh ...` from the
repository root, without path or environment prefixes, so the rules match. STYLE LOCK
`--lock` always asks and image generation keeps the default prompt.


Prepare `.ai/gp/requests/<name>.json`: role, goal, tool, complexity, risk, context
[{path,start,end}], write_paths, acceptance, stage, attempt, depth=1. `assign --run
RUN --request FILE` reserves ownership and returns native dispatch settings plus
the bounded prompt. **Actually pass model and reasoning to the native spawn tool**;
mentioning them in text is insufficient. Use a fresh compact context rather than
forking the full conversation. Claude spawns the matching role agent and passes the
descriptor model as the Agent tool `model` parameter (omitted only when null). If the
host overrides it, record the observed model; a mismatch fails finish-assignment.
No cross-provider CLI bridge is required.
Respect runtime concurrency caps and tool-enforced read-only roles; do not bypass
sandbox policy. When the tool cannot enforce narrow writes, audit the resulting
diff against ownership. No nested delegation. Wait before dependent operations.

Call `finish-assignment` with the structured result, observed actual model/effort
when supplied by the host (otherwise unknown), and observed usage (otherwise null).
The result needs status DONE|FAILED|BLOCKED, changed_files, summary, findings,
checks and blockers. Reviewers/verifiers warn and never fix. They receive the SPEC
criteria independently, not only the developer's account, plus CHANGED_FILES, the
run diff when it fits the context budget and gate evidence paths; read-only roles
have no shell. Do not silently replace
an unavailable model. Fix tool/environment failures without model escalation;
reasoning failures may escalate with the diff, failing example and tested hypotheses.
Three attempts per stage by default; diagnose/replan when exhausted, preserving
acceptance. Do not infer a wrong SPEC merely from two failed attempts.

## Context and cost

Only load the current runbook, its contracts, direct prerequisite evidence and
referenced requirement sections. Use `context` to bound packets and record source
hashes. Cached research may be reused only while those hashes still match. Exclude
archives, secrets, generated builds and irrelevant modules. Keep full logs under
docs/evidence; return concise statuses and relevant errors. Use tools directly for
mechanical gates, counters and status transitions. Do not delegate those to an LLM.
Metrics include retries, coordinator observations and unknown usage; subscription
usage is obtained from the host if available, not inferred from API prices.

## Existing projects, art and isolation

`pipeline/project.json` maps layer names, writable repositories and actual commands.
Preserve pure deterministic 2D domain rules irrespective of directory names. 3D
physics belongs to world and uses scenario tolerances. Preserve intentional use-case,
repository and mapper boundaries. Capture current changes before implementation.

SPEC gp-meta may declare dependencies, prerequisites, gates, art, acceptance_ids
and context. Required ART cards must be DONE with evidence before a dependent SPEC
closes. Keep separate code/art ownership; filing an ART card does not satisfy final
visual acceptance. Use art-estimate before large batches. Blender recipe authorship
uses the expert tier; repeated builds/exports are scripts. Blender asset tooling can
be enabled for 2D with --blender-assets without installing FPS instructions. Preserve
STYLE LOCK, immutable recipes, dependencies, provenance, previews and Godot visuals.
Verify simulation invariance when visuals/audio change gameplay-adjacent code.

Evaluated authoring is separate from production host development: explicit frozen
model/tools, context allowlist, dedicated repository, no production history or
other chapters. The runtime refuses dispatch from the production workspace. Export
the allowlist first; respect the project's author/repair contract. No mandatory
model comparison or second baseline is added to ordinary production.

## Evidence and recovery

`checkpoint --run RUN --stage STAGE --note TEXT` records progress and renews the
claim. `resume` checks acceptance and stale gates. Investigate interrupted ownership;
recover only an expired claim, preserving previous run evidence. Never remove locks
by deletion. Keep external blockers scoped; independent ready tasks remain visible.

Use `gates --run RUN` for affected checks; `--final` includes mandatory regressions.
Run registered argv via `gate --run RUN --id ID`; json-line/json-file/explicit
exit-code adapters wrap existing tests without replacing them. Gate outcomes bind
source hashes, command, logs and duration. A JSON error or skipped required check
never passes. External tools/devices still need genuine qualification evidence.

Completion maps each acceptance item (AC1..ACn, or explicit IDs) to hashed evidence.
Manual entries record performer, platform and artifact, never an invented approval.
Check the normal player entry path, not only an isolated launcher. `close --status
DONE` validates gate/evidence freshness, independent review/verifier, ART dependencies
and then updates card/index and execution handoff. REVIEW/BLOCKED requires a concrete
reason and keeps the card unfinished. Refresh the project's existing HANDOFF/STATE
and run consistency; do not create conflicting project truth. Reports include what
changed, what was actually tested, remaining checks and observed model use. Git
delivery follows existing user authorization; no automatic next SPEC or publication.
