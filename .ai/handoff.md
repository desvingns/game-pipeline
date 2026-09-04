# Handoff

_Updated: 2026-09-04 — Claude Code._

## DONE

- `docs/DESIGN.md` — decisions D1-D8 with rationale, from the founding brainstorm.
- v0.1.0 skeleton: `bootstrap.sh`, `lib/{render,detect,prompts}.sh`, four style
  profiles, two projection profiles, two schemas, the art subsystem (provider
  adapter + Pillow validator + style-lock), four Godot gate scripts, 14 agents,
  the orchestrator with nine runbooks, root doc templates, three memory memos.
- Smoke-tested: dry run, real bootstrap into a throwaway directory, no leaked
  placeholders or conditional markers.

## DECISIONS

- **Bash is the interface, Python may be the implementation.** Image analysis
  cannot be done in bash. Gates that need pixels are thin bash wrappers over
  Pillow, emitting one JSON line, degrading to a distinct `error_kind` when the
  interpreter is missing. No `jq` dependency anywhere.
- **Style is a profile instantiation, never free-form prose.** The asset gate is a
  function of the style; prose cannot be enforced. `--auto` picks from the
  catalogue, it does not invent.
- **`codex-native` is human-in-the-loop.** Codex Desktop's `image_gen` is
  interactive, so the adapter renders the prompt, stops, and registers the file a
  human brings back — writing the provenance record itself.
- **Projection is a first-class profile** because it multiplies the art backlog
  (1x for top-down 3/4, 4x for true isometry).

## NEXT

1. **Art vertical slice** — the founding milestone, deliberately before anything
   else: one tower through style bible, generation, validator, part separation,
   skeletal rig, in-scene screenshot. It tests the riskiest assumption in the
   whole design.
2. Godot harness scenes the gates expect: `res://tools/gates/sim_harness.tscn`
   and `res://tools/gates/shot.tscn`. Until they exist, `sim` and `visual` gates
   correctly report `harness_missing`.
3. Run one real Gemini generation once daily quota allows. The endpoint, auth,
   request shape and model id are verified (a 429 rather than a 404 proves the
   call is well-formed), but no image has actually come back yet, so the response
   parsing path is still untested.
4. `.codex/` adapter emission, so `--tool=codex` produces more than a directory
   name.

## OWNER

Claude Code — canonical prose, agents, runbooks, profiles, schemas, `.ai/`.
Unassigned — Codex adapters, sync tooling.

## BLOCKERS

- Godot 4 is not installed on this machine. Every Godot gate is written and
  syntax-clean but has never executed; they currently return `godot_not_found`.
- Codex Desktop's `image_gen` capability has not been verified from this repo; the `codex-native`
  adapter is written for the human-in-the-loop path either way.
