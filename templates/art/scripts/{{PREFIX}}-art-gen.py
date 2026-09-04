#!/usr/bin/env python3
"""Render one prompt-spec into a prompt, and — where the provider allows it —
into an image plus its provenance record.

Three providers, one contract:

  gemini        scripted call to the Gemini image API. Available in a Claude
                session where GEMINI_API_KEY is set.
  codex-native  Codex Desktop's built-in image_gen. It is interactive and not
                scriptable, so this script stops after rendering the prompt and
                returns it for a human to run. The agent then registers the
                returned file with --register.
  manual        any other tool. Same flow as codex-native.

What matters is that all three consume the same prompt-spec and produce the same
provenance record. The prompting agent never learns which one ran.
"""

import argparse
import base64
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_GEMINI_MODEL = os.environ.get("GP_GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def posix(path):
    """Report paths with forward slashes on every platform.

    These strings are read back by agents and pasted into later commands; a
    backslash that survives into a prompt or a shell argument on Windows is a
    quoting bug waiting to happen.
    """
    return path.replace(os.sep, "/")


def out(payload):
    print(json.dumps(payload, separators=(",", ":")))
    sys.exit(0)


def fail(kind, message, extra=None):
    payload = {"pass": False, "error_kind": kind, "errors": [message]}
    if extra:
        payload.update(extra)
    out(payload)


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def render_prompt(spec):
    """Flatten the spec into the linear prompt every image model actually wants.

    Section order is not arbitrary: subject first (models weight early tokens
    most), style and lighting next because they are what drifts between assets,
    hard constraints last where they act as a checklist, and the negatives in
    their own block.
    """
    parts = []
    if spec.get("primary_request"):
        parts.append(spec["primary_request"])
    parts.append("Subject: %s" % spec["subject"])
    if spec.get("part"):
        parts.append("This is one detachable part of a larger unit: %s. It must line up with the "
                     "other parts of the same unit and share their light direction exactly." % spec["part"])
    if spec.get("scene"):
        parts.append("Scene: %s" % spec["scene"])
    parts.append("Style: %s" % spec["style_medium"])
    if spec.get("composition"):
        parts.append("Composition: %s" % spec["composition"])
    if spec.get("lighting"):
        parts.append("Lighting: %s" % spec["lighting"])

    palette = spec.get("palette") or {}
    if palette.get("emphasis"):
        parts.append("Palette: lead with %s." % ", ".join(palette["emphasis"]))
    if spec.get("text"):
        parts.append("Render this text exactly: %s" % spec["text"])

    canvas = spec["canvas"]
    parts.append("Canvas: %dx%d pixels, %s background."
                 % (canvas["width"], canvas["height"], canvas["background"]))
    if canvas.get("margin_pct"):
        parts.append("Leave a %g%% margin on every side." % canvas["margin_pct"])

    parts.append("Requirements: " + "; ".join(spec["constraints"]) + ".")
    parts.append("Do not include: " + "; ".join(spec["avoid"]) + ".")
    return "\n".join(parts)


def write_provenance(path, spec, spec_path, provider, model, params, sheet_hash, operator, attempt):
    record = {
        "provenance_version": 1,
        "asset_id": spec["id"],
        "prompt_spec_path": spec_path,
        "prompt_spec_sha256": sha256_file(spec_path),
        "provider": provider,
        "model": model,
        "parameters": params,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "style_profile": spec["style_profile"],
        "reference_sheet_sha256": sheet_hash,
        "operator": operator,
        "attempt": attempt,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")
    return record


def read_sheet_hash(manifest_path):
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            return json.load(fh).get("sheet_sha256")
    except (OSError, ValueError):
        return None


def call_gemini(prompt, spec, api_key, model):
    """One request, one image. Reference images ride along as inline parts.

    Conditioning on the frozen reference sheet is the single most important
    thing this function does — without it every call is an independent roll and
    the asset set drifts apart.
    """
    parts = [{"text": prompt}]
    for ref in spec.get("reference_images", []):
        if not os.path.isfile(ref):
            return None, "reference image not found: %s" % ref
        ext = os.path.splitext(ref)[1].lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".webp": "image/webp"}.get(ext, "image/png")
        with open(ref, "rb") as fh:
            parts.append({"inline_data": {"mime_type": mime,
                                          "data": base64.b64encode(fh.read()).decode("ascii")}})

    body = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")
    req = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model),
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        return None, "HTTP %s from the image API: %s" % (exc.code, detail)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return None, "image API call failed: %s" % exc

    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            blob = part.get("inline_data") or part.get("inlineData")
            if blob and blob.get("data"):
                return base64.b64decode(blob["data"]), None
    return None, "the response contained no image part (model=%s)" % model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--provider", default="gemini", choices=["gemini", "codex-native", "manual"])
    ap.add_argument("--out-dir", default="assets/inbox")
    ap.add_argument("--sheet-manifest", default="art/style/reference-manifest.json")
    ap.add_argument("--operator", default="claude-code")
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--render-only", action="store_true",
                    help="Print the rendered prompt and stop, whatever the provider.")
    ap.add_argument("--register", default="",
                    help="Path to an image produced elsewhere; writes its provenance and moves it into place.")
    args = ap.parse_args()

    try:
        with open(args.spec, "r", encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as exc:
        fail("spec_unreadable", "cannot read prompt-spec: %s" % exc)

    for key in ("id", "style_profile", "subject", "style_medium", "canvas", "constraints", "avoid"):
        if key not in spec:
            fail("spec_invalid", "prompt-spec is missing required field: %s" % key)

    prompt = render_prompt(spec)
    sheet_hash = read_sheet_hash(args.sheet_manifest)
    if not sheet_hash and spec.get("asset_type") != "reference_sheet":
        fail("not_style_locked",
             "no locked reference sheet at %s — production assets may not be generated before STYLE LOCK"
             % args.sheet_manifest)

    os.makedirs(args.out_dir, exist_ok=True)
    image_path = posix(os.path.join(args.out_dir, spec["id"] + ".png"))
    prov_path = posix(os.path.join(args.out_dir, spec["id"] + ".provenance.json"))

    # ---- registering an image produced outside this script -----------------
    if args.register:
        if not os.path.isfile(args.register):
            fail("register_missing", "no such file: %s" % args.register)
        if os.path.abspath(args.register) != os.path.abspath(image_path):
            with open(args.register, "rb") as src, open(image_path, "wb") as dst:
                dst.write(src.read())
        write_provenance(prov_path, spec, args.spec, args.provider,
                         os.environ.get("GP_IMAGE_MODEL", "unknown"), {"registered_from": args.register},
                         sheet_hash or "", args.operator, args.attempt)
        out({"pass": True, "action": "registered", "image": image_path, "provenance": prov_path})

    # ---- providers that cannot be scripted --------------------------------
    if args.render_only or args.provider in ("codex-native", "manual"):
        prompt_path = posix(os.path.join(args.out_dir, spec["id"] + ".prompt.txt"))
        with open(prompt_path, "w", encoding="utf-8") as fh:
            fh.write(prompt + "\n")
        out({
            "pass": True,
            "action": "human_in_the_loop",
            "provider": args.provider,
            "prompt_file": prompt_path,
            "expected_image": image_path,
            "reference_images": spec.get("reference_images", []),
            "next_step": ("Run this prompt in %s, save the result, then re-run this script with "
                          "--register <path> to write provenance and move it into place."
                          % ("Codex Desktop image_gen" if args.provider == "codex-native" else "your image tool")),
            "prompt": prompt,
        })

    # ---- gemini -----------------------------------------------------------
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        fail("no_api_key", "GEMINI_API_KEY is not set; use --provider manual to get a prompt instead")

    model = os.environ.get("GP_GEMINI_IMAGE_MODEL", DEFAULT_GEMINI_MODEL)
    data, err = call_gemini(prompt, spec, api_key, model)
    if err:
        fail("generation_failed", err, {"model": model, "prompt_file": None})

    with open(image_path, "wb") as fh:
        fh.write(data)
    params = {"model": model}
    if spec.get("seed") is not None:
        params["seed"] = spec["seed"]
    write_provenance(prov_path, spec, args.spec, "gemini", model, params,
                     sheet_hash or "", args.operator, args.attempt)
    out({"pass": True, "action": "generated", "provider": "gemini", "model": model,
         "image": image_path, "provenance": prov_path,
         "bytes": len(data), "sha256": sha256_file(image_path)})


if __name__ == "__main__":
    main()
