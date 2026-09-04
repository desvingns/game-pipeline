<!-- gp-runtime-contracts: startup -->

# `--design` — mechanics, loop, feel, content

One topic per run. Produces documents and content data — never code, never art.

## Steps

1. **Bound the topic.** If it is broader than one mechanic or one system, split it
   and ask the user which part to design now. A design document covering four
   systems is one nobody implements.
2. Spawn `{{PREFIX}}-game-designer`. It returns one DESIGN block and writes
   `docs/design/<topic>.md` plus any content data.
3. **Read the ART_COST line out loud to the user.** A design that quietly implies
   forty new sprites is the most common way an AI-first game project stalls, and
   the number is the whole point of asking for it.
4. **Read the DETERMINISM_RISKS line.** Anything listed there needs a decision
   before implementation: express it in ticks and integers, or accept that the
   replay gate will not cover it.
5. If content data changed, run the balance gate to see where the design lands
   before anyone tunes it:

   ```
   {{AGENT_DIR}}/scripts/{{PREFIX}}-sim-godot.sh --balance
   ```

   Quote the JSON. An `error_kind` here is expected early in a project — the
   harness may not exist yet — and is reported, not worked around.
6. File the follow-ups the design implies: SPECs on the code board, ART cards on
   the art board. Filing them is the deliverable; producing them is not this mode.
7. Close out with `{{PREFIX}}-docs`.

## Output

```
=== DESIGN RUN ===
TOPIC: <one sentence>
DOCS: <paths>
CONTENT: <paths, or "none">
ART_COST: <N cards, itemised>
DETERMINISM_RISKS: <list, or "none">
BALANCE_SNAPSHOT: <JSON line, or n/a: reason>
FILED:
- SPEC <id> — <goal>
- ART <id> — <asset>
OPEN_QUESTIONS: <what the user must decide>
=== END DESIGN RUN ===
```
