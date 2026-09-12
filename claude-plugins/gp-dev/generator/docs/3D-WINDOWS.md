# Godot / Blender / Windows FPS workflow

gp remains a generator, not a game engine or a bundled FPS game. Version 0.3
composes a common orchestrator with a selected dimension, platform, art, genre
and network contract. The existing 2D/Android path keeps its simulation rules
and raster art. The new 3D path installs only its own role/runtime overrides.

## Install and use

Run from a separate game directory (Python 3 is required to read preset JSON):

```bash
bash /path/to/game-pipeline/bootstrap.sh --preset=3d-fps-windows \
  --tool=codex --prefix=fp --project-name="My FPS" \
  --genre=arena --network=offline --non-interactive
```

No Android package is needed. Genre is arena, tactical or horde. Network mode is
offline by default; coop and competitive add explicit implementation guidance
and a required network scenario. These modules do not implement game-specific
netcode for the model. The model must build it against the approved brief.

Then give `$fp --build <game brief>` (Claude: `/fp --build`). A natural whole-game
request also selects build. It creates a staged plan/boards, then completes the
brief through design, art, code, tests, polish and executable delivery. All roles
follow the project model policy: Codex and Claude Code route by complexity; Claude pins effort per role agent. Image/audio providers remain explicit.

An approved brief authorizes its implementation without repeated confirmations
for routine steps. STYLE LOCK still waits for approval of the actual references.
Concept work and approved non-production blockouts may run before that lock.

## Pure rules and Godot physics

`domain/` has RefCounted-only seeded state transitions: ammo, health, cooldowns,
weapon rules, inventory and encounter state. `world/` integrates CharacterBody3D,
collision and navigation; `input/` provides shared commands for human and bots;
`render/` and `ui/` display actual state. Physics tests use concrete scenarios and
documented tolerances. Two equal domain hashes do not certify whole-world replay.

Godot/Jolt integration cannot be assumed to supply deterministic input/state at
every layer merely because Jolt can be deterministic. See the
[integration's explanation](https://github.com/godot-jolt/godot-jolt#what-about-determinism).

## Art production

After approving the style sheet, run the generated style-lock.sh --lock.
The machine profile is stylized-3d; its qualitative review checklist accompanies
every asset pass. Material palettes, visual language and reference interpretation
are recorded in art/style/style-bible.json and judged using actual images.

Create a Blender recipe defining build(spec), and a mesh spec:

```json
{
  "spec_version": 1, "id": "crate", "kind": "prop",
  "source": "tools/blender/crate.py", "dependencies": [], "seed": 4242,
  "creator": {"tool": "codex", "model": "unknown"},
  "size_m": {"min": [0.9, 0.9, 0.9], "max": [1.1, 1.1, 1.1]},
  "animations": [], "collision": "convex"
}
```

Record actual creator metadata when known. Units are meters. Blender uses Z-up;
export converts to Godot Y-up. The size range is measured on final Godot axes.
Recipes create meshes/armatures/materials/clips; the shared driver owns export,
blend snapshot and three previews. Declare imported helpers/external images.

Run mesh-build.sh --spec art/prompts/crate.json. The validator independently
reads the GLB's binary vertex/index data, node transforms, clip names and embedded
textures. It checks real bounds, normals, triangle/material/bone/texture limits,
required animation clips, import collision suffixes and provenance. Unsupported
required glTF extensions fail explicitly. It does not infer artistic quality,
perfect rig deformation or usable collision from a metadata flag.

Production records under art/builds/ bind exact artifact bytes, recipe/dependency
hashes, frozen spec, Blender version, frozen profile and reference-sheet hash.
Commit these records together with GLBs/provenance. Source changes require a
rebuild; attempts and previous artifacts are retained. Image dependencies use
image-register.sh --image ... --prompt ... --provider ... --model ...; supplied
images may record provider=user, model=not-applicable with an origin note.

The integrator must test Godot's actual import, collision shapes, materials and
animation wiring, using wrapper scenes so reimport does not discard gameplay.
[Godot recommends glTF/GLB for Blender interchange](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html).

## Executable gates and honest coverage

The frozen pipeline/qa-contract.json names required behavioral checks for smoke,
movement, combat, enemies, route, restart, UI, visual and performance scenarios.
Network selections add real two-process peer/authority/reconnect requirements.

fps-godot.sh --init-harness installs four host scripts without overwriting existing
game harnesses. The model supplies RefCounted suites and replay logic, scenario
scenes, and manifests under game/tests/. Read the generated contract-3d.md for
their exact APIs. Empty suites, missing scenarios, absent observations, duplicate
checks, wrong run ids, malformed JSON and unsuccessful processes fail.

Visual/UI/performance runs use an actual rendering window. The host records
fresh PNGs, measures frame times after 60 warmup frames, and reports GPU/OS.
Default performance criteria at 1280x720 are at least 120 measured frames,
55 average FPS and 25 ms p95 frame time. Agree hardware and workload before
changing these project-local values; they are not universal hardware guarantees.
The host does not automate subjective mouse feel, audio quality or visual taste.

runner-godot.sh --export builds a fresh package and runs the actual exported
executable with a unique smoke id. Install export_bridge.gd as GPExportQA autoload
and implement the normal main scene's gp_run(context) smoke hook. Missing hooks
fail. Export templates must be installed. The whole package, including any PCK
or runtime DLLs, is delivered together; previous files are retained.

All new gate processes have deadlines; logs are preserved. Missing tools report
structured error_kind rather than pass. GODOT_BIN, BLENDER_BIN and GP_PYTHON pin
executables. doctor.sh reports versions; optional pipeline/toolchain.json pins
the exact first version lines for subsequent checks.

## Upgrades and scope

--force upgrades the same preset/genre/network. Switching these in place is
rejected before writes because existing memory, frozen art and scripts could
contradict the new contract. Use a fresh directory for a deliberate migration.
Newly generated files are staged and prior runtime files archived. State, boards,
custom root instructions, frozen art and QA settings remain preserved.

No baseline game, paired model experiment or automatic comparison is generated.
The user compares new assisted builds to existing games manually. The pipeline
improves structure and feedback; passing technical gates does not guarantee a
commercial game's content scale, artistic quality or multiplayer robustness.
