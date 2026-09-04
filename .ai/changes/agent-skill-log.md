# Agent / template change log

Append-only. Format: `.ai/changes/README.md`.

## 2026-09-04-initial-roster
- kind: agent
- target: templates/{common,art,godot}/agents/*.md
- change: create the initial 14-agent roster for v0.1.0
- why: founding brainstorm; the roster splits art into prompter / generator /
  validator / director / integrator so that "bad asset" and "broken asset" fail
  in different places
- breaking: no

## 2026-09-04-style-profiles
- kind: profile
- target: profiles/style/*.json, profiles/projection/*.json
- change: add four style profiles and two projection profiles, each pairing a
  prompt skeleton with machine-checkable rules
- why: the asset gate is a function of the style, so a style described as prose
  cannot be enforced; the projection multiplier must be known before the backlog
  is sized, not discovered during production
- breaking: no
