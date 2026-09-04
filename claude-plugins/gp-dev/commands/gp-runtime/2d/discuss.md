<!-- gp-runtime-contracts: startup -->

# `--discuss` — read-only brainstorm

Nothing is written in this mode. Not a SPEC, not a card, not a file. The value of
a brainstorm is that it costs nothing to reject.

## Steps

1. Restate the topic in one sentence and confirm you understood it.
2. Spawn `gp-architect` with the topic. It returns one BRAINSTORM block.
3. Present the block. Add nothing to it — the options are the architect's, and
   editorialising over them removes the user's ability to judge them.
4. If the user picks an option, say which mode implements it (`--design`,
   `--feature`, `--art`, `--level`) and stop. Do not start.

## When the architect's answer is thin

If the BRAINSTORM has fewer than two real options, or every option touches the
same layer, that usually means the topic is a decision already made rather than a
question. Say so, and ask the user what the actual open question is.

## Output

The architect's BRAINSTORM block verbatim, then one line naming the mode that
would implement each option.
