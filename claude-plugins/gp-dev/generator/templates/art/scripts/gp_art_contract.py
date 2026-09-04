"""Shared, standard-library-only validation for frozen art contracts."""
import hashlib
import json
import os
import re
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(value, schema, where="document"):
    """Validate the JSON Schema keywords used by the shipped gp schemas."""
    kinds = {"object": dict, "array": list, "string": str, "integer": int,
             "number": (int, float), "boolean": bool}
    kind = schema.get("type")
    if kind and (not isinstance(value, kinds[kind]) or
                 (kind in ("number", "integer") and isinstance(value, bool))):
        raise ValueError("%s must be %s" % (where, kind))
    if "const" in schema and value != schema["const"]:
        raise ValueError("%s has an unsupported version/value" % where)
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("%s is not an allowed value" % where)
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError("%s is missing %s" % (where, key))
        props = schema.get("properties", {})
        for key, child in value.items():
            if key not in props and schema.get("additionalProperties") is False:
                raise ValueError("%s has unknown field %s" % (where, key))
            if key in props:
                validate(child, props[key], "%s.%s" % (where, key))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError("%s has too few items" % where)
        for index, child in enumerate(value):
            validate(child, schema.get("items", {}), "%s[%d]" % (where, index))
    if isinstance(value, str) and schema.get("pattern"):
        if not re.search(schema["pattern"], value):
            raise ValueError("%s has invalid format" % where)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")):
            raise ValueError("%s is outside its allowed range" % where)


def check_schema(value, name):
    schema = json.loads(Path("art/schemas/%s.schema.json" % name).read_text(encoding="utf-8"))
    validate(value, schema, name)


def check_spec(spec):
    check_schema(spec, "prompt-spec")
    if spec["operation"] == "edit":
        if not spec.get("source_image") or not spec.get("edit_goal"):
            raise ValueError("edit requires source_image and edit_goal")
        if not Path(spec["source_image"]).is_file():
            raise ValueError("edit source_image is missing")
    if spec["asset_type"] != "reference_sheet" and not spec.get("reference_images"):
        raise ValueError("production assets require frozen reference_images")


def verify_sheet(manifest_path="art/style/reference-manifest.json"):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 1:
        raise ValueError("unsupported reference manifest version")
    sheet_dir = Path(manifest["sheet_dir"])
    files = manifest["files"]
    if not files or not sheet_dir.is_dir():
        raise ValueError("locked reference sheet is empty or missing")
    current = sorted(p.as_posix() for p in sheet_dir.rglob("*")
                     if p.is_file() and p.suffix in (".png", ".jpg", ".webp"))
    if current != [f["path"] for f in files]:
        raise ValueError("reference file list changed after STYLE LOCK")
    for item in files:
        if digest(item["path"]) != item["sha256"]:
            raise ValueError("reference image changed after STYLE LOCK: %s" % item["path"])
    encoded = ",".join(json.dumps(f, separators=(",", ":"), ensure_ascii=False) for f in files)
    actual = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    if actual != manifest.get("sheet_sha256"):
        raise ValueError("reference manifest hash mismatch")
    return manifest


def check_references(spec, manifest):
    locked = {os.path.normcase(os.path.abspath(f["path"])) for f in manifest["files"]}
    for ref in spec.get("reference_images", []):
        if os.path.normcase(os.path.abspath(ref)) not in locked:
            raise ValueError("reference is outside the locked sheet: %s" % ref)


def check_provenance(prov, profile_id):
    check_schema(prov, "provenance")
    for key in ("asset_id", "model", "created_utc", "prompt_spec_path"):
        if not prov[key]:
            raise ValueError("provenance has empty %s" % key)
    if prov["style_profile"] != profile_id:
        raise ValueError("provenance style profile differs from validator profile")
    if digest(prov["prompt_spec_path"]) != prov["prompt_spec_sha256"]:
        raise ValueError("prompt-spec changed after generation")
    spec = json.loads(Path(prov["prompt_spec_path"]).read_text(encoding="utf-8"))
    check_spec(spec)
    if spec["id"] != prov["asset_id"] or spec["style_profile"] != profile_id:
        raise ValueError("provenance does not match prompt-spec identity")
    if spec["asset_type"] != "reference_sheet":
        manifest = verify_sheet()
        check_references(spec, manifest)
        if manifest["sheet_sha256"] != prov["reference_sheet_sha256"]:
            raise ValueError("asset was produced against another reference sheet")
