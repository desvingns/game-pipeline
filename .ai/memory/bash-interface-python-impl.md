---
name: bash-interface-python-impl
description: How gp gates keep the one-JSON-line contract while doing work bash cannot do
metadata:
  type: project
---

cmp's rule is "cross-platform bash only". gp keeps the spirit and adjusts the
letter: **bash is the interface, Python may be the implementation.** Decoding a
PNG, measuring palette distance or detecting a contour is not achievable in bash,
and pretending otherwise would produce a gate that does not actually check
anything.

The shape:

- The `.sh` wrapper owns argument parsing, profile resolution, interpreter
  detection, and the single JSON line on stdout.
- The `.py` implementation does the pixels and prints one JSON object.
- A missing interpreter or missing Pillow becomes
  `{"pass":false,"error_kind":"python_missing",...}` — never a silent pass and
  never an asset failure.
- No `jq` dependency anywhere: it is absent on stock Windows Git Bash, and a gate
  that cannot run on the author's own machine is not a gate.

Same discipline as `godot_not_found`: the environment being wrong and the game
being wrong are different answers, and conflating them sends agents to fix things
that were never broken. See [[gates-report-truth-note]].
