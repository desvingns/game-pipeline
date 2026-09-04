# 3D execution contract

Read CLAUDE.md and the selected genre.md/network.md. Frozen settings live in
pipeline/profile.json. No sprite-facing multiplier applies to 3D meshes.

## Harness API

Create game/project.godot, then run fps-godot.sh --init-harness. This preserves
existing harness files and creates empty manifests; empty manifests fail tests.

- tests/gp_suites.json: array of res:// paths to RefCounted scripts. Each defines
  run_tests() returning {assertions: positive integer, failures: Array}.
- tests/gp_replay.gd: RefCounted.replay(seed) returns nonempty pure domain state.
  Fresh processes hash its sorted JSON representation. No scene physics here.
- tests/gp_scenarios.json: object mapping scenario names to res:// scene paths.
  Each scene defines async or synchronous gp_run(context) -> {checks: Array,
  metrics: Dictionary (optional)}. Context contains seed/scenario/run_id.
- Each check has id, boolean pass, observed evidence. Required ids are listed
  in pipeline/qa-contract.json. Exercise real code, include negative cases;
  never return constants or teleport bots past geometry to satisfy a route.
- qa_host.gd measures actual rendered frame times and saves a fresh PNG for
  visual, ui and perf. Run representative combat for at least 180 frames. It
  discards the first 60 samples. Headless rendering cannot pass those gates.
- Add tools/gates/export_bridge.gd as GPExportQA autoload. The normal main scene
  implements gp_run(context) for exported smoke. The exported gate invokes the
  actual executable and checks its fresh run id; no separate dummy main scene.
- Network scenarios additionally return peers: [{pid: positive integer,
  run_id: context.run_id, log: project-relative log path}, ...] for at least two
  distinct actual processes. Each peer logs GP_PEER_READY=<run_id> after its
  production connection succeeds. Preserve peer logs; stale/missing receipts fail.

The host is a reusable test transport, not a game implementation or universal
playtest bot. The tester must implement scenarios against each game's real APIs.
All tools have a deadline (--timeout seconds). Failed, missing, stale or malformed
evidence is never converted to pass or n/a. Keep logs and review screenshots.

## Blender API

tools/blender/<id>.py defines build(spec) using bpy. Metric Z-up Blender content
exports as metric Y-up Godot GLB. Name clips/sockets and collision import suffixes.
Do not export inside the recipe: pipeline/blender/build_driver.py owns .blend,
GLB and three previews. Put imported helpers and external files in dependencies.
Use Principled BSDF material nodes for exported PBR values. Workbench viewport
diffuse colors alone do not establish exported material appearance; check Godot.
Mesh specs follow art/schemas/mesh-spec.schema.json; size_m min/max is the allowed
final Godot-axis bounding box size. Builds fail on budget/contract violations.

mesh-build.sh writes game/assets/models/<id>.glb plus provenance and retains
sources/evidence under art/builds/. Changing a recipe, dependency, profile,
reference or output invalidates the corresponding asset check. Preserve records
in version control. Generated image inputs use image-register.sh --image <file>
--prompt <text-file> --model <actual-model> --provider <actual-provider>.
Images supplied by the user may record provider=user and model=not-applicable.

Technical success still requires director review in Godot: collision shape fit,
rig deformation, animation blending, materials, silhouettes and viewmodel clipping.
