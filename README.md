# game-pipeline (gp)

A **generator** of AI-first development pipelines for 2D Android games and 3D
Windows shooters using Godot 4 and Blender. It is not a
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
- **Mandatory provenance** on every generated asset. An asset nobody can regenerate is a
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

### Marketplace plugin

The recommended installation is the `game-pipeline` marketplace. It exposes
`/gp` in Claude Code and `$gp-dev` in Codex, and bundles the generator for both
2D Android and 3D Windows FPS projects:

```bash
# Claude Code
claude plugin marketplace add D:/Pet/game-pipeline
claude plugin install gp-dev@game-pipeline

# Codex
codex plugin marketplace add /d/Pet/game-pipeline
codex plugin add gp-dev@game-pipeline
```

Use the GitHub URL instead of the local path when the repository is not on the
same machine. Reopen the tool session after installation. The full guide is in
[`docs/MARKETPLACE.md`](docs/MARKETPLACE.md).

For Codex, the standalone personal entry point remains available when a
marketplace cannot be registered:

```bash
bash install-codex.sh
```

Then invoke `$gp-dev` in Codex to bootstrap or run a game pipeline. It needs a
target game directory, prefix, project name and preset for a new installation.
An Android package id is required only for 2d-android. For a Windows shooter:

```text
$gp-dev create a Godot 3D arena FPS with Blender in D:/Pet/my-fps,
prefix fp, project name My FPS. Use the game-pipeline and complete the brief.
```

See [the 3D workflow](docs/3D-WINDOWS.md). To install the 2D preset from Bash:

```bash
cd /path/to/my-game
bash /path/to/game-pipeline/bootstrap.sh --tool=codex \
  --prefix=td --project-name="My TD" --package=com.example.td --non-interactive
```

Codex discovers `$td` through `.agents/skills/td/SKILL.md`, reads `AGENTS.md`,
and uses `.codex/agents/*.toml` adapters backed by canonical Markdown roles.
Try `$td --gates`, then `$td --style`. No global model or permission changes are
required. See [the Codex setup](docs/USAGE.md#codex-desktop-and-cli).

For Claude Code:

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
| build + tests | import/compile plus gdUnit4 (2D) or nonempty domain suites (3D) |
| determinism | repeat the pure simulation/domain state hash from a seed |
| balance | 2D win-rate corridor; 3D combat/resource/route observations |
| assets | raster rules (2D) or GLB geometry/rig/material/provenance checks (3D) |
| style lock | has the reference sheet drifted since it was frozen |
| FPS scenarios | production movement, combat, navigation, restart, UI and selected networking |
| screenshots / performance | fresh rendered evidence and measured frame times; needs graphics |
| export | Android APK or Windows package plus real executable smoke |

Every gate emits exactly one JSON line. `pass` records the result; `error_kind`
distinguishes missing dependencies, invalid contracts, process failures and
scenario failures so the agent can address the actual cause.

## Status

v0.4.0 adds the dual-harness `game-pipeline` marketplace plugin. v0.3.0 added
a selectively composed 3D FPS/Windows/Blender workflow, game-brief
orchestration, GLB/provenance validation, real Godot test hosts and Windows
executable smoke. The default 2D/Android workflow remains available. See
[3D-WINDOWS.md](docs/3D-WINDOWS.md), [MARKETPLACE.md](docs/MARKETPLACE.md) and
[CHANGELOG.md](CHANGELOG.md).

This is a generator: each game still needs actual gameplay, assets and tests.
Technical checks do not establish visual taste or control feel. No paired model
experiment or duplicate baseline game is required.
