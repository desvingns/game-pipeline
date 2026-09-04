# MARKETPLACE — `game-pipeline`

`game-pipeline` is available as one dual-harness marketplace plugin named
`gp-dev`. The plugin is generated from the repository's canonical templates and
works with both Claude Code and Codex. It keeps the generator bundled, so a
git-sourced installation can bootstrap a new game without a second checkout.

## What ships

| Plugin | Claude Code | Codex | Purpose |
|---|---|---|---|
| `gp-dev` | `/gp` command + `gp-runtime` fallbacks + generator wrapper | `$gp-dev` skill + runtime references + generator wrapper | Godot 2D Android or Blender-based 3D Windows FPS pipeline |

Generated projects still receive their selected prefix, dimension-specific
roles, native Codex adapters, gate scripts and frozen profiles from
`bootstrap.sh`. The marketplace plugin is the front door and bootstrap source;
it does not replace the project-local pipeline.

## Layout

```text
game-pipeline/
├── .claude-plugin/marketplace.json       # Claude Code catalog
├── .agents/plugins/marketplace.json      # Codex catalog
├── claude-plugins/gp-dev/                # Claude plugin package
│   ├── .claude-plugin/plugin.json
│   ├── commands/gp.md
│   ├── commands/gp-runtime/{2d,3d}/
│   ├── skills/gp-dev/SKILL.md
│   ├── scripts/gp-bootstrap.sh
│   └── generator/                         # bundled bootstrap source
├── codex-plugins/gp-dev/                 # Codex plugin package
│   ├── .codex-plugin/plugin.json
│   ├── skills/gp-dev/SKILL.md
│   ├── skills/gp-dev/references/runtime/{2d,3d}/
│   ├── scripts/gp-bootstrap.sh
│   └── generator/
├── templates/                            # canonical source
└── lib/build-marketplace.sh              # reproducible adapter builder
```

## Claude Code

Register the local marketplace once:

```bash
claude plugin marketplace add D:/Pet/game-pipeline
claude plugin install gp-dev@game-pipeline
```

For a portable git source, use the repository URL instead:

```bash
claude plugin marketplace add https://github.com/desvingns/game-pipeline.git
claude plugin install gp-dev@game-pipeline
```

Restart the Claude Code session after installation. Use `/gp` for an existing
generated project. A natural-language request to create a new game loads the
`gp-dev` skill and uses the bundled `gp-bootstrap.sh`; it infers
`3d-fps-windows` for a Blender-based Windows shooter and keeps `2d-android` as
the default otherwise.

## Codex

Register the repository marketplace and install its plugin:

```bash
codex plugin marketplace add /d/Pet/game-pipeline
codex plugin add gp-dev@game-pipeline
```

The git form is:

```bash
codex plugin marketplace add https://github.com/desvingns/game-pipeline.git
codex plugin add gp-dev@game-pipeline
```

Reopen the Codex project or session after installation. The plugin appears in
the Plugins page as **Game Pipeline** and the skill is invoked as `$gp-dev`.
After a project is bootstrapped, use its generated `$<prefix>` skill for
project work; `$gp-dev` remains the generator/bootstrap entry point.

## Rebuild after template changes

The plugin trees are generated artifacts. Rebuild both harness adapters from
the canonical templates after changing the runtime or skill:

```bash
bash lib/build-marketplace.sh --dry-run
bash lib/build-marketplace.sh
```

The builder archives replaced plugin trees under
`archive/marketplace/<timestamp>/` and never deletes them. Verify the catalogs,
manifests and bundled source with:

```bash
bash lib/build-marketplace.sh --check
python C:/Users/Admin/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  codex-plugins/gp-dev
claude plugin validate claude-plugins/gp-dev
```

The Claude validator may warn that internal runtime Markdown files have no
frontmatter; they are lazy-loaded runbooks rather than user-facing slash
commands. The warning is non-fatal and matches the layout used by
`mobile-pipeline`.

## Source of truth

Edit `templates/`, `skills/gp-dev/SKILL.md`, or the marketplace templates under
`templates/marketplace/`; do not hand-edit generated plugin trees. The bundled
`generator/` copies only the files needed to run `bootstrap.sh`, and is
regenerated on every build. One production workflow is preserved: the plugin
does not add a paired baseline implementation or model benchmark protocol.
