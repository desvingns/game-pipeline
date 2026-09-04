<!-- gp-runtime-contracts: startup -->

# `--level` — maps, paths, wave tables

One level per run. Produces content data only.

## Steps

1. Read the projection profile named in the style bible. It decides the grid shape
   and, through `backlog_multiplier`, what a new enemy type costs in art.
2. Spawn `gp-level-designer`.
3. **Check the PATH_CHECK line.** Reachability and walkability are verifiable, so
   an assertion without a method is not acceptable. If the project has a content
   validation test, run it; if it does not, that is a SPEC worth filing.
4. Run the balance gate on the new level:

   ```
   .claude/scripts/gp-sim-godot.sh --balance --seeds 20
   ```

   Quote the JSON. Outside the corridor is not a failure of this mode — it is the
   handoff to `--balance`, and saying so is more useful than tuning here.
5. If the level introduces an enemy or tower that does not exist, stop. That is a
   design decision, not a level-authoring one; file it and say so.
6. Close out with `gp-docs`.

## Output

```
=== LEVEL RUN ===
LEVEL: <id> — <grid, paths, waves>
PATH_CHECK: <method and result>
FILES: <paths>
BALANCE: <JSON line, or n/a: reason>
ART_COST: <N cards after the multiplier, or "none">
HANDOFF: <--balance, or "none">
BLOCKED_BY: <missing content that must be designed first, or "none">
=== END LEVEL RUN ===
```
