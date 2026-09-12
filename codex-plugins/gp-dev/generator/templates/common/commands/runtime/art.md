<!-- gp-runtime-contracts: startup, art, work -->

# `--art` — take one ART card from card to integrated asset

One card per run. With `--next`, take the top card from `art/cards/backlog/`.

## Preconditions

Verify before anything else, and stop on the first failure:

1. `art/style/reference-manifest.json` exists — otherwise there is no STYLE LOCK
   and no production art may be made. Direct the user to `--style`.
2. `{{AGENT_DIR}}/scripts/{{PREFIX}}-style-lock.sh --verify` returns `pass:true`.
   `sheet_drift` means the sheet changed after lock; that is a decision for the
   user, not something to work around.
3. The card names an asset id, type, tier, and — for a unit part — which part.

## Steps

**1. Prompt-spec.** Spawn `{{PREFIX}}-art-prompter`. It reads the bible, the
frozen profile and the sheet, and writes `art/prompts/<id>.json`. Check the
returned `RENDERED_PROMPT` yourself: it is the last cheap moment to catch a spec
that describes the wrong thing.

**2. Generate.**

```
{{AGENT_DIR}}/scripts/{{PREFIX}}-art-gen.sh --spec art/prompts/<id>.json
```

The provider comes from the session (see `contract-art`). If the result is
`action: human_in_the_loop`, the script has rendered a prompt, not an image.
<!-- tool:claude -->
Present that prompt to the user, wait for the file, then register it.
<!-- /tool:claude -->
<!-- tool:codex -->
When `provider: codex-native` and a native image-generation tool is available,
invoke it with the rendered prompt, the returned reference images, and the edit
source (for `operation: edit`). Inspect local references first when the tool
requires it. Register the actual returned image path. If the tool is unavailable
or `provider: manual`, present the prompt and wait for the user's file.
<!-- /tool:codex -->

```
bash {{AGENT_DIR}}/scripts/{{PREFIX}}-art-gen.sh --spec art/prompts/<id>.json --register <path> --attempt <n>
```

If generation is unavailable, stop. Never substitute a hand-made placeholder.

**3. Validate.**

```
{{AGENT_DIR}}/scripts/{{PREFIX}}-asset-validate.sh --image assets/inbox/<id>.png --tier <A|B>
```

Quote the JSON line verbatim. On `pass:false`, read the specific errors: they map
to concrete prompt changes (semi-transparent ratio too high means the model
produced a soft edge; colour count too high means the fills are not flat; contour
width out of range means the canvas size and the prompt disagree). Fix the
prompt-spec, not the image. Three attempts maximum.

An `error_kind` is not an asset failure. Report the environment problem and stop.

**4. Review.** Spawn `{{PREFIX}}-art-director` in `review` mode with the image,
the validator JSON, and the locked sheet. `revise` returns to step 1 with the
director's notes; `reject` returns the card to the board with a reason.

**5. Integrate.** On `accept`, spawn `{{PREFIX}}-asset-integrator`.

**6. Close out.** Move the card to `art/cards/done/`, run `{{PREFIX}}-docs`, and
record anything learned about the profile — a rule that failed to catch a real
problem is the most valuable output of an art run.

## Output

```
=== ART RUN ===
CARD: <id> — <what it is> — tier <A|B>
PROMPT_SPEC: art/prompts/<id>.json
GENERATION: provider=<...> attempts=<n>
VALIDATOR: <JSON line, verbatim, final attempt>
DIRECTOR: <accept|revise|reject> — <the one-sentence reason>
INTEGRATED: <path> pivot=<x,y> atlas=<name>
PROFILE_GAP: <a rule that should have caught something and did not, or "none">
=== END ART RUN ===
```
