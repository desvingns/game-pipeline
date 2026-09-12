<!-- gp-runtime-contracts: startup, art, work -->

# `--animate` — rig and animate one unit

One unit per run.

## Preconditions

1. Every part the rig needs is integrated — validated, with provenance, referenced
   through a resource. A rig assembled from files sitting in `assets/inbox/` will
   break the moment the art is revised.
2. The design document states the response windows in milliseconds. Invented
   timings are how a game ends up feeling arbitrary; if they are missing, ask.

## Steps

1. Spawn `gp-animator-godot` with the unit id, its parts, and the timing
   requirements.
2. **Check the OVERLAP_CHECK line.** This is the specific failure mode of skeletal
   animation in a contoured style: the rest pose always looks fine and the extreme
   of the swing shows the seam. The answer must name how the extremes were checked,
   not that they were.
3. If MISSING_PARTS is non-empty, stop and file ART cards. Do not let the animator
   improvise a part.
4. Capture the result:

   ```
   .codex/scripts/gp-visual-godot.sh --scene <unit preview scene>
   ```

   Then spawn `gp-art-director` in `review` mode on the captured frames.
   A rig can satisfy every rule and still read wrong in motion, and this is the
   only place that gets caught.
5. Run build + tests; animation lives in `.tscn` and `.tres`, so a malformed track
   fails the import gate.
6. Close out with `gp-docs`.

## Output

```
=== ANIMATE RUN ===
UNIT: <id>
RIG: <bones, with rotation limits>
ANIMATIONS: <name — duration — loop|one-shot>
PROCEDURAL: <effects and timings>
OVERLAP_CHECK: <method and result at the extremes>
SHOTS: <JSON line, or n/a: reason>
DIRECTOR: <accept|revise|reject> — <reason>
GATES: <build+test JSON line>
MISSING_PARTS: <ART cards filed, or "none">
=== END ANIMATE RUN ===
```
