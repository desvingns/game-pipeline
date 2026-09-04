<!-- gp-runtime-contracts: startup, art -->

# `--style` — build the style bible and lock the reference sheet

This runs once per game, at the start, and again only when the user deliberately
re-opens the visual direction. Everything visual afterwards is downstream of it.

## Two intake modes

Ask which, if the user did not say:

- **`--guided`** — the user supplies references (screenshots, links, images they
  like). You read what is actually in them and propose a reading.
- **`--auto`** — the user says "you decide". You choose a profile and a direction
  and present it for approval.

Both converge on the same artifacts. The difference is only where the direction
comes from.

## Steps

**1. Intake.** In guided mode, look at every reference the user gave and describe
what you actually see — contour or not, how many tonal steps, light direction,
level of abstraction, colour temperament. Do not describe what the user probably
meant; describe the pixels. In auto mode, propose a direction and say why it fits
the game concept.

**2. Profile selection.** Spawn `gp-art-director` in `instantiate` mode.
It picks a profile from `art/style/profiles/` — it does not invent one. If nothing
fits, it says so and the correct answer is to add a profile to the pipeline, which
is a separate, deliberate change.

**3. Present for approval.** Show the user: profile, palette with role names,
light direction, outline width, both tiers, and the plan for the reference sheet.
This is a gate. Wait.

**4. Trial key frames.** Generate 2-4 reference-sheet assets through the normal
art path (`contract-art`). These are `asset_type: reference_sheet`, which is the
one case the generator allows before STYLE LOCK. Anything else is refused, by
design.

**5. STYLE LOCK — hard human gate.** Show the frames. The user approves or sends
back. **This gate never proceeds unattended.** On approval:

```
.codex/scripts/gp-style-lock.sh --lock
```

Quote the JSON. The sheet hash it prints is now recorded in the provenance of
every asset the project ever generates.

**6. Freeze the profile into the project.** Copy the chosen profile to
`art/style/profiles/<id>.json` so the game keeps building the same way after the
pipeline moves on.

## Re-locking

Changing the sheet after lock invalidates comparability with everything generated
before it. That is sometimes right, and it is never accidental: state plainly what
becomes inconsistent, get explicit approval, then re-lock. `--verify` reporting
`sheet_drift` means someone edited the sheet without doing this.

## Output

```
=== STYLE RUN ===
MODE: guided | auto
PROFILE: <id> — <why this one and not the others>
PALETTE: <name #hex> ...
LIGHT: <direction>
TIERS: A <WxH>  B <range>
REFERENCE_SHEET: <N frames> — <paths>
STYLE_LOCK: <the script's JSON line, verbatim>
FROZEN_PROFILE: art/style/profiles/<id>.json
NEXT: <what the user should run next>
=== END STYLE RUN ===
```
