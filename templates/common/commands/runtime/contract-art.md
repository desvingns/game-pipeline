# contract-art — binding rules for anything that produces pixels

## Order of operations

```
ART card
  -> {{PREFIX}}-art-prompter        writes art/prompts/<id>.json
  -> {{PREFIX}}-art-gen.sh          provider adapter; writes assets/inbox/<id>.png
                                    + <id>.provenance.json
  -> {{PREFIX}}-asset-validate.sh   deterministic gate; one JSON line
  -> {{PREFIX}}-art-director        multimodal review against the locked sheet
  -> {{PREFIX}}-asset-integrator    into the Godot project
```

Each arrow is a real boundary. The prompter never generates; the generator never
judges; the validator never has taste; the director never edits pixels; the
integrator never fixes art. Collapsing any two of these is how a pipeline stops
being able to tell "we made a bad asset" from "we made a broken one".

## Provider selection

| Session | Default provider | Behaviour |
|---|---|---|
| Claude Code | `gemini` | scripted, needs `GEMINI_API_KEY` |
| Codex Desktop | `codex-native` | script renders the prompt; the agent invokes the available native image tool and registers its returned path; external-file fallback when unavailable |
| any | `manual` | same human-in-the-loop flow, any tool |

Override with `GP_ART_PROVIDER`. The prompt-spec is identical in all three cases —
that is the whole point of the adapter.

**When image generation is unavailable, stop.** Do not produce an SVG, an HTML
mock, a coloured rectangle, or an ASCII sketch "as a placeholder". A stand-in that
enters the project is indistinguishable from real art two weeks later, and it will
pass every gate that does not look at it. Emit the prompt-spec, say generation is
unavailable, and stop.

## Provenance

Every image carries `<id>.provenance.json` with the prompt-spec hash, provider,
model, parameters, timestamp, style profile, and the locked reference-sheet hash.
When a human produced the image, the agent writes the record on registration. The
asset gate fails a missing record exactly as hard as a broken alpha channel,
because an asset nobody can regenerate is a liability rather than an asset.

## Retry policy

At most **three** generation attempts per asset. Each attempt records its
`attempt` number in provenance, so the true cost of an asset stays visible. After
the third, stop and report: either the prompt-spec is wrong (fix the spec, reset
the counter) or the profile cannot express what is being asked (a profile gap
worth reporting upward). Retrying identically past three is how a run burns an
afternoon and a budget.

## Tier discipline

Never generate a tier-B gameplay asset from tier-A wording. A splash prompt
produces beautiful mush at 128 pixels. The prompter reads the tier from the ART
card and renders the corresponding canvas and constraints.
