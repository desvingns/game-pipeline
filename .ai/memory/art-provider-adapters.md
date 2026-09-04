---
name: art-provider-adapters
description: One provider-neutral prompt-spec, three providers, one provenance record — and why placeholders are forbidden
metadata:
  type: project
---

The prompting agent writes `prompt-spec.json` and never learns which provider
runs it. Three adapters consume the same document:

- **`gemini`** — scripted, needs `GEMINI_API_KEY`. The Claude-session default.
- **`codex-native`** — Codex Desktop's `image_gen`. Interactive and not
  scriptable, so the adapter renders the prompt, stops with
  `action: human_in_the_loop`, and the agent later calls `--register <path>` with
  the file the human produced.
- **`manual`** — any other tool, same flow.

The spec's field vocabulary (use case, asset type, subject, scene, style/medium,
composition, lighting, palette, text, constraints, avoid) deliberately matches
Codex Desktop's production-prompt structure, so rendering to that target is
lossless.

**Provenance is written in all three cases**, including when a human made the
image — then the agent writes the record. Missing provenance fails the asset gate
exactly as hard as a broken alpha channel, because an asset nobody can regenerate
cannot be extended six months later.

**Never substitute a placeholder** — no SVG, no HTML mock, no coloured rectangle —
when generation is unavailable. A stand-in that enters the project is
indistinguishable from real art two weeks later and passes every gate that does
not look at it. Emit the spec and stop. Retry cap is three attempts per asset;
past that the spec or the profile is wrong. See [[style-is-enforceable]].
