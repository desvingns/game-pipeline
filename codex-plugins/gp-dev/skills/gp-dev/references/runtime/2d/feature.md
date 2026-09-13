<!-- gp-runtime-contracts: startup, work -->

# --feature — one shared SPEC to a verified result

1. Orient through contract-startup and contract-work. Adopt existing paths/checks
   when project.json is absent. If SPECS/ is missing, delegate discovery first;
   report backlog_empty if no tasks exist. Preserve the original task descriptions.
2. Select with work.sh next and --spec/--track. For free text, author one bounded
   SPECS/backlog card with goal, behavior, dependencies, exclusions and observable
   acceptance (pipeline/spec-board.md). Existing scope approval persists. Preview
   actual files, prerequisites, model assignments and checks under --preview.
3. Claim the task before edits. Capture existing changes; preserve the project's
   architecture mapping and pure simulation rules. Resolve required ART dependencies
   rather than claiming final acceptance with unfinished assets.
4. Under the standard profile, prepare bounded assignments and actually spawn the
   selected native models. A simple patch uses the simple tier; cross-system work
   complex; algorithms/Blender and critical lifecycle expert. Tester writes
   independent behavior tests. Reviewer and verifier are read-only; run them over
   the relevant contracts and changed code.
5. Repair concrete findings within the attempt budget. Escalate reasoning failures
   with current diff, reproduction and rejected hypotheses, not full conversation.
   Environment failures require environment diagnosis, not a more expensive model.
6. Checkpoint stages; run registered affected gates directly, then mandatory final
   gates. Do not spawn an LLM just to run a script. Existing project harnesses remain
   authoritative. Missing real engine/device/provider evidence cannot become pass.
7. Verify the normal player entry path and each acceptance item. Use the required
   rendered/device evidence for visual work. In 2D, keep logical simulation pure
   and replay-stable; in 3D, physics uses real scenarios with agreed tolerances.
8. Close through work.sh with hashed acceptance evidence, actual manual checks,
   independent reviewer/verifier results and completed ART dependencies. Refresh
   the existing project handoff/state and run consistency. Report REVIEW/BLOCKED
   precisely when something remains. Stop after one task unless a batch is explicitly
   authorized and compatible with the project's execution contract.

9. With Codex `--chain`, after a verified DONE run `work.sh status`, then create
   exactly one new Codex task with `create_thread` in the same saved project and
   the prompt `Run gp --feature --next --chain in the current project.` The new
   task must have an empty transcript and inherit no model override. Do not use
   `fork_thread` or `send_message_to_thread`. Stop on `backlog_empty`,
   `no_ready_tasks`, a blocker, a human gate or unavailable task creation. Claude
   reports `chain_unsupported_in_claude` for this modifier.


## `--light` profile

Use this only with `--feature`, never with `--batch`. Claim with `work.sh claim
--profile light`. Dispatch one expert-tier developer assignment that owns production
implementation, its focused tests and up to one repair pass. Do not create separate
tester or architect assignments. Keep one compact context packet and return a concrete
failure to the same developer instead of opening a new repair role.

After the source is stable, run the required final gates once. Additional affected
gates are justified only by a concrete failure or a changed source snapshot. Then use
one fresh simple-tier closer sequentially for two read-only runtime assignments:
reviewer first, verifier second. They remain independent of implementation and each
must return its own result contract. Mandatory final gates, manual checks, acceptance
mapping, source-bound evidence, ART dependencies and normal player-path verification
are identical to the standard profile. If the runtime reports
`light_risk_requires_standard`, stop and rerun the SPEC with the standard profile;
do not weaken or relabel its risk. In Claude Code, the closer's pinned frontmatter
effort may exceed the simple tier's; the dispatch descriptor's `tier_reasoning_effort`
reports the gap honestly, it does not silently claim the cheaper effort ran.

Return one FEATURE RUN block: SPEC, STATUS, PROFILE, FILES, MODELS (requested/observed),
REVIEW, TESTS, GATE_JSON, EVIDENCE, MANUAL_CHECKS, NOT_DONE, NEXT_READY.
