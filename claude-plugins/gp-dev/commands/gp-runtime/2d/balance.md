<!-- gp-runtime-contracts: startup -->

# `--balance` — tune the numbers against the gate

Content data only. No code, no design changes, no widening of the corridor.

## Steps

1. **Baseline first.**

   ```
   .claude/scripts/gp-sim-godot.sh --balance --seeds 20
   ```

   Quote the JSON. A tuning session with no before-number cannot report a result,
   only a feeling. If this returns an `error_kind`, stop: there is nothing to tune
   against.
2. Read the relevant design document so the intent behind each number is known
   before any of them move.
3. Spawn `gp-economy` with the baseline, the corridor, and the intent.
4. **Check that the seed set is listed** in its report. A balance claim from
   unlisted seeds is not reproducible, and reproducibility is the only thing that
   makes this gate worth running.
5. If BLOCKED_BY_DESIGN is non-empty, stop and bring it to the user. The numbers
   have found a design problem, which is a genuinely useful outcome — and burying
   it under further tuning is how a game ends up unbalanceable.
6. Re-run the determinism gate. Content changes can alter iteration order:

   ```
   .claude/scripts/gp-sim-godot.sh --replay --seed 4242
   ```
7. Close out with `gp-docs`, recording the final numbers and why.

## Never

- Widen the corridor to pass. The corridor is a decision; changing it is the
  user's call, made explicitly, not a tuning step.
- Change the seed set to one that happens to pass.
- Report a pass without the gate line that shows it.

## Output

```
=== BALANCE RUN ===
BASELINE: <JSON line, verbatim>
ITERATIONS: <n> — <what moved, in one line each>
FINAL: <JSON line, verbatim>
SEEDS: <the exact list>
FILES_CHANGED: <paths>
DETERMINISM: <JSON line, verbatim>
INTENT_PRESERVED: <how>
BLOCKED_BY_DESIGN: <the problem numbers cannot fix, or "none">
=== END BALANCE RUN ===
```
