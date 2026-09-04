# v0.3 validation — 2026-09-04

## Delivered scope

One generator with 2D/Android and 3D FPS/Windows presets, selectively composed
genre/network modules, whole-game orchestration, inherited role models, Blender
production/provenance, independent GLB checks, actual Godot harness transports,
rendered evidence, bounded execution and Windows artifact smoke. No baseline
game or paired model experiment was created. Personal gp-dev was updated locally.

## Automated regression coverage

`bash tests/smoke.sh` runs the original nine test groups and eight FPS groups.
Final runs passed all nine legacy and eight FPS groups. The FPS suite includes generation for both
Claude and Codex, offline and co-op composition, malformed configurations,
migration refusal before writes, marker/model filtering, native TOML parsing,
missing evidence, scenario identities, binary geometry rather than advertised
bounds, deadlines/process failures, harness preservation and fresh peer receipts.

The tests preserve all fixture projects and logs under out/. Python bytecode
caches are excluded from source overlays: importing a helper must not break the
next bootstrap. All Python sources/JSON parse and Bash scripts pass syntax checks.
The personal skill passes skill-creator quick validation and matches its source.

## Real tool integration

`tests/test_fps_integration.py` passed 18 ordered checks against:

- Godot 4.7.2.stable.official.ed1daf0bf, Windows console executable.
- Blender 5.2 (the exact version line is retained in the receipt/toolchain pin).
- Windows rendering on NVIDIA GeForce RTX 3080 Ti Laptop GPU.

Retained evidence:

- Project/receipts: `out/fps-real-0vm4bpeo/integration-results.json`.
- Exported package: `out/fps-real-0vm4bpeo/build/package/fixture.exe`.
- Blender GLB, blend source, previews and provenance: that project's art/builds/
  and game/assets/models/ directories.
- Real rendered screenshots and timings: that project's out/gp-runs/ directories.

Positive checks exercised doctor/tool pins, harness installation, synthetic test
STYLE LOCK, real Blender export, independent asset validation, Godot import,
nonempty domain assertions, replay in independent processes, normal-scene smoke,
movement against physical geometry, rendered visual/performance host behavior,
and fresh Windows export plus execution of its real main-scene smoke bridge.

Negative checks confirmed refusal of an incomplete project, missing assets,
production before STYLE LOCK, an unregistered scenario, modified GLB bytes and
modified recipe source. The final negative source-drift check intentionally
invalidated the retained fixture's recipe; receipts preserve that failure. The
repeatable test now restores the recipe after recording the negative result.

Actual image inspection caught a Workbench/export material mismatch. The test
recipe now uses Principled BSDF nodes; the production contract requires verifying
exported material appearance in Godot. A separate exported-smoke argument keeps
the autoload bridge from intercepting ordinary QA host runs.

## Limits

This is a small integration fixture, not a completed commercial FPS and not a
performance benchmark of a representative full game. Scenario hosts cannot
invent tests for a new game's API: the tester role must implement them against
the production input/world code. Network receipt validation is tested with
protocol fixtures; no real co-op/competitive game or network session was built.
Rig deformation, animation feel, audio quality, difficulty and artistic quality
still require appropriate runtime/human review. Android export/device execution
and actual Linux/macOS runners were not exercised in this turn.

Existing uncommitted v0.2 changes were preserved and extended. No commit or push
was made; the working tree contains both that earlier work and this expansion.
