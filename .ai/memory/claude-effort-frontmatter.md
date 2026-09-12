---
description: Claude Code subagents take a per-spawn model but effort only from frontmatter
---

- The Claude Code Agent tool accepts a per-invocation `model` (highest precedence
  since CLI v2.1.251) but no effort. `effort:` is read only from agent frontmatter.
- gp pins model+effort per role from `claude.role_tiers` at bootstrap, passes the
  tier model at spawn and reports the applied effort beside the tier's. The user
  chose this over per-tier agent copies (2026-09-12): a simple assignment for an
  xhigh role runs at xhigh, and the descriptor says so.
- Use full IDs (`claude-sonnet-5`, `claude-opus-5`); the `sonnet` alias resolves
  to older models on Bedrock/Vertex/Foundry. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`
  and `CLAUDE_CODE_EFFORT_LEVEL` override both, so record observed values.
- Sources: code.claude.com/docs/en/sub-agents and /model-config.
