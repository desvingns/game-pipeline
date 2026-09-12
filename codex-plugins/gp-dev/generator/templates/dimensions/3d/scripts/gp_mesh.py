"""Blender production and independent GLB/provenance validation (stdlib only)."""
import hashlib
import math
import os
from pathlib import Path
import shutil
import struct
import sys

from gp_3d import GateError, Parser, binary, entry, inside, read_json, run_dir, run_process, version, write_json
from gp_art_contract import verify_sheet


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec_check(spec):
    import re
    if type(spec.get("spec_version")) is not int or spec["spec_version"] != 1 or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", str(spec.get("id", ""))):
        raise GateError("spec_invalid", "Expected mesh spec_version=1 and a safe asset id")
    if spec.get("kind") not in ("prop", "kit", "weapon", "character"):
        raise GateError("spec_invalid", "Unknown mesh kind")
    source = inside(spec.get("source", ""))
    if not source.is_file() or source.suffix != ".py":
        raise GateError("spec_invalid", "source must be a project-local Blender Python recipe")
    creator = spec.get("creator", {})
    if not all(isinstance(creator.get(key), str) and creator[key].strip() for key in ("tool", "model")):
        raise GateError("spec_invalid", "Record creator.tool and creator.model; use unknown when unavailable")
    if type(spec.get("seed")) is not int:
        raise GateError("spec_invalid", "An integer seed is required")
    if not isinstance(spec.get("dependencies", []), list) or not all(isinstance(x, str) for x in spec.get("dependencies", [])):
        raise GateError("spec_invalid", "dependencies must list project-relative source files")
    if not isinstance(spec.get("animations"), list) or not all(isinstance(x, str) and x for x in spec["animations"]):
        raise GateError("spec_invalid", "animations must list required clip names (empty for static meshes)")
    bounds = spec.get("size_m", {})
    for key in ("min", "max"):
        values = bounds.get(key)
        if not isinstance(values, list) or len(values) != 3 or not all(type(x) in (float, int) and math.isfinite(x) and x >= 0 for x in values):
            raise GateError("spec_invalid", "size_m.min/max must each contain three finite nonnegative values")
    if any(lo > hi or hi <= 0 for lo, hi in zip(bounds["min"], bounds["max"])):
        raise GateError("spec_invalid", "Invalid size range")
    if spec.get("collision") not in ("none", "convex", "trimesh"):
        raise GateError("spec_invalid", "collision must be none, convex or trimesh")
    if spec["kind"] in ("weapon", "character") and spec["collision"] == "trimesh":
        raise GateError("spec_invalid", "Dynamic assets cannot use concave trimesh collision")
    return source


def identity():
    return [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]


def multiply(a, b):
    return [sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4)) for col in range(4) for row in range(4)]


def transform(node):
    if "matrix" in node:
        result = node["matrix"]
        if len(result) != 16 or not all(type(x) in (float, int) and math.isfinite(x) for x in result):
            raise ValueError("Invalid node matrix")
        return result
    x, y, z, w = node.get("rotation", [0., 0., 0., 1.])
    sx, sy, sz = node.get("scale", [1., 1., 1.])
    tx, ty, tz = node.get("translation", [0., 0., 0.])
    return [(1-2*y*y-2*z*z)*sx, (2*x*y+2*z*w)*sx, (2*x*z-2*y*w)*sx, 0.,
            (2*x*y-2*z*w)*sy, (1-2*x*x-2*z*z)*sy, (2*y*z+2*x*w)*sy, 0.,
            (2*x*z+2*y*w)*sz, (2*y*z-2*x*w)*sz, (1-2*x*x-2*y*y)*sz, 0., tx, ty, tz, 1.]


def image_size(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 255:
                raise ValueError("Invalid JPEG marker")
            marker = data[pos + 1]
            pos += 2
            if marker in (0xD8, 0xD9):
                continue
            size = int.from_bytes(data[pos:pos+2], "big")
            if size < 2:
                raise ValueError("Invalid JPEG segment")
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[pos+3:pos+7])
                return width, height
            pos += size
    raise ValueError("Only embedded PNG/JPEG textures are supported")


def inspect_glb(path, spec, profile):
    import json
    raw = Path(path).read_bytes()
    if len(raw) < 20 or struct.unpack("<III", raw[:12]) != (0x46546C67, 2, len(raw)):
        raise ValueError("Invalid GLB header/length")
    chunks = []
    offset = 12
    while offset < len(raw):
        size, kind = struct.unpack_from("<II", raw, offset)
        offset += 8
        if size % 4 or offset + size > len(raw):
            raise ValueError("Invalid GLB chunk bounds/alignment")
        chunks.append((kind, raw[offset:offset+size]))
        offset += size
    if len(chunks) != 2 or chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
        raise ValueError("Expected one JSON and one embedded BIN chunk")
    doc = json.loads(chunks[0][1], parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    blob = chunks[1][1]
    buffers = doc.get("buffers", [])
    if doc.get("asset", {}).get("version") != "2.0" or len(buffers) != 1 or "uri" in buffers[0] or not 0 < buffers[0]["byteLength"] <= len(blob):
        raise ValueError("Expected glTF 2.0 and one embedded buffer")
    if doc.get("extensionsRequired"):
        raise ValueError("Required glTF extensions need explicit validator support")

    def item(table, index):
        values = doc.get(table, [])
        if type(index) is not int or index < 0 or index >= len(values):
            raise ValueError("Invalid reference to " + table)
        return values[index]

    def view_bytes(index):
        view = item("bufferViews", index)
        start = view.get("byteOffset", 0)
        end = start + view["byteLength"]
        if view.get("buffer", 0) != 0 or start < 0 or end > buffers[0]["byteLength"]:
            raise ValueError("bufferView exceeds embedded buffer")
        return blob[start:end], view

    def accessor(index, expected):
        acc = item("accessors", index)
        if "sparse" in acc or acc.get("type") != expected or type(acc.get("count")) is not int or acc["count"] <= 0:
            raise ValueError("Unsupported/empty accessor")
        sizes = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
        fmt, scalar_size = sizes[acc["componentType"]]
        width = {"SCALAR": 1, "VEC3": 3}[expected]
        if expected == "VEC3" and acc["componentType"] != 5126:
            raise ValueError("Positions/normals must be float vectors")
        data, view = view_bytes(acc["bufferView"])
        stride = view.get("byteStride", scalar_size * width)
        start = acc.get("byteOffset", 0)
        if start < 0 or stride < scalar_size * width or start + (acc["count"] - 1) * stride + scalar_size * width > len(data):
            raise ValueError("Accessor exceeds bufferView")
        values = [struct.unpack_from("<" + fmt * width, data, start + i * stride) for i in range(acc["count"])]
        if any(not math.isfinite(n) for value in values for n in value):
            raise ValueError("Non-finite geometry")
        return values

    mesh_data = {}
    for index, mesh in enumerate(doc.get("meshes", [])):
        points, tris = [], 0
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                raise ValueError("Only triangle primitives are supported")
            attrs = primitive["attributes"]
            item("materials", primitive.get("material"))
            vertices = accessor(attrs["POSITION"], "VEC3")
            normals = accessor(attrs["NORMAL"], "VEC3")
            if len(normals) != len(vertices) or any(not 0.5 < sum(n*n for n in value) < 1.5 for value in normals):
                raise ValueError("Invalid/missing normals")
            count = len(vertices)
            if "indices" in primitive:
                indices = accessor(primitive["indices"], "SCALAR")
                if any(type(v[0]) is not int or v[0] >= len(vertices) for v in indices):
                    raise ValueError("Invalid vertex index")
                count = len(indices)
            if count % 3:
                raise ValueError("Incomplete triangle")
            tris += count // 3
            points.extend(vertices)
        mesh_data[index] = (points, tris)
    nodes = doc.get("nodes", [])
    roots = item("scenes", doc.get("scene", 0)).get("nodes", [])
    points, triangles, visited = [], 0, set()

    def visit(index, parent):
        nonlocal triangles
        if index in visited:
            raise ValueError("Cyclic or multiply parented scene node")
        visited.add(index)
        node = item("nodes", index)
        matrix = multiply(parent, transform(node))
        if "mesh" in node:
            item("meshes", node["mesh"])
            vertices, tris = mesh_data[node["mesh"]]
            triangles += tris
            for xyz in vertices:
                v = (*xyz, 1.)
                points.append([sum(matrix[k*4+row]*v[k] for k in range(4)) for row in range(3)])
        for child in node.get("children", []):
            visit(child, matrix)
    for root in roots:
        visit(root, identity())
    if not points or triangles < 1 or any(not math.isfinite(x) for p in points for x in p):
        raise ValueError("No finite visible triangle geometry")
    size = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
    if any(x < lo - 0.0001 or x > hi + 0.0001 for x, lo, hi in zip(size, spec["size_m"]["min"], spec["size_m"]["max"])):
        raise ValueError("Measured size exceeds spec: " + str(size))
    materials = len(doc.get("materials", []))
    bones = len({joint for skin in doc.get("skins", []) for joint in skin.get("joints", [])})
    actual = {"triangles": triangles, "materials": materials, "bones": bones}
    for key, limit in profile["budgets"][spec["kind"]].items():
        if actual[key] > limit:
            raise ValueError("%s budget exceeded: %s > %s" % (key, actual[key], limit))
    animations = {a.get("name") for a in doc.get("animations", []) if a.get("channels") and a.get("samplers")}
    if not set(spec["animations"]).issubset(animations):
        raise ValueError("Missing required animation clips")
    if spec["kind"] == "character" and (bones < 1 or not spec["animations"]):
        raise ValueError("Characters need a rig and required animation clips")
    for image in doc.get("images", []):
        if "uri" in image:
            raise ValueError("External texture dependency is not allowed")
        data, _ = view_bytes(image["bufferView"])
        width, height = image_size(data)
        if min(width, height) < 1 or max(width, height) > profile["max_texture_size"]:
            raise ValueError("Texture size budget exceeded")
    for texture in doc.get("textures", []):
        item("images", texture.get("source"))
    for material in doc.get("materials", []):
        pbr = material.get("pbrMetallicRoughness", {})
        for obj in (material, pbr):
            for key, value in obj.items():
                if key.endswith("Texture"):
                    item("textures", value.get("index"))
    suffix = {"convex": "-convcol", "trimesh": "-col"}.get(spec["collision"])
    if suffix and not any(suffix in str(node.get("name", "")) for node in nodes):
        raise ValueError("Missing Godot collision import suffix: " + suffix)
    return {**actual, "size_m": size, "animations": sorted(animations), "textures": len(doc.get("images", []))}


def profile_data():
    # Mesh validation is independent from a 2D project's raster style selection.
    path = Path("art/style/profiles/stylized-3d.json")
    return path, read_json(path)


def locked_sheet():
    if not Path("art/style/reference-manifest.json").is_file():
        raise GateError("not_style_locked", "Approve and freeze the reference sheet before production")
    try:
        return verify_sheet()
    except (OSError, ValueError, KeyError) as exc:
        raise GateError("sheet_drift", str(exc)) from exc


def validate_asset(asset):
    asset = inside(asset)
    provenance = asset.with_suffix(".provenance.json")
    if not provenance.is_file():
        raise GateError("provenance_missing", str(asset))
    prov = read_json(provenance)
    if prov.get("provenance_version") != 1 or prov.get("pipeline") != "blender-3d":
        raise ValueError("Unsupported mesh provenance")
    for field in ("created_utc", "blender", "creator", "source_hashes", "artifacts", "spec_path", "spec_sha256"):
        if not prov.get(field):
            raise ValueError("Missing provenance: " + field)
    spec = read_json(inside(prov["spec_path"]))
    spec_check(spec)
    if prov.get("asset_id") != spec["id"] or prov["creator"] != spec["creator"]:
        raise ValueError("Provenance/spec identity mismatch")
    if digest(inside(prov["spec_path"])) != prov["spec_sha256"]:
        raise ValueError("Frozen mesh spec hash mismatch")
    profile_path, profile = profile_data()
    if digest(profile_path) != prov.get("profile_sha256"):
        raise ValueError("Style profile changed; review and rebuild")
    if locked_sheet()["sheet_sha256"] != prov.get("reference_sheet_sha256"):
        raise ValueError("Reference sheet changed since production")
    hashes = prov["source_hashes"]
    required_sources = {spec["source"], *spec.get("dependencies", [])}
    if not required_sources.issubset(hashes):
        raise ValueError("Recipe/dependency provenance is incomplete")
    for name, sha in hashes.items():
        if digest(inside(name)) != sha:
            raise ValueError("Recipe or dependency changed: " + name)
        if Path(name).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            check_image(inside(name))
    key = asset.relative_to(Path.cwd()).as_posix()
    if key not in prov["artifacts"]:
        raise ValueError("Provenance does not bind this GLB")
    for name, sha in prov["artifacts"].items():
        if digest(inside(name)) != sha:
            raise ValueError("Artifact bytes changed: " + name)
    stats = inspect_glb(asset, spec, profile)
    return {"pass": True, "asset": key, "stats": stats, "machine_checks": profile["machine_checks"], "review_required": profile["review_checks"]}


def build(args):
    from datetime import datetime, timezone
    spec_path = inside(args.spec)
    spec = read_json(spec_path)
    source = spec_check(spec)
    sheet = locked_sheet()
    profile_path, profile = profile_data()
    dependencies = [source, *(inside(p) for p in spec.get("dependencies", [])), inside("pipeline/blender/build_driver.py")]
    source_hashes = {p.relative_to(Path.cwd()).as_posix(): digest(p) for p in dependencies}
    for dependency in dependencies:
        if dependency.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            check_image(dependency)
            record_path = dependency.with_suffix(".provenance.json")
            record = read_json(record_path)
            for extra in (record_path, inside(record["prompt_path"])):
                source_hashes[extra.relative_to(Path.cwd()).as_posix()] = digest(extra)
    directory = run_dir("mesh-" + spec["id"], "art/builds")
    frozen_spec = directory / "spec.json"
    write_json(frozen_spec, spec)
    exe = binary("blender")
    tool_version = version("blender", exe, directory)
    output = directory / (spec["id"] + ".glb")
    run_process([exe, "--background", "--factory-startup", "--python", inside("pipeline/blender/build_driver.py"), "--", frozen_spec, source, output], directory / "blender.log", args.timeout)
    actual_inputs = read_json(output.with_suffix(".inputs.json"))
    if not set(actual_inputs).issubset(source_hashes):
        raise GateError("dependency_missing", "Declare every external Blender texture/library in mesh spec dependencies: " + str(actual_inputs))
    stats = inspect_glb(output, spec, profile)
    artifacts = [output, directory / (spec["id"] + ".blend"), *(directory / (spec["id"] + "-" + str(i) + ".png") for i in range(3))]
    if any(not p.is_file() or p.stat().st_size == 0 for p in artifacts):
        raise GateError("artifact_missing", "GLB, blend source and three previews are required")
    destination = inside(args.project) / "assets/models" / output.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    prov_path = destination.with_suffix(".provenance.json")
    for old in (destination, prov_path):
        if old.exists():
            previous = directory / "previous"
            previous.mkdir(exist_ok=True)
            shutil.move(str(old), previous / old.name)
    shutil.copy2(output, destination)
    artifacts.append(destination)
    write_json(prov_path, {"provenance_version": 1, "pipeline": "blender-3d", "asset_id": spec["id"],
        "created_utc": datetime.now(timezone.utc).isoformat(), "creator": spec["creator"], "blender": tool_version,
        "spec_path": frozen_spec.relative_to(Path.cwd()).as_posix(), "spec_sha256": digest(frozen_spec),
        "source_hashes": source_hashes, "profile_sha256": digest(profile_path), "reference_sheet_sha256": sheet["sheet_sha256"],
        "artifacts": {p.relative_to(Path.cwd()).as_posix(): digest(p) for p in artifacts}, "stats": stats})
    result = validate_asset(destination)
    return {**result, "provenance": str(prov_path), "previews": [str(p) for p in artifacts if p.suffix == ".png"], "logs": str(directory)}


def main():
    parser = Parser(add_help=False)
    parser.add_argument("action", choices=["build", "validate", "image"])
    parser.add_argument("--spec")
    parser.add_argument("--asset")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--project", default=os.environ.get("GP_PROJECT_DIR", "game"))
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--image")
    parser.add_argument("--prompt")
    parser.add_argument("--model")
    parser.add_argument("--provider")
    args = parser.parse_args()
    if args.action == "image":
        return register_image(args)
    if args.action == "build":
        if not args.spec:
            raise GateError("bad_usage", "--spec is required")
        return build(args)
    if args.all:
        paths = sorted((inside(args.project) / "assets").rglob("*.glb"))
        if not paths:
            raise GateError("assets_missing", "No GLB assets found")
        results = []
        for path in paths:
            try:
                results.append(validate_asset(path))
            except (GateError, OSError, ValueError, KeyError, TypeError, IndexError, struct.error) as exc:
                results.append({"pass": False, "asset": str(path), "error_kind": getattr(exc, "kind", "asset_invalid"), "errors": [str(exc)]})
        return {"pass": all(r["pass"] for r in results), "assets": results}
    if not args.asset:
        raise GateError("bad_usage", "--asset or --all is required")
    try:
        return validate_asset(args.asset)
    except struct.error as exc:
        raise GateError("asset_invalid", str(exc)) from exc


def check_image(image):
    path = image.with_suffix(".provenance.json")
    if not path.is_file():
        raise GateError("provenance_missing", "Image dependency needs provenance: " + str(image))
    record = read_json(path)
    image_size(image.read_bytes())
    if record.get("pipeline") != "3d-image" or record.get("image_sha256") != digest(image):
        raise GateError("provenance_invalid", "Image bytes/provenance mismatch")
    if digest(inside(record["prompt_path"])) != record.get("prompt_sha256") or not record.get("model") or not record.get("provider"):
        raise GateError("provenance_invalid", "Image prompt/provider metadata mismatch")


def register_image(args):
    from datetime import datetime, timezone
    if not all((args.image, args.prompt, args.model, args.provider)):
        raise GateError("bad_usage", "Image registration requires --image --prompt --model --provider")
    image, prompt = inside(args.image), inside(args.prompt)
    if image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise GateError("bad_usage", "Image dependencies must be PNG or JPEG")
    image_size(image.read_bytes())
    image_hash = digest(image)
    directory = run_dir("image-" + image.stem, "art/builds")
    snapshot = directory / "prompt.txt"
    shutil.copy2(prompt, snapshot)
    prov = image.with_suffix(".provenance.json")
    if prov.exists():
        shutil.copy2(prov, directory / "previous-provenance.json")
    write_json(prov, {"provenance_version": 1, "pipeline": "3d-image", "image_sha256": image_hash,
        "model": args.model, "provider": args.provider, "created_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_path": snapshot.relative_to(Path.cwd()).as_posix(), "prompt_sha256": digest(snapshot)})
    check_image(image)
    return {"pass": True, "image": str(image), "provenance": str(prov)}


if __name__ == "__main__":
    entry(main)
