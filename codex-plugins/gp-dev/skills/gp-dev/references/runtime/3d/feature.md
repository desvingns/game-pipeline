<!-- gp-runtime-contracts: startup, 3d -->

# --feature

Write a bounded SPEC from the brief or take --next. Include player-visible goal,
layers, content/art/audio needs, pure-rule changes, physics scenarios, acceptance
criteria and exclusions. Existing user approval covers work within its scope;
ask only for unresolved material choices. Move the SPEC to active/.

Use developer-godot, independent reviewer-godot, then tester-godot. Preserve
write ownership; testers write actual suites and scenarios, reviewers only warn.
Fix review/test findings without changing acceptance criteria. Two unsuccessful
repair cycles require diagnosing the cause and revising the approach; an external
blocker is reported with retained evidence, never hidden behind green status.

Run runner-godot.sh, sim-godot.sh --replay for domain changes, and affected
fps-godot.sh scenarios. For art run mesh-validate.sh --all and style-lock.sh
--verify. Visual/performance work needs a rendered run. Use verifier-godot to
check reachability from the normal main scene and evidence against the SPEC.
Close with docs; move to done/ only when criteria are met. Export the complete
Windows package when the brief requests a playable delivery.
Return one FEATURE RUN block: SPEC, FILES, REVIEW, TESTS, GATE_JSON, VERIFIER,
MANUAL_CHECKS (en), NOT_DONE.
