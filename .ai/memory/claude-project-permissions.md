---
description: Claude project allow rules for pipeline scripts and their matching limits
---

- Bootstrap (tool=claude) merges `.claude/settings.json` rules generated from the
  installed `<prefix>-*.sh` scripts: `Bash(bash .claude/scripts/<script> *)`.
  `common` (sourced) and `art-gen` (paid image API) get no rule; `style-lock` allows
  only `--verify *` and has an ask rule `*--lock*` (ask beats allow).
- Existing keys/rules are kept; a changed file is archived under the bootstrap
  run's `previous/`. Unreadable JSON is preserved and the rules are printed.
- Rules match only that literal command form from the repo root: an absolute path,
  `./` prefix or a non-safe env assignment falls back to a prompt. Project allow
  rules apply only after workspace trust (code.claude.com/docs/en/permissions).
- Read-only Claude roles (architect/reviewer/verifier) must stay Read/Glob/Grep;
  tests assert this for 2D and 3D.
