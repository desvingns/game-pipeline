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
4. Prepare bounded assignments and actually spawn the selected native models. A
   simple patch uses the simple tier; cross-system work complex; algorithms/Blender
   and critical lifecycle expert. Tester writes independent behavior tests. Reviewer
   and verifier are read-only; run them over the relevant contracts and changed code.
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


Return one FEATURE RUN block: SPEC, STATUS, FILES, MODELS (requested/observed),
REVIEW, TESTS, GATE_JSON, EVIDENCE, MANUAL_CHECKS, NOT_DONE, NEXT_READY.
