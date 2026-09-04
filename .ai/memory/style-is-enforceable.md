---
name: style-is-enforceable
description: Why gp ships a catalogue of style profiles instead of letting a spec describe a style in prose
metadata:
  type: project
---

The asset gate is **a function of the style**. Pixel art needs grid snapping and
palette quantisation; cel-shaded needs a dark contour along the alpha edge;
painterly is barely machine-checkable at all. If a spec invents a style as a
paragraph of prose, the gate has nothing to enforce and every asset falls back to
human review — which is the exact cost the pipeline exists to remove.

So gp ships `profiles/style/*.json`, each pairing a prompt skeleton with numeric
rules, and a game spec **instantiates** one: palette, contour width, light
direction, tiers. `--auto` chooses from the catalogue rather than inventing.
Adding a genuinely new style is a deliberate pipeline change that must include its
validation rules.

Projection follows the same logic and is a profile too, because it multiplies the
art backlog: one drawn facing plus a mirror for top-down 3/4, four plus mirrors
for true isometry. The planner reads the multiplier rather than discovering it
during production. See [[art-provider-adapters]].
