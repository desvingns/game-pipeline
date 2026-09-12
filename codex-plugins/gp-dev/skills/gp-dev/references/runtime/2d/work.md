<!-- gp-runtime-contracts: startup, work -->

# Shared workflow utilities

Use Bash: `.codex/scripts/gp-work.sh --root <project> <command>`.
The command is a deterministic local utility, not another AI agent.

| Selector | Command / behavior |
|---|---|
| --adopt | adopt preview, inspect candidates, then adopt --apply; configure existing real gates |
| --doctor | doctor; tool availability is not qualification |
| --status | status and consistency; explain ready/blocked/empty |
| --resume ID | locate owned run in .ai/gp/runs, resume --run ID, continue its stage |
| --metrics | metrics; observed usage and unknowns, no invented limit coefficients |

Adoption preserves existing architecture and test entry points. All projects use
SPECS/. Keep project-specific layer mappings, repositories, gate commands and
qualification tiers in pipeline/project.json. Do not copy host-specific rules into
the generic skill. Read only relevant sections of existing architecture documents.

If SPECS is absent, follow the discovery protocol in contract-work before creating
it. A present but empty board is reported as backlog_empty without discovery.
