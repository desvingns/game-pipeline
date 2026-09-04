<!-- gp-runtime-contracts: startup -->

# `--feature` — from SPEC to shipped

One SPEC per run. With `--next`, take the top SPEC from
`{{AGENT_DIR}}/specs/backlog/`.

## 1. SPEC

If the user gave free text, synthesise a SPEC. Existing approval of the brief
covers implementation within its scope; ask only for unresolved material choices.

```
SPEC: <id>
GOAL: <one sentence, in player-visible terms>
LAYERS: content | sim | render | ui
BEHAVIOUR:
- <observable statement, testable>
CONTENT: <data files added or changed, or "none">
ART: <ART cards this needs — filed separately, not produced here>
DETERMINISM: <how this stays replay-stable>
OUT_OF_SCOPE: <what is deliberately not in this SPEC>
DONE_WHEN:
- <verifiable condition>
```

If the SPEC needs art, file the ART cards on `art/cards/backlog/` and continue
with a placeholder-free implementation — code that works with the assets that
exist. `--feature` never generates art; mixing the two makes a run that cannot be
reviewed as one thing.

## 2. Implement

Spawn `{{PREFIX}}-developer-godot` with the approved SPEC. Move the SPEC to
`{{AGENT_DIR}}/specs/active/`.

## 3. Review

Spawn `{{PREFIX}}-reviewer-godot` over the changed files. Any `blocker` returns to
step 2 with the findings. Maximum two repair cycles; a third means the SPEC is
wrong, and that goes back to the user rather than into a fourth attempt.

## 4. Test

Spawn `{{PREFIX}}-tester-godot` with the SPEC and the changed files. Tests are
written by a different role than the code, deliberately.

## 5. Gates

Through `{{PREFIX}}-runner-godot`, quoting every JSON line verbatim:

```
{{AGENT_DIR}}/scripts/{{PREFIX}}-runner-godot.sh
{{AGENT_DIR}}/scripts/{{PREFIX}}-sim-godot.sh --replay --seed <n>     # if sim/ changed
{{AGENT_DIR}}/scripts/{{PREFIX}}-sim-godot.sh --balance               # if content changed
```

A failing gate returns to step 2. An `error_kind` stops the run and is reported as
an environment problem — never silently skipped, and never treated as a pass.

## 6. Verify

Spawn `{{PREFIX}}-verifier-godot`. It asks whether the user would actually see
this change in the running game. `pass:false` returns to step 2.

## 7. Close out

Move the SPEC to `done/`, run `{{PREFIX}}-docs`, present the verifier's manual
checks in **{{UI_LANGUAGE}}**, and ask before pushing.

## Output

```
=== FEATURE RUN ===
SPEC: <id> — <goal>
IMPLEMENTATION: <n files> — <the one-line summary>
REVIEW: pass|fail after <n> cycles
TESTS: <n tests across n files>
GATES:
- <each JSON line, verbatim>
VERIFIER: <JSON line, verbatim>
MANUAL_CHECKS:
- <in {{UI_LANGUAGE}}>
ART_CARDS_FILED: <ids, or "none">
NOT_DONE: <what was left out and why>
=== END FEATURE RUN ===
```
