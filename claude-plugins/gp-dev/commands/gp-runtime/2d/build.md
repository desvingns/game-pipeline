<!-- gp-runtime-contracts: startup -->

# --build — complete the user's game brief

This mode coordinates a whole game across staged board items. It is an exception
to the single-item scope of feature/art modes. Load each child runbook only when
needed; do not bulk-load every role. Preserve progress in STATE.md and boards
so continuation resumes the next unfinished item.

1. Read the brief and current project. Record required gameplay, visual direction,
   input, platform, duration/content scope and acceptance criteria in docs/BRIEF.md.
   Use the user's references for the intended experience, not as a demand to
   copy proprietary assets. Resolve meaningful ambiguity; infer routine details.
2. Establish tools and target hardware. Record actual versions; retain environment
   failures. Propose the smallest playable slice, followed by the brief's remaining
   scope. Existing approval covers implementation inside that scope.
3. Run design and level planning. Establish the production input/gameplay boundary
   and observable acceptance checks. Create SPECs and ART cards in dependency order.
4. Establish style using --style. Present real references for human STYLE LOCK;
   production waits until they are approved. While waiting, independent domain
   logic, tests and non-production blockout work may proceed if authorized.
5. Implement the slice through feature/art/animate runbooks, with independent
   review and tests where delegation is available. Preserve the user's scope:
   a slice is an integration checkpoint, not an excuse to omit the rest of the game.
6. Iterate remaining content and polish: readable UI, settings, animations, audio
   and visual feedback, progression/objectives, death/restart and performance.
   Use the running game and screenshots to find actual problems. Keep production
   assets consistent with the approved style; do not ship blockout substitutes.
7. Run required gates and inspect visual/control/audio quality. Repair defects
   inside scope. Never weaken checks or invent passing evidence. If a tool or
   required approval blocks progress, record precise evidence and the next action.
8. Export the requested platform package, test the delivered artifact and provide
   its path, controls, results and known limits. Update state and append history.


The selected path is 2D/Android. Use the sim replay/balance, raster asset and
rendering gates; finish with APK export and device verification when available.


There is no mandatory paired experiment, second implementation or baseline run.
Deliver one game using this pipeline. Output one BUILD DELIVERY block: BRIEF,
COMPLETED, PACKAGE, CONTROLS, GATES, VISUAL_REVIEW, KNOWN_LIMITS, NEXT.
