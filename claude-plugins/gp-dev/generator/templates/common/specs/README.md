# SPEC board — {{PROJECT_NAME}}

Two boards, deliberately separate.

```
{{AGENT_DIR}}/specs/{backlog,active,done}/   code work, consumed by /{{PREFIX}} --feature
art/cards/{backlog,active,done}/             art work,  consumed by /{{PREFIX}} --art
```

They are separate because they fail differently and are reviewed differently. A
code SPEC is done when the gates pass; an ART card is done when a human agrees it
looks right. Mixing them into one board produces runs that cannot be reviewed as
one thing.

## SPEC file

One file per unit of work, named `<id>-<slug>.md`.

```markdown
# SPEC-042 — frost tower slows enemies in radius

GOAL: <one sentence in player-visible terms>
LAYERS: sim, content
BEHAVIOUR:
- A frost tower applies a slow of X% for Y ticks to every enemy within radius R.
- Slows from multiple towers do not stack; the strongest wins.
CONTENT: content/towers/frost.json
ART: ART-018 (tower body), ART-019 (projectile)
DETERMINISM: slow is an integer tick counter on the enemy, applied in tower id order.
OUT_OF_SCOPE: upgrade tiers, the freeze visual effect
DONE_WHEN:
- A test proves the slow applies and expires at the right tick.
- The replay gate passes with the tower present.
```

## ART card

```markdown
# ART-018 — frost tower body, tier B

ASSET_ID: tower_frost_base
TYPE: tower
TIER: B
PART: base
FACING: south
WHAT: <what it must communicate at a glance, in one sentence>
MUST_MATCH: <which reference-sheet frames anchor it>
NOTES: <the joint overlap this part is responsible for, if any>
```

## Rules

- One item moves to `active/` at a time, per board.
- Nothing enters `done/` without its gate evidence.
- Work discovered mid-run becomes a new card. It never joins the run in progress.
- An ART card filed by a design or feature run is not produced by that run. Filing
  is the deliverable.
