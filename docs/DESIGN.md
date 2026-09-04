# game-pipeline (gp) — design draft v0

Status: historical founding draft, 2026-09-04. The 3D expansion and current
dimension-specific architecture are specified in `docs/3D-WINDOWS.md`.
Tools: Claude Code + Codex CLI (dual-tool from day one).

## 1. What this is

`game-pipeline` (gp) is a **generator**, not a game — the same shape as `claude-mobile-pipeline`
(cmp). `bootstrap.sh` renders a template tree into a ready-to-use agent pipeline inside a
**separate repository per game**. The thing edited here is the template system.

Target: 2D mobile games for Android, built AI-first — the human writes/approves specs and judges
the result; agents produce design, code, art, animation, and run the gates.

## 2. Scope, and what gp is deliberately not

gp covers **games**. Its sibling generator
[`claude-mobile-pipeline`](https://github.com/desvingns/mobile-pipeline) covers mobile
**applications**, and gp vendored its framework — the render engine, the bootstrap skeleton, the
`.ai/` protocol, the spec board, the change-log with a cursor — then diverged. Improvements to the
shared framework are worth considering on both sides; the domain layers stay separate, and porting
copies *semantics*, never syntax.

What gp is not: a game engine (that is Godot's job), a runtime library, or a template for one
specific game. It generates the pipeline; the game lives in its own repository.

## 3. Decisions taken (with rationale)

- **D1 — Engine: Godot 4 + GDScript.** Chosen on one criterion: how completely the project is
  representable as text and buildable headless from CLI. Godot's `.tscn` / `.tres` /
  `project.godot` are readable text an agent edits directly and a human reviews as a diff;
  `godot --headless --export-release` produces an APK with no license activation; gdUnit4 runs in
  CI; MIT, no royalties. Unity was rejected because its editor is a partial source of truth: an LLM
  writes C# well but cannot wire inspector references without editor scripts, and prefab/scene YAML
  merges badly. GDScript over C# in Godot: less boilerplate per agent iteration, simpler Android
  export.
- **D2 — Separate repository.** cmp's `templates/common/` is saturated with "mobile app, Clean
  Architecture, Gradle, screens". Game work needs different agents and different gates. gp vendors
  cmp's framework once (`lib/render.sh`, `bootstrap.sh` skeleton, `.ai/` protocol, spec board,
  change-log + cursor) and then diverges.
- **D3 — Simulation in logical coordinates, rendering as a separate layer.** Projection becomes a
  render concern, determinism gates stay possible, and the isometric question stops being
  load-bearing for game logic.
- **D4 — Default projection: 3/4 top-down (Kingdom Rush family), not true 2:1 isometry.** At 3/4 an
  enemy needs one facing plus a mirror; true isometry needs 4-8 facings, each separately animated.
  The projection profile therefore drives the size of the art backlog.
- **D5 — Art style family: cel-shaded cartoon with a heavy outline ("vector look"), raster.** The
  reference that anchored this decision (a mobile TD splash screen in the Kingdom Rush lineage) is
  this — not painterly, and not pixel art.
  Real SVG is rejected: models do not emit clean SVG at this complexity, and Godot rasterises SVG
  on import anyway.
- **D6 — Animation: skeletal 2D (Skeleton2D + AnimationPlayer) plus tweens and procedural juice.**
  Motion is then *text* the agent writes and reviews as code. Frame-by-frame spritesheets are
  rejected: AI cannot hold consistency across frames, and the result is a binary asset no diff can
  review. D5 and D6 reinforce each other — an outline hides the seam at every joint.
- **D7 — Style and setting are produced by the spec phase, not fixed by the pipeline.** Each game
  repo derives its own. Two intake modes, mirroring `/mp-spec`'s greenfield/clone duality:
  `--guided` (user supplies references, agent returns its reading plus trial key frames) and
  `--auto` (model invents setting and style, human only gates).
- **D8 — Art providers are thin adapters behind one provider-neutral `prompt-spec`.** Policy:
  Claude sessions use Gemini / Nano Banana; Codex sessions use OpenAI imagery. The prompting agent
  knows neither. Swapping a model touches one script; A/B of two providers on one prompt-spec is
  free.

## 4. Two-tier art detail

A splash screen is not a gameplay asset. The style bible carries two tiers and never mixes them:

- **tier A (key art)** — splash, icon, store promo. A handful of assets, heavily iterated.
- **tier B (gameplay)** — towers, enemies, tiles, UI. Hundreds of assets. Hard constraints: outline
  3-4 px at 128 px, at most 4 tones per object, silhouette readable in black and white.

Generating tier-B assets from tier-A prompts is the classic failure: beautiful in the folder,
unreadable on the battlefield.

## 5. Style profiles — why style cannot be free-form prose

The `asset` gate is **a function of the style**. Pixel art needs grid snapping and palette
quantisation; cel-shaded needs a dark outline along the alpha edge; painterly is barely
machine-checkable at all. If `--auto` invents a style as a paragraph of prose, the gate has nothing
to enforce and every asset falls back to human review — defeating the purpose.

Therefore gp ships a **catalogue of style profiles**, each a pair of *prompt skeleton* + *machine
rules*:

| Profile | Machine rules (sketch) |
|---|---|
| `cel-shaded-outline` | dark outline present along alpha edge, width within range; <= N tones per object; palette distance to locked palette; clean alpha |
| `flat-vector` | no outline; <= N flat fills; no gradients above threshold |
| `pixel-art` | palette quantised to locked set; pixel-grid multiple; no anti-aliased edges |
| `painterly` | weak checks only — flagged as high human-review cost |

A spec **instantiates** a profile (palette, outline width in px, light direction, tiers); it does
not invent one. A genuinely new style is a separate piece of work: "add a profile", including its
validation rules.

Projection is a profile too (`top-down-34`, `iso-2to1`), and it determines how many facings each
art card demands — the backlog planner must read it rather than discover it later.

## 6. Per-game bootstrap flow

```
bootstrap  ->  /gp-spec --guided | --auto
   |- setting phase   -> concept, factions, player fantasy            [human gate]
   |- style phase     -> profile + palette + 2-4 trial key frames     [human gate: STYLE LOCK]
   |- gameplay phase  -> mechanics, economy, waves
   `- plan phase      -> ART cards (count driven by projection profile)
                         + gameplay SPECs onto the backlog board
```

**STYLE LOCK** is a hard gate. Until the reference sheet is approved, no art card enters
production. On approval the reference images are frozen into the game repo under `art/style/` and
hashed; every later generation is conditioned on them. Without freezing, a hundred assets drift,
because the model does not remember previous calls.

Consequence: unlike `/mp-spec`, the spec phase here is **not** text-only and not cheap — it makes
external image calls.

## 7. Art subsystem

```
ART card -> gp-art-prompter -> prompt-spec.json (provider-neutral)
                                     |
              scripts/gp-art-gen.sh --provider=gemini|openai|codex-native
                                     |
              assets/inbox/*.png + *.provenance.json
                                     |
              gp-asset-validator  (deterministic gate)
                                     |
              gp-art-director     (multimodal review vs style bible)
                                     |
              gp-asset-integrator -> .tres / atlas / import settings
```

**Provenance is mandatory.** Every generated PNG is accompanied by a provenance record: prompt-spec
hash, provider, model, parameters/seed where available, timestamp, reference-sheet hash. When an
image is produced inside an agent session rather than by the script, the *agent* writes the record.
The validator treats a missing provenance file as a failure, exactly like a broken alpha channel.
Rationale: "one more enemy in the same style, six months later" is impossible without it.

**Unit design rules** live in the style bible and are enforced at review, not post-processing:
joints hidden by overlap (pauldron over shoulder), parts generated as parts under one light
direction, and cloth/smoke/flags done procedurally rather than skeletally.

## 8. Agent roster

| Layer | Agents |
|---|---|
| Design | `gp-architect` (options before spec, read-only), `gp-game-designer`, `gp-level-designer`, `gp-economy` |
| Art | `gp-art-director` (style bible, multimodal review), `gp-art-prompter`, `gp-asset-integrator` |
| Code | `gp-developer-godot`, `gp-ui-godot`, `gp-animator`, `gp-vfx` |
| Verify | `gp-reviewer` (sim/render boundary), `gp-tester` (gdUnit4), `gp-runner`, `gp-playtest`, `gp-visual-reviewer`, `gp-verifier` |
| Meta | `gp-docs`, `gp-knowledge`, `gp-improve` |

Same contracts as mp/me: reviewers warn and never auto-fix; deterministic scripts emit exactly one
JSON line; agents return exactly one structured payload.

## 9. Gates

1. **build** — `godot --headless --import`, then APK export.
2. **test** — gdUnit4 headless.
3. **sim** — N waves replayed from a seed, hash stable.
4. **balance** — win rate per wave inside a defined corridor, auto report.
5. **asset** — alpha edges, size, palette distance, profile-specific rules, pivot, provenance.
6. **perf** — FPS / draw calls / texture budget on a real device.
7. **visual** — headless screenshot plus multimodal comparison against the style bible.

Gates 3-5 are what make AI-first realistic: without them every iteration is reviewed by eye, which
is the cost the pipeline exists to remove.

## 10. Benchmark track

Superseded 2026-09-04: the user compares new pipeline-assisted builds to existing
baseline games manually. No paired experiment, second implementation or --bench
workflow is part of gp. The paragraph below records the original proposal only.

`/gp --bench <model>`: one identical prompt ("build a TD"), run through the same gates. Objective
score = gate results; subjective score = the human. Reuses an existing model-benchmark harness
rather than inventing a new rubric.

## 11. First milestone — art vertical slice

Deliberately not the pipeline skeleton. The riskiest assumption is that a consistent cel-shaded
style is reproducible across separately generated parts; prove it on one asset before building the
agent roster around it.

1. Instantiate `cel-shaded-outline`: palette, outline width, light direction, both detail tiers.
2. Generate one tower at tier A and tier B.
3. Run a first cut of the asset validator over both.
4. Generate the tower as separate parts (base, turret, barrel) under one light.
5. Assemble Skeleton2D + an AnimationPlayer track for aim and recoil.
6. Put it in a Godot scene, headless screenshot, eyeball the result.

Exit criterion: parts generated in independent calls read as one object, and the validator's rules
actually discriminate good assets from bad ones.

## 12. Open questions

- **OpenAI image access.** The user reports Codex generates images in-session without API keys;
  this is unverified and must not become load-bearing until demonstrated. Fallbacks: a separate
  OpenAI API key, manual web generation dropped into `assets/inbox/`, or letting Codex use the
  Gemini key.
- **Monetisation** — undecided. Designed as a detachable layer so it does not constrain engine or
  architecture choices now.
- **Setting** — per-game, produced by the spec phase (D7).
- **Audio** — not yet discussed. Likely a later profile + gate, the same shape as art.
