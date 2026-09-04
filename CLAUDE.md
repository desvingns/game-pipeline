@AGENTS.md

# CLAUDE.md — Claude Code-specific notes

The canonical instructions for this repo live in `AGENTS.md` (imported above). This file holds only
the Claude-Code-specific bits; never duplicate rules from `AGENTS.md` here.

- **Shared vs personal memory.** The canonical, git-tracked memory is `.ai/memory/` — put durable
  framework knowledge there so Codex sees it too. Auto-memory under `~/.claude/projects/.../memory/`
  is a personal mirror; shared decisions must not live only there.
- **Exploration.** For codebase searches spanning more than ~3 lookups, use the Explore subagent;
  otherwise Glob / Grep directly.
- **Coordination.** Follow the `.ai/` protocol in `AGENTS.md` — read `.ai/handoff.md` at start and
  rewrite it before handing back to Codex.
- **Art channel.** In a Claude session the provider is `gemini` and `GEMINI_API_KEY` must be in the
  environment. Never fall back to producing an SVG or HTML placeholder when image generation is
  unavailable — emit the prompt-spec and stop, as the art contract requires.
