# game-pipeline (gp)

A **generator** of AI-first development pipelines for 2D mobile games. It is not a
game and not a game engine: `bootstrap.sh` renders a template tree into one game
repository, producing specialist agents, an orchestrator command, deterministic
gate scripts, and an art subsystem.

Sibling project: [`claude-mobile-pipeline`](https://github.com/desvingns/mobile-pipeline),
which does the same for mobile applications. gp vendored its framework and then
diverged.

## Why it exists

Building a game with agents fails in a specific place. Code can be reviewed as a
diff, tested, and gated; **art cannot**, and by default every generated asset is
an independent roll that a human has to look at. A pipeline where a person
eyeballs three hundred sprites is not an AI-first pipeline, it is a slow one.

gp's answer is to make style machine-checkable:

- A **catalogue of style profiles** — each a prompt skeleton plus rules a
  validator can actually enforce (palette distance, colour count, contour width,
  alpha hygiene, grid discipline). A game **instantiates** a profile; it never
  invents a style as prose, because prose cannot be enforced.
- A **frozen reference sheet** behind a hard human gate (STYLE LOCK). Every
  generation is conditioned on it, so assets made weeks apart still match.
- **Mandatory provenance** on every image. An asset nobody can regenerate is a
  liability.
- A **deterministic asset gate** that rejects the broken, so the expensive
  multimodal review only ever sees plausible candidates.

The same discipline the code side already had — deterministic gates, one JSON
line, reviewers that warn rather than fix — extended to the part of game
development that usually escapes it.

## Engine: Godot 4

Chosen on one criterion: how completely the project is representable as text and
buildable headless from the command line. `.tscn` / `.tres` / `project.godot` are
readable text an agent edits directly and a human reviews as a diff; export needs
no license activation; tests run headless. Unity's editor is a partial source of
truth — an LLM writes C# well but cannot wire inspector references without editor
scripts — which breaks the review loop this pipeline depends on. Full rationale in
[`docs/DESIGN.md`](docs/DESIGN.md).

## Quick start

```bash
cd /path/to/my-game
/path/to/game-pipeline/bootstrap.sh \
  --prefix=td --project-name="My TD" --package=com.example.td
```

Then, in your agent harness:

```
/td --style            # style bible + reference sheet + STYLE LOCK
/td --design <topic>   # mechanics, loop, feel, content
/td --art --next       # one asset: prompt-spec -> generate -> validate -> review -> integrate
/td --feature --next   # SPEC -> code -> review -> tests -> gates -> verify
/td --gates            # health check
```

See [`docs/USAGE.md`](docs/USAGE.md) for every flag, and
[`AGENTS.md`](AGENTS.md) for the rules that apply when working *on* this repo.

## Gates

| Gate | Answers |
|---|---|
| build + tests | does it import, compile, and pass gdUnit4 |
| determinism | same seed, same state hash, twice |
| balance | is the win rate inside the corridor across many seeds |
| assets | does this image obey its style profile, and can it be regenerated |
| style lock | has the reference sheet drifted since it was frozen |
| screenshots | does the scene render headlessly |
| export | does an APK come out |

Every one emits exactly one JSON line. `"error_kind"` means the environment is
wrong, not the game — a distinction that decides whether an agent goes off to fix
something that was never broken.

## Status

v0.1.0 — working skeleton. The generator, the render engine, the profile
catalogue, the art subsystem and the gate scripts are real. Not yet built: audio,
on-device performance gate, playtest agent, the `--bench` model-comparison mode,
and Codex `.codex/` adapter emission. See [`CHANGELOG.md`](CHANGELOG.md).
