# Unified backlog execution

Version 1.0 uses **SPECS/** for every game and both Codex and Claude Code.
The Markdown board remains the source of truth; `.ai/gp/` contains execution
records, reservations and disposable/rebuildable research results, not another board.

## Start and adopt

Use `$gp-dev` in Codex or `/gp` in Claude Code, then the generated project prefix.
Natural language such as “implement the next ready backlog task” selects
`--feature --next`. Other selectors: `--spec ID`, `--track H`, `--preview`,
`--status`, `--doctor`, `--resume RUN`, `--metrics`. One task is the default;
`--batch N` is an explicitly requested bounded sequence and respects project gates.

Codex also supports `--feature --next --chain`: after each verified DONE, it
opens a fresh Codex task in the same saved project with an empty transcript and
repeats the command. The chain stops at an empty or not-ready board, a human gate,
REVIEW/BLOCKED/FAILED result, or unavailable task creation. It is sequential and
does not replace the bounded `--batch` contract. Claude Code reports that this
modifier is unsupported because it selects its own native runtime.

Connect an existing game from its directory:

```bash
bash /path/to/game-pipeline/bootstrap.sh --adopt --dry-run --tool=codex \
  --prefix=gt --project-name='Existing Game' --package=com.example.game
bash /path/to/game-pipeline/bootstrap.sh --adopt --tool=codex \
  --prefix=gt --project-name='Existing Game' --package=com.example.game
```

Use `--tool=claude` for the other adapter. Existing game code, root instructions,
SPECS, state, memory, art and project configuration are preserved. The generated
`pipeline/project.json` describes detected paths; inspect/register actual gate
commands before executing a task. Detection lists candidate verification scripts;
it does not claim an unexecuted test passed or force a gdUnit4 migration.

Use `--adopt --preview` to render an archived candidate and inspect its file diff
without deploying it. `--dry-run` prints the installation outline without writes.
Upgrades archive replaced pipeline files and preserve project configuration.

If SPECS is absent, the skill **first delegates backlog discovery**. In Codex that
agent is Luna xhigh. Claude uses its simple tier (Sonnet 5 / medium). It searches only the
current project, inspects candidate cards/checklists, and migrates the real backlog.
It retains original content, IDs, acceptance, status and relative links. An empty
backlog is reported explicitly. Direct bootstrap leaves the board absent until
that discovery happens; it cannot impersonate a native subagent.

The shared board supports BACKLOG, ACTIVE, BLOCKED, REVIEW and DONE. Unfinished
cards live in `SPECS/backlog/`; finished cards in `SPECS/done/`. Dependencies and
evidence determine readiness. Imported `active/` cards are recognized; the migration
preserves ACTIVE in the card while moving it to the unified backlog layout.

## Model policies

`pipeline/model-policy.json` is the single project configuration:

| Codex tier | Model | Reasoning | Examples |
|---|---|---|---|
| simple | gpt-5.6-luna | xhigh | bounded fixes, small tests, discovery, close-out text |
| complex | gpt-5.6-sol | xhigh | cross-layer features, integrations, substantive review |
| expert | gpt-6-astra | high | Blender, new algorithms/codecs, critical lifecycle/concurrency |

The recommended **Codex chat orchestrator is GPT-5.6 Sol / high**. It coordinates
bounded work without repeating each specialist's research. Select it manually in
the chat; the skill never changes the primary session model. For predominantly
novel architecture or hard debugging, Astra high is a reasonable primary choice.
Simple-task subagents retain the user's requested xhigh setting. Savings are
measured across successful completion including retries; no percentage is promised.

Claude Code has independent settings under `claude` (`mode: tiered`):

| Claude tier | Model | Effort | Examples |
|---|---|---|---|
| simple | claude-sonnet-5 | medium | bounded fixes, small tests, discovery, close-out text |
| complex | claude-sonnet-5 | xhigh | cross-layer features, integrations, substantive review |
| expert | claude-opus-5 | xhigh | Blender, new algorithms/codecs, critical lifecycle/concurrency |

Claude Code accepts a model per spawn but reads effort only from agent frontmatter.
Bootstrap therefore pins `model` and `effort` into every `.claude/agents/*.md` role
from `claude.role_tiers` (default complex; docs, runner and backlog-discovery simple;
art-prompter and animator expert), using a preserved project policy when present.
The descriptor passes the tier model and reports `reasoning_effort` as the effort that
actually applies, with `tier_reasoning_effort` and `effort_source` alongside. A simple
developer assignment therefore runs Sonnet 5 at the developer's xhigh: a deliberate
trade-off against per-tier agent copies. Reasoning checks stay strict against the
applied effort. Full model IDs are used because the `sonnet` alias resolves to older
models on Bedrock, Vertex and Foundry. Missing entries, including 1.1 `mode: auto`
policies with empty tiers, use these defaults; `mode: native` restores session-selected
models. Re-run bootstrap `--force` after editing Claude tiers. There is no GPT model
or Codex CLI bridge in Claude. The same board, roles, schemas and evidence protocol
apply to both tools.

Claude read-only roles (architect, reviewer, verifier) have only Read, Glob and Grep,
so independence is tool-enforced as in the Codex read-only sandbox; the coordinator
passes changed files, the run diff and evidence paths. `claude.max_turns` pins
`maxTurns` (runner: 8). Bootstrap merges project-scoped `.claude/settings.json` allow
rules for the installed work and gate scripts into any existing file, archiving the
previous copy. STYLE LOCK `--lock` always asks and image generation keeps the default
prompt. The rules apply after workspace trust and match only
`bash .claude/scripts/<prefix>-<name>.sh ...` invoked from the repository root.

The runtime selects per subtask, not only by profession or S/M card size. Expert
risk triggers bypass cheaper failed attempts. Review can set `review_floor`.
`failure_kind: reasoning` permits escalation; environment/tool/model unavailability
does not. Missing models are explicit blockers; no silent substitution. Default
caps: three simultaneous agents, one delegation level, three attempts per stage.
Native role TOML has sensible defaults, but explicit assignment selection wins.
`mode: inherit` is an opt-in compatibility mode; Codex backlog discovery remains
Luna xhigh. It is not the default tiered policy.

## Portable commands

In examples below, `work` means:

```bash
bash .codex/scripts/gt-work.sh --root .
# Claude: bash .claude/scripts/gt-work.sh --root .
```

Do not define a shell alias in the user's environment. Invoke the full command.
Each command produces exactly one JSON line. Failure exits nonzero with an
`error_kind`; `pass` is always the truth source. No jq dependency is required.

| Command | Purpose |
|---|---|
| `adopt [--apply]` | Preview/create detected project map without overwriting custom configuration |
| `upgrade-preview --generated DIR` | Compare an archived rendered candidate with installed files |
| `discover --tool codex` | List candidate sources for the discovery agent; no migration or model call |
| `migrate --plan FILE [--apply]` | Validate/apply a hash-bound move plan; replay interrupted journal |
| `next [--track H] [--spec H12]` | Select the next dependency-ready card |
| `--feature --next --chain` | Codex: finish one card, create a fresh task, and continue until the board stops |
| `status`, `consistency`, `sync-index` | Inspect readiness, detect inconsistencies, synchronize the index |
| `claim --spec ID --owner SESSION` | Reserve before any implementation writes |
| `claim ... --recover-stale` | Recover the same expired run, preserving its checkpoints |
| `recover-mutation --pid PID` | Archive an interrupted mutation lock only after its owner is confirmed dead |
| `checkpoint --run RUN --stage test --note TEXT` | Record progress and renew ownership |
| `resume --run RUN` | Recover stage/context and list stale/missing checks |
| `route --request FILE` | Explain model selection without spawning |
| `assign --run RUN --request FILE` | Reserve bounded file ownership and return native dispatch descriptor |
| `dispatch --assignment ID` | Re-read that descriptor without another reservation |
| `finish-assignment --assignment ID --result FILE` | Audit changes and record native results/observed usage |
| `context --request FILE` | Build a bounded, source-hashed context packet |
| `research-cache --key KEY [--request FILE]` | Store/reuse findings only when source hashes still match |
| `gates --run RUN [--final]` | Select affected checks and mandatory final regression |
| `gate --run RUN --id CHECK` | Execute an existing check and retain source-bound evidence |
| `snapshot` | Get the current source digest for completion evidence |
| `close --run RUN --status DONE --evidence FILE` | Validate acceptance/review/gates/art and close the card |
| `close --run RUN --status REVIEW --reason TEXT` | Preserve an unfinished task with a concrete remaining check |
| `doctor` | Report tool/project/gate readiness, without claiming qualification |
| `metrics`, `record-usage --request FILE` | Observed specialist/coordinator usage, retries and unknowns |
| `art-estimate --request FILE` | Count asset variants/facings/frames and declared meshes/rigs/clips |
| `validate --schema FILE --file FILE` | Validate portable workflow payloads |

Put temporary requests/results under `.ai/gp/requests/` so they do not change the
production source snapshot. Full logs belong in `docs/evidence/<SPEC>/<RUN>/`.
`dispatch` returns settings; the **host actually calls its native spawn tool**.
It does not claim a selected model ran merely because its name appears in a prompt.
Use the model and effort fields as real tool arguments. Record actual model/effort
only when observed from the host; otherwise use `unknown`, and usage `null`.

### Assignment example

```json
{
  "role": "developer",
  "tool": "codex",
  "goal": "Implement the approved bounded behavior",
  "complexity": "complex",
  "risk": {"subsystems": 2},
  "context": [
    {"path": "SPECS/backlog/TASK-1.md"},
    {"path": "DESIGN.md", "start": 30, "end": 55}
  ],
  "write_paths": ["domain/session/", "data/session/"],
  "acceptance": ["One terminal outcome per session"],
  "stage": "implement",
  "attempt": 1,
  "depth": 1
}
```

Use reviewer/verifier with empty write_paths and native read-only execution when
supported. The runtime checks changed paths but is not an OS sandbox. Independent
review must be fresh for the final source snapshot. Specialist role instructions
should be included in the selected packet along with SPEC/contracts, not replaced
by a developer's summary. Explicit ownership prevents concurrent conflicting writes.

### Existing gate adapter

Register actual commands in project.json, for example:

```json
{
  "id": "lifecycle",
  "command": ["python", "tools/lifecycle/verify.py", "--output", "{evidence}/run"],
  "result": "json-file",
  "result_path": "{evidence}/run/result.json",
  "paths": ["domain/session/*", "app/*"],
  "final": true,
  "timeout_seconds": 300
}
```

This is an example, not a verified command for any specific game. Inspect the real
script's arguments/output before registering it. `json-line` requires exactly one
JSON line; `json-file` requires a fresh declared output; `exit-code` is an explicit
adapter for existing conventional test runners. A JSON `error_kind` never passes.
Files/results/logs are hashed and retained. Source changes invalidate gate evidence.

Repositories are named in `repositories`, each with path, writable flag and pinned
version metadata. A context entry or assignment may select `repository`; gates may
select it too and use `{repository}` in argv. Only explicitly mapped independent
repositories are accessible. Their source digests participate in freshness. Keep
SDK ownership/versioning explicit; do not fork a second drifting source copy.

### Completion evidence

```json
{
  "run_id": "TASK-1-actual-run-id",
  "source_sha256": "64-character-current-snapshot-hash",
  "acceptance": [
    {"id": "AC1", "status": "pass", "evidence": "docs/evidence/TASK-1/run/check.json", "sha256": "64-character-artifact-hash"}
  ],
  "manual": [
    {"status": "pass", "performer": "actual reviewer", "platform": "actual device/runtime", "path": "docs/evidence/TASK-1/run/manual.md", "sha256": "64-character-artifact-hash"}
  ]
}
```

Use AC1..ACn in the acceptance list's order or explicit gp-meta acceptance_ids.
The illustrative hash strings above must be replaced by actual digests. All
required checks, ART dependencies, independent review and manual evidence must be
complete. REVIEW and BLOCKED require reasons; they do not masquerade as DONE.
Final close-out updates the board and execution handoff, then the host refreshes
the project's existing HANDOFF/STATE and runs consistency. Git delivery follows
the user's existing authorization. No publication or next task is implicit.

## Art, platform and authoring boundaries

`--blender-assets` adds reproducible mesh/recipe tooling to a 2D preset without
installing FPS role/world instructions. It can supply pre-render source assets;
final 2D renders still need the raster profile/provenance checks. Use the installed
stylized-3d mesh profile for mesh checks and the project's approved reference sheet.
Blender recipe authorship uses the expert model; repeated builds use scripts.
Art estimates are counts, not promised generation costs. STYLE LOCK remains a hard
human gate. Machine geometry/alpha/provenance checks complement real Godot visual,
animation, scale and collision review. Visual/audio changes must preserve pure
simulation replay where relevant.

Evaluated chapter authoring uses a frozen model/tool contract and a neutral allowlist
in an isolated repository. Production dispatch explicitly refuses to run it inside
the host workspace. The host orchestrator exports the allowed package first; it
does not leak production lore, other chapters or conversation history to the author.
No benchmark or second baseline is imposed on ordinary game development.

## Verification and limits

`bash tests/smoke.sh` tests both tools/presets, native adapter settings, generated
schemas, missing/stale evidence, discovery/migration, ownership, recovery, context,
model routing, existing gates and end-to-end completion in retained fixtures.
Real model dispatch and real Godot/Blender/device/provider runs are separate
integration evidence; scripted fixture success does not claim them. The local
runtime cannot infer Codex subscription multipliers or hidden reasoning usage.

The adoption preview against Ground Truth is read-only. Its real board
selects H12 on the H track; the game is not modified or implemented by generator
tests. The generic implementation contains no hard-coded Ground Truth paths/rules.

## Approved improvement coverage

The numbers correspond to the 60 approved proposals, with the user's two changes:
SPECS is universal, and Claude owns its native model policy.

| IDs | Implementation |
|---|---|
| 1–3 | bootstrap --adopt, shared board, router selectors and preview |
| 4–7 | dependency/evidence readiness, derived READY, status/content migration |
| 8–10 | claims/mutation lock, checkpoints/recovery, consistency/index validation |
| 11–12 | mapped repositories; one-task contract and explicitly bounded batches |
| 13–17 | policy schema, per-assignment difficulty/risk routing and expert triggers |
| 18–20 | failure classification, escalation descriptors, persistent stage attempt caps |
| 21–24 | actual-versus-requested checks, explicit unavailable path, review floor, concurrency/ownership |
| 25–29 | direct script gates, thin coordinator, bounded packets, fresh native contexts, source sections |
| 30–34 | hash-invalidated research cache, retained logs, affected/final checks, repair packets, observed usage |
| 35–39 | architecture mapping, real harness adapters, doctor, source baseline, acceptance digest |
| 40–44 | acceptance/artifact mapping, independent tester/reviewer contracts, fresh evidence, normal-entry verification, precise close states |
| 45–48 | isolated evaluated-authoring contract, allowlists, ART prerequisites, 2D Blender module |
| 49–52 | expert recipes/script execution, art counting, retained existing visual/provenance gates, replay invariance contract |
| 53–56 | shared 2D/3D feature flow, versioned schemas, Bash/Python kernel, read-only native roles and ownership audit |
| 57–60 | workflow/adoption regressions, marketplace source parity, archived upgrades preserving user state/policy |
