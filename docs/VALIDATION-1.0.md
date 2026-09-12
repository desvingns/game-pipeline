# Version 1.0 validation

Date: 2026-09-12. Host: Windows, Git Bash, Python. Fixtures and full logs are
retained under ignored `out/`; no production game implementation was started.

The follow-up 1.1.0 marketplace change adds Codex chain mode and was validated by
the marketplace contract test and package parity check below.

Result: all 50 smoke tests passed, plus 18 real engine integration checks.
Marketplace parity matched all 290 checked source copies. The built marketplace
packages are version 1.1.0; the previously installed 1.0.0 packages remain
archived until the new version is installed and the host session is restarted.

## Coverage

- Workflow kernel: 25 tests for discovery, migration, dependencies, reservations,
  recovery, model routing, ownership, context, research freshness, mapped
  repositories, usage, real subprocess gates and evidence-bound completion.
- Existing 2D pipeline: 9 regressions across both tools, retained user files,
  rendering, art/provenance and personal installation.
- FPS pipeline: 8 regressions covering both native adapters, actual geometry,
  peer receipts, stale evidence, timeouts and malformed harness results.
- Marketplace and existing-project adoption tests validate rendered packages,
  source parity, both tools, shared SPECS and preserved architecture/configuration.
- Skill Creator validation passes for both packaged skills and the personal entry.
- Python compilation, JSON parsing and Bash syntax checks pass.

## Real integrations

Godot 4.7.2 and Blender 5.2 completed 18 integration checks, including style lock,
Blender build/provenance, mesh validation, real Godot harnesses, exported launch,
and expected rejection of missing/invalid evidence. These are generated fixtures,
not a completed FPS or proof of final game art quality.

A native GPT-5.6 Luna / xhigh subagent received an isolated legacy backlog and the
discovery role. It migrated two task cards and a supporting document to SPECS;
the subsequent consistency check passed with two BACKLOG cards and no findings.
Evidence: `out/native-discovery-validation.json` and the fixture named by
`out/native-discovery-path.txt`.

Ground Truth was inspected read-only: adoption detected the root Godot project,
Clean architecture, existing SPECS and native verification candidates. Selection
on track H returned H12. Existing game source, board and SDK were not modified.

## Corrections and limits

Regression testing caught an unrendered project-name placeholder in the newly
shared board reference. Bootstrap now renders that reference for both presets.
Independent review found migration, dependency and recovery edge cases; fixes
were incorporated into regressions. The reviewer's final follow-up hit its host
usage limit, so it does not count as a completed final independent approval.

Live Claude model selection, complete native multi-agent feature implementation,
Android device execution and live image-provider generation were not exercised
in this release validation. Claude's native policy remains intentionally editable.
No subscription savings percentage, hidden usage or API cost is asserted.

Chain-mode validation confirms the Codex marketplace skill and runtime contain
`create_thread` and the empty-transcript successor contract, while Claude's
rendered package contains only `chain_unsupported_in_claude`. The 1.1.0 full smoke
run is recorded in `out/smoke-chain-v110.log`.

Final regression output: `out/smoke-v1-final.log`. Real engine output:
`out/real-integration-validation.log`; retained scene/build artifacts are named
in `out/latest-fps-real.txt`.
