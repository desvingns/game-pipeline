<!-- gp-runtime-contracts: startup -->

# `--gates` — run every applicable gate and report

A read-only health check. Changes nothing, fixes nothing, and that is what makes
its answer worth having.

## What to run

Through `{{PREFIX}}-runner-godot`, in this order — cheapest and most likely to
fail first, so a broken import does not hide behind a four-minute balance run:

| # | Gate | Command | Applicable when |
|---|---|---|---|
| 1 | build + tests | `{{PREFIX}}-runner-godot.sh` | always |
| 2 | determinism | `{{PREFIX}}-sim-godot.sh --replay --seed 4242` | `sim/` exists |
| 3 | balance | `{{PREFIX}}-sim-godot.sh --balance --seeds 20` | content tables exist |
| 4 | style lock | `{{PREFIX}}-style-lock.sh --verify` | the sheet is locked |
| 5 | assets | `{{PREFIX}}-asset-validate.sh --image <each>` | assets exist |
| 6 | screenshots | `{{PREFIX}}-visual-godot.sh --all` | a shot list exists |
| 7 | APK export | `{{PREFIX}}-runner-godot.sh --export` | only on request |

"Applicable" is decided by looking, not by assuming. A gate that does not apply is
reported as `n/a` with the reason; a gate that could not run is reported with its
`error_kind`. Neither is a pass.

## Asset sweep

For gate 5, validate every file under `game/assets/` that has a provenance
sibling, and report the count of passes, failures, and — separately — assets with
no provenance at all. That last number is the one worth watching: it only grows
when somebody bypassed the pipeline.

## Reporting

Quote every JSON line verbatim. Do not summarise a failure into prose; the line
contains the specific rule that failed, and paraphrasing loses it.

Rank findings by what blocks shipping: a failing determinism gate outranks a
failing asset, which outranks a balance corridor miss.

## Output

```
=== GATES ===
1 BUILD+TESTS: <JSON line, or n/a: reason>
2 DETERMINISM:  <JSON line, or n/a: reason>
3 BALANCE:      <JSON line, or n/a: reason>
4 STYLE_LOCK:   <JSON line, or n/a: reason>
5 ASSETS:       <n passed / n failed / n without provenance>
   FAILURES:
   - <asset> — <the specific rule>
6 SCREENSHOTS:  <JSON line, or n/a: reason>
7 EXPORT:       <JSON line, or "not requested">

ENVIRONMENT: <every error_kind observed, or "clean">
BLOCKING: <what must be fixed before shipping, in order>
=== END GATES ===
```
