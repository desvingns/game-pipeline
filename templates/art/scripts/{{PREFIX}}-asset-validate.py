#!/usr/bin/env python3
"""Deterministic asset gate: measure one image against its style profile.

Invoked by the bash wrapper of the same name, which owns the JSON-line contract.
This module never prints prose and never raises out to the caller: every failure
becomes a structured result, because a gate that crashes is indistinguishable
from a gate that was never run.

Design note. The checks here are deliberately blunt and measurable — alpha
hygiene, colour count, palette distance, contour presence and width, grid
discipline, provenance. They do not judge whether the art is good; that is the
art director's multimodal review. Splitting the two is the whole point: the
cheap deterministic pass rejects the obviously broken so the expensive
multimodal pass only ever sees plausible candidates.
"""

import argparse
import hashlib
import json
import math
import os
import sys
from gp_art_contract import check_provenance

REQUIRED_PROVENANCE_KEYS = (
    "provenance_version", "asset_id", "prompt_spec_path", "prompt_spec_sha256",
    "provider", "model", "created_utc", "style_profile", "reference_sheet_sha256",
)


def _fail(error_kind, message, extra=None):
    out = {"pass": False, "error_kind": error_kind, "errors": [message],
           "warnings": [], "checks": {}}
    if extra:
        out.update(extra)
    print(json.dumps(out, separators=(",", ":")))
    sys.exit(0)


def deep_merge(base, overrides):
    """Tier overrides patch the profile rules one level deep, by design.

    A tier says "key art may use 96 colours", not "key art redefines every rule",
    so a shallow-per-section merge is the honest semantics and keeps the profile
    files readable.
    """
    merged = json.loads(json.dumps(base))
    for section, patch in (overrides or {}).items():
        if isinstance(patch, dict) and isinstance(merged.get(section), dict):
            merged[section].update(patch)
        else:
            merged[section] = patch
    return merged


def luminance(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def load_palette(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    raw = data.get("colors", data) if isinstance(data, dict) else data
    out = []
    for item in raw:
        value = item.get("hex") if isinstance(item, dict) else item
        if not isinstance(value, str):
            continue
        value = value.lstrip("#")
        if len(value) == 6:
            out.append(tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)))
    return out or None


def erode(mask, steps, ImageFilter):
    """Erode a binary mask by `steps` pixels using repeated 3x3 min filters.

    Pillow has no morphology primitive that is guaranteed present across
    versions; MinFilter(3) is exactly a one-pixel erosion and has been stable
    for a decade, so repeating it is the portable choice.
    """
    out = mask
    for _ in range(steps):
        out = out.filter(ImageFilter.MinFilter(3))
    return out


def analyse_outline(img, mask, rules, scale, ImageFilter):
    """Measure the dark contour just inside the alpha edge.

    Returns (edge_coverage, estimated_width_px). edge_coverage is the fraction of
    the outermost one-pixel ring that is darker than the profile's threshold —
    a contour that only covers part of the silhouette is a generation artefact,
    not a style.
    """
    max_lum = rules.get("max_luminance", 96)
    probe_limit = max(2, int(math.ceil(rules.get("max_width_px", 6) * scale)) + 2)
    gray = img.convert("L")
    gpx = gray.load()

    rings = []
    prev = mask
    for depth in range(1, probe_limit + 1):
        inner = erode(prev, 1, ImageFilter)
        ring_px, dark_px = 0, 0
        prev_px, inner_px = prev.load(), inner.load()
        w, h = mask.size
        step = 1 if w * h <= 512 * 512 else 2  # subsample large canvases; ratios are stable
        for y in range(0, h, step):
            for x in range(0, w, step):
                if prev_px[x, y] and not inner_px[x, y]:
                    ring_px += 1
                    if gpx[x, y] <= max_lum:
                        dark_px += 1
        rings.append((dark_px / ring_px) if ring_px else 0.0)
        prev = inner

    coverage = rings[0] if rings else 0.0
    width = 0
    for ratio in rings:
        if ratio >= 0.5:
            width += 1
        else:
            break
    return coverage, width


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--tier", default="B", choices=["A", "B"])
    ap.add_argument("--palette", default="")
    ap.add_argument("--provenance", default="")
    args = ap.parse_args()

    try:
        from PIL import Image, ImageFilter
    except ImportError:
        _fail("pillow_missing", "Pillow is not importable by this interpreter.")

    if not os.path.isfile(args.image):
        _fail("image_missing", "No such image: %s" % args.image)
    try:
        with open(args.profile, "r", encoding="utf-8") as fh:
            profile = json.load(fh)
    except (OSError, ValueError) as exc:
        _fail("profile_unreadable", "Cannot read style profile: %s" % exc)

    tier = profile.get("tiers", {}).get(args.tier, {})
    rules = deep_merge(profile.get("rules", {}), tier.get("overrides"))

    try:
        img = Image.open(args.image)
        img.load()
    except Exception as exc:  # Pillow raises a wide family here
        _fail("image_unreadable", "Cannot open image: %s" % exc)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    w, h = img.size
    checks, errors, warnings = {}, [], []

    # ---- geometry -------------------------------------------------------
    geo = rules.get("geometry", {})
    max_side, min_side = max(w, h), min(w, h)
    checks["size"] = "%dx%d" % (w, h)

    lo, hi = tier.get("min_side_px"), tier.get("max_side_px")
    if lo and max_side < lo:
        errors.append("tier %s expects at least %dpx on the long side, got %d" % (args.tier, lo, max_side))
    if hi and max_side > hi:
        errors.append("tier %s expects at most %dpx on the long side, got %d" % (args.tier, hi, max_side))

    multiple = geo.get("size_multiple")
    if multiple and (w % multiple or h % multiple):
        errors.append("dimensions must be multiples of %d (atlas packing and pivot maths depend on it)" % multiple)

    max_ar = geo.get("max_aspect_ratio")
    if max_ar and min_side and (max_side / min_side) > max_ar:
        errors.append("aspect ratio %.2f exceeds %.2f" % (max_side / min_side, max_ar))

    # ---- alpha ----------------------------------------------------------
    alpha_rules = rules.get("alpha", {})
    alpha = img.getchannel("A")
    hist = alpha.histogram()
    total = w * h
    opaque = sum(hist[250:])
    semi = sum(hist[8:250])
    transparent = sum(hist[:8])

    checks["opaque_ratio"] = round(opaque / total, 4)
    checks["semi_transparent_ratio"] = round(semi / total, 4)
    if opaque + semi == 0:
        errors.append("image is entirely transparent; no visible asset was produced")

    if alpha_rules.get("required") and transparent == 0:
        errors.append("no transparent pixels at all — the background was not removed")
    if alpha_rules.get("background_must_be_transparent"):
        corners = [alpha.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        if any(c > 8 for c in corners):
            errors.append("canvas corners are not transparent (corner alphas: %s)" % corners)
    cap = alpha_rules.get("max_semi_transparent_ratio")
    if cap is not None and (semi / total) > cap:
        errors.append("semi-transparent pixels %.1f%% exceed %.1f%% — soft or haloed edges"
                      % (100 * semi / total, 100 * cap))
    cap = alpha_rules.get("max_opaque_area_ratio")
    if cap is not None and (opaque / total) > cap:
        errors.append("opaque area %.1f%% exceeds %.1f%% — the asset has no margin or the background is baked in"
                      % (100 * opaque / total, 100 * cap))

    # ---- colours --------------------------------------------------------
    color_rules = rules.get("colors", {})
    bits = int(color_rules.get("quantise_bits", 5))
    shift = max(0, 8 - bits)
    lut = [(i >> shift) << shift for i in range(256)] * 3
    rgb = img.convert("RGB").point(lut)
    # Count only pixels the player actually sees.
    opaque_mask = alpha.point(lambda a: 255 if a >= 250 else 0)
    counts = {}
    packed = rgb.getcolors(maxcolors=1 << 24) or []
    if opaque < total:
        rgb_masked = Image.composite(rgb, Image.new("RGB", img.size, (1, 2, 3)), opaque_mask)
        packed = rgb_masked.getcolors(maxcolors=1 << 24) or []
        packed = [(n, c) for n, c in packed if c != (1, 2, 3)]
    for n, c in packed:
        counts[c] = counts.get(c, 0) + n

    distinct = len(counts)
    checks["distinct_colors"] = distinct
    cap = color_rules.get("max_distinct_after_quantise")
    if cap is not None and distinct > cap:
        errors.append("%d distinct colours after %d-bit quantisation exceed %d — the fills are not flat"
                      % (distinct, bits, cap))

    try:
        palette = load_palette(args.palette)
    except (ValueError, TypeError):
        palette = None
    mode = color_rules.get("palette_mode", "advisory")
    if palette and mode != "off":
        opaque_total = sum(counts.values()) or 1
        worst, worst_color = 0.0, None
        for color, n in counts.items():
            if n / opaque_total < 0.005:      # ignore anti-aliasing crumbs
                continue
            d = min(math.dist(color, p) for p in palette)
            if d > worst:
                worst, worst_color = d, color
        checks["max_palette_distance"] = round(worst, 1)
        limit = color_rules.get("max_palette_distance")
        if limit is not None and worst > limit:
            msg = ("colour #%02x%02x%02x is %.1f away from the locked palette (limit %.1f)"
                   % (worst_color[0], worst_color[1], worst_color[2], worst, limit))
            (errors if mode == "locked" else warnings).append(msg)
    elif mode == "locked":
        errors.append("palette_mode is 'locked' but no valid palette file was supplied")

    # ---- outline --------------------------------------------------------
    outline_rules = rules.get("outline", {})
    mask = alpha.point(lambda a: 255 if a >= 128 else 0)
    scale = max(1.0, max_side / float(outline_rules.get("width_measured_at_px", 128)))

    if outline_rules.get("required") or outline_rules.get("forbidden"):
        coverage, width = analyse_outline(img, mask, outline_rules, scale, ImageFilter)
        checks["outline_edge_coverage"] = round(coverage, 3)
        checks["outline_width_px"] = width

        if outline_rules.get("required"):
            need = outline_rules.get("min_edge_coverage", 0.7)
            if coverage < need:
                errors.append("dark contour covers only %.0f%% of the silhouette edge (need %.0f%%)"
                              % (100 * coverage, 100 * need))
            wmin = int(round(outline_rules.get("min_width_px", 2) * scale))
            wmax = int(round(outline_rules.get("max_width_px", 6) * scale))
            if width < wmin or width > wmax:
                errors.append("contour width %dpx is outside %d-%dpx expected at this canvas size"
                              % (width, wmin, wmax))
        if outline_rules.get("forbidden"):
            cap = outline_rules.get("max_edge_dark_coverage", 0.2)
            if coverage > cap:
                errors.append("this profile forbids a contour, but %.0f%% of the edge is dark"
                              % (100 * coverage))

    # ---- pixel grid -----------------------------------------------------
    grid = geo.get("pixel_grid") or {}
    if grid.get("required"):
        native = int(grid.get("native_px", 32))
        if max_side % native:
            errors.append("long side %d is not a whole multiple of the %dpx native grid" % (max_side, native))
        else:
            factor = max_side // native
            if factor > 1:
                small = img.resize((w // factor, h // factor), Image.NEAREST)
                back = small.resize((w, h), Image.NEAREST)
                diff = sum(abs(a - b) for a, b in zip(img.convert("RGB").tobytes(), back.convert("RGB").tobytes()))
                per_px = diff / float(w * h * 3)
                checks["grid_residual"] = round(per_px, 2)
                if per_px > 2.0:
                    errors.append("image does not survive a nearest-neighbour round trip to its %dpx grid "
                                  "(residual %.1f) — the pixel grid drifted during generation" % (native, per_px))

    # ---- provenance -----------------------------------------------------
    if rules.get("provenance", {}).get("required", True):
        prov_path = args.provenance or (os.path.splitext(args.image)[0] + ".provenance.json")
        checks["provenance_path"] = prov_path
        if not os.path.isfile(prov_path):
            errors.append("no provenance record at %s — an asset nobody can regenerate is not an asset" % prov_path)
        else:
            try:
                with open(prov_path, "r", encoding="utf-8") as fh:
                    prov = json.load(fh)
                check_provenance(prov, profile.get("id"))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append("invalid provenance: %s" % exc)

    with open(args.image, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()

    print(json.dumps({
        "pass": not errors,
        "asset": os.path.basename(args.image),
        "sha256": digest,
        "profile": profile.get("id"),
        "tier": args.tier,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
