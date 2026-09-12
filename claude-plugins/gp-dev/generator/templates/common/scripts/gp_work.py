"""Portable, dependency-free workflow kernel. Run through <prefix>-work.sh.

The board is Markdown; .ai/gp holds recoverable execution records, never another
editable backlog. All mutations preserve prior versions in archive/.
"""
from __future__ import annotations

import argparse
import contextlib
import fnmatch
import hashlib
import json
import os
import errno
import difflib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

VERSION = 1
STATES = {"BACKLOG", "ACTIVE", "BLOCKED", "REVIEW", "DONE"}
EXCLUDE = {".git", ".godot", "archive", "node_modules", "__pycache__", "build", "builds", "out", "graphify-out"}
ID = r"[A-Za-z][A-Za-z0-9_]*-?\d+[A-Za-z0-9_-]*"
READ_ONLY = {"reviewer", "verifier", "architect", "explorer"}
TIERS = ["simple", "complex", "expert"]
DEFAULT_POLICY = {
    "version": 1, "mode": "tiered",
    "claude": {"mode": "auto", "tiers": {}, "orchestrator": {}, "notes": "Claude Code selects its current native models; configure tiers here when known"},
    "orchestrator": {"model": "gpt-5.6-sol", "reasoning": "high"},
    "tiers": {
        "simple": {"model": "gpt-5.6-luna", "reasoning": "xhigh"},
        "complex": {"model": "gpt-5.6-sol", "reasoning": "xhigh"},
        "expert": {"model": "gpt-6-astra", "reasoning": "high"}},
    "max_concurrent_agents": 3, "max_delegation_depth": 1,
    "max_attempts_per_stage": 3, "context_chars": 24000,
    "fallbacks": {}}


class WorkError(Exception):
    def __init__(self, kind, detail):
        self.kind, self.detail = kind, detail
        super().__init__(detail)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("bad_usage", message)


def fail(kind, detail):
    raise WorkError(kind, detail)


def read(path):
    return path.read_text(encoding="utf-8-sig")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load(path):
    try:
        return json.loads(read(path))
    except (ValueError, OSError) as exc:
        fail("invalid_json", f"{path}: {exc}")


def contract(root, name, value):
    candidates = [root / "pipeline/schemas" / ("work-" + name + ".schema.json"),
                  Path(__file__).resolve().parents[3] / "schemas" / ("work-" + name + ".schema.json")]
    schema = next((p for p in candidates if p.is_file()), None)
    if schema:
        validate_schema(value, load(schema))


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        fail("path_outside_project", str(name))
    return path


def rel(root, path):
    return path.relative_to(root).as_posix()


def safe_id(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", value):
        fail("invalid_id", value)
    return value


def preserve(root, path):
    if path.exists():
        dst = root / "archive/gp-work" / uuid.uuid4().hex / rel(root, path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


def write(root, path, value):
    path = inside(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    preserve(root, path)
    tmp = path.with_name(path.name + ".tmp." + uuid.uuid4().hex)
    tmp.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def event(root, kind, **data):
    folder = root / ".ai/gp/events"
    folder.mkdir(parents=True, exist_ok=True)
    # Separate immutable events avoid interleaved append writes across processes.
    (folder / (str(time.time_ns()) + "-" + uuid.uuid4().hex + ".json")).write_text(
        json.dumps({"version": 1, "time": time.time(), "kind": kind, **data}) + "\n", encoding="utf-8")


def recover_mutation(root, expected_pid):
    path = root / ".ai/gp/mutation.lock"
    if not path.exists():
        return {"pass": True, "status": "not_locked"}
    value = load(path)
    if value.get("pid") != expected_pid:
        fail("lock_owner_changed", "Inspect the current mutation lock before retrying recovery")
    if os.name == "nt":
        proc = subprocess.run(["tasklist", "/FI", f"PID eq {expected_pid}", "/FO", "CSV", "/NH"], capture_output=True, timeout=10)
        if proc.returncode:
            fail("lock_owner_unknown", "Could not verify the Windows process list")
        running = f'","{expected_pid}",'.encode() in proc.stdout
    else:
        try:
            os.kill(expected_pid, 0)
            running = True
        except OSError as exc:
            running = exc.errno != errno.ESRCH
    if running:
        fail("mutation_busy", "The lock owner is still alive; do not steal its transaction")
    target = root / "archive/gp-work/locks" / (uuid.uuid4().hex + "-recovered.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Recheck identity immediately before retiring an interrupted owner.
    if load(path) != value:
        fail("lock_owner_changed", "Mutation lock changed during inspection")
    path.rename(target)
    event(root, "mutation_lock_recovered", previous=value, archive=rel(root, target))
    return {"pass": True, "status": "recovered", "archive": rel(root, target)}


@contextlib.contextmanager
def mutex(root):
    path = root / ".ai/gp/mutation.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "time": time.time()}, stream)
    except FileExistsError:
        fail("mutation_busy", "Another mutation or an interrupted transaction owns .ai/gp/mutation.lock; inspect before archive/recovery")
    try:
        yield
    finally:
        target = root / "archive/gp-work/locks" / (uuid.uuid4().hex + ".json")
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)


def files(root):
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE and not (Path(base).name == ".ai" and d == "gp"))
        for name in sorted(names):
            path = Path(base) / name
            if not path.is_symlink() and path.resolve().is_relative_to(root):
                yield path


def section(text, title):
    text = re.sub(r"<!-- gp-meta\s*\{.*?\}\s*-->", "", text, flags=re.S)
    match = re.search(r"(?im)^#{1,3}\s+" + "(?:" + title + ")" + r"[^\n]*\n(.*?)(?=^#{1,3}\s|\Z)", text, re.S | re.M)
    return match.group(1).strip() if match else ""


def metadata(text):
    match = re.search(r"<!-- gp-meta\s*(\{.*?\})\s*-->", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except ValueError:
        fail("spec_invalid", "Malformed gp-meta JSON")


def parse_card(root, path, kind="spec"):
    text = read(path)
    meta = metadata(text)
    heading = re.search(r"(?m)^#\s+(" + ID + r")(?:\s|[:—–-])", text)
    key = meta.get("id") or (heading.group(1) if heading else path.stem.split(" ")[0])
    safe_id(key)
    status_match = re.search(r"(?im)^Status:\s*\**(" + "|".join(sorted(STATES)) + r")\b", text)
    state = status_match.group(1).upper() if status_match else {"done": "DONE", "active": "ACTIVE"}.get(path.parent.name.lower(), "BACKLOG")
    dep_text = section(text, "Dependencies")
    deps = meta.get("dependencies", re.findall(r"\b(" + ID + r")\b", dep_text))
    acceptance = section(text, "Acceptance criteria|DONE_WHEN")
    if not acceptance:
        m = re.search(r"(?im)^DONE_WHEN:\s*\n(.*?)(?=^[A-Z_]+:|\Z)", text, re.S)
        acceptance = m.group(1).strip() if m else ""
    track_match = re.match(r"[A-Za-z]+", key)
    track = track_match.group(0) if track_match else "general"
    return {"id": key, "path": rel(root, path), "status": state, "track": meta.get("track", track),
            "dependencies": list(dict.fromkeys(deps)), "acceptance": acceptance,
            "acceptance_sha256": json_hash(acceptance), "sha256": digest(path),
            "meta": meta, "kind": kind}


def board(root, art=False):
    folder = root / ("art/cards" if art else "SPECS")
    if not folder.is_dir():
        fail("board_missing", "SPECS/ is absent. Dispatch the tool's simple-tier backlog-discovery agent before creating it" if not art else "art/cards/ is absent")
    cards = []
    for area in ("backlog", "active", "done"):
        for path in sorted((folder / area).glob("*.md")):
            if path.name.upper() != "README.MD":
                cards.append(parse_card(root, path, "art" if art else "spec"))
    seen = set()
    for card in cards:
        if card["id"] in seen:
            fail("duplicate_id", card["id"])
        seen.add(card["id"])
    index = folder / "INDEX.md"
    if index.exists():
        order = re.findall(r"\[(" + ID + r")[^\]]*\]\((?:backlog|active|done)/", read(index))
        rank = {key: i for i, key in reversed(list(enumerate(order)))}
        cards.sort(key=lambda card: (rank.get(card["id"], len(order)), card["id"]))
    return cards


def completion_exists(root, card):
    meta = card["meta"]
    if meta.get("evidence"):
        path = inside(root, meta["evidence"])
        return path.is_file() and bool(meta.get("evidence_sha256")) and digest(path) == meta["evidence_sha256"]
    # Existing boards can retain their original completion documents and evidence.
    body = section(read(root / card["path"]), "Completion evidence|Completion|Implementation evidence")
    paths = list((root / "docs/evidence" / card["id"]).glob("**/*"))
    return bool(body and any(p.is_file() and p.stat().st_size for p in paths))


def ready(root, cards, track=None, key=None):
    lookup = {c["id"]: c for c in cards}
    result = []
    for card in cards:
        if track and card["track"] != track or key and card["id"] != key:
            continue
        reasons = []
        if not card["acceptance"]:
            reasons.append("acceptance_missing")
        if card["status"] != "BACKLOG":
            reasons.append("status=" + card["status"])
        for dep in card["dependencies"]:
            other = lookup.get(dep)
            if not other or other["status"] != "DONE" or not completion_exists(root, other):
                reasons.append("dependency_evidence:" + dep)
        for name in card["meta"].get("prerequisites", []):
            if not inside(root, name).exists():
                reasons.append("prerequisite:" + name)
        result.append({**card, "ready": not reasons, "reasons": reasons})
    return result


def discover(root, tool="codex"):
    candidates = []
    for path in files(root):
        if path.suffix.lower() != ".md" or "SPECS" in path.parts or "templates" in path.parts:
            continue
        relative = rel(root, path)
        if any(part.lower() in {"spec", "specs", "backlog", "tasks", "issues"} for part in path.parts[:-1]) or path.stem.lower() in {"backlog", "todo", "tasks", "roadmap"}:
            candidates.append({"path": relative, "sha256": digest(path), "bytes": path.stat().st_size})
    return {"pass": True, "board_exists": (root / "SPECS").is_dir(), "candidates": candidates,
            "dispatch": {"role": "backlog-discovery", **route(root, {"role": "backlog-discovery", "tool": tool})},
            "next": "The selected discovery agent must inspect candidates, distinguish task cards from guidance, and write a migration plan; report backlog_empty when no tasks exist"}


def rewrite_links(root, moves, preview=False):
    mapping = {inside(root, src): inside(root, dst) for src, dst in moves.items()}
    reverse = {dst: src for src, dst in mapping.items()}
    updates = []
    for path in list(files(root)):
        if path.suffix.lower() != ".md":
            continue
        destination_path = mapping.get(path, path)
        old_parent = (path if path in mapping else reverse.get(path, path)).parent
        def replace(match):
            target = match.group(2)
            if re.match(r"[a-z]+:|#", target, re.I):
                return match.group(0)
            local, mark, anchor = target.partition("#")
            resolved = (old_parent / local.replace("%20", " ")).resolve()
            destination = mapping.get(resolved, resolved)
            if resolved not in mapping and path not in reverse and path not in mapping:
                return match.group(0)
            value = os.path.relpath(destination, destination_path.parent).replace(os.sep, "/")
            return match.group(1) + value + (mark + anchor if mark else "") + ")"
        before = read(path)
        after = re.sub(r"(!?\[[^\]]*\]\()([^\)]+)\)", replace, before)
        if before != after:
            updates.append({"path": str(destination_path), "text": after})
            if not preview:
                write(root, destination_path, after)
    return updates


def migrate(root, plan, apply=False):
    contract(root, "migration", plan)
    journal_path = root / ".ai/gp/migration-transaction.json"
    journal = load(journal_path) if journal_path.exists() else None
    resuming = bool(journal and journal.get("status") == "PENDING" and journal.get("plan_hash") == json_hash(plan))
    if (root / "SPECS").exists() and not resuming:
        fail("board_exists", "Use the existing SPECS board; discovery migration is only for an absent board")
    if plan.get("version") != 1 or not isinstance(plan.get("moves"), list):
        fail("migration_invalid", "Expected version:1 and moves:[{source,target,sha256}]")
    moves, targets = {}, set()
    for item in plan["moves"]:
        src, dst = inside(root, item["source"]), inside(root, item["target"])
        actual = dst if resuming and not src.exists() else src
        if not actual.is_file() or src.suffix.lower() != ".md" or (not resuming and digest(actual) != item["sha256"]):
            fail("migration_stale", item["source"])
        if any(p in EXCLUDE for p in Path(item["source"]).parts):
            fail("migration_invalid", "Archived/build inputs are not a live backlog")
        if not dst.is_relative_to(root / "SPECS") or (dst.exists() and not resuming) or dst in targets or str(src) in moves or dst.suffix.lower() != ".md":
            fail("migration_conflict", item["target"])
        is_card = bool(re.search(r"(?m)^#\s+" + ID + r"(?:\s|[:—–-])", read(actual))) or src.parent.name.lower() in {"backlog", "active", "done"} and src.name.lower() != "readme.md"
        if is_card and dst.parent not in {root / "SPECS/backlog", root / "SPECS/done"}:
            fail("migration_invalid", "Task cards must be directly under SPECS/backlog or SPECS/done")
        moves[str(src)] = str(dst)
        targets.add(dst)
    if not moves:
        if apply:
            (root / "SPECS/backlog").mkdir(parents=True)
            (root / "SPECS/done").mkdir()
            event(root, "backlog_empty", migration=plan)
        return {"pass": True, "status": "backlog_empty", "message": "No tasks were found; the backlog is empty"}
    if apply:
        with mutex(root):
            # Decode all affected Markdown before any moves. Keep a durable journal
            # so an interrupted filesystem operation can be replayed with this plan.
            if not resuming:
                updates = rewrite_links(root, moves, preview=True)
                for src, dst in moves.items():
                    if Path(src).parent.name.lower() == "active":
                        update = next((u for u in updates if u["path"] == dst), None)
                        text = update["text"] if update else read(Path(src))
                        if not re.search(r"(?im)^Status:", text):
                            first, _, tail = text.partition("\n")
                            text = first + "\n\nStatus: **ACTIVE**\n" + tail
                            if update: update["text"] = text
                            else: updates.append({"path": dst, "text": text})
                journal = {"status": "PENDING", "plan_hash": json_hash(plan), "plan": plan, "updates": updates}
                write(root, journal_path, journal)
            for src, dst in moves.items():
                source, target = Path(src), Path(dst)
                if not source.exists() and target.exists():
                    continue
                preserve(root, source)
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
            for update in journal["updates"]:
                write(root, Path(update["path"]), update["text"])
            (root / "SPECS/backlog").mkdir(exist_ok=True)
            (root / "SPECS/done").mkdir(exist_ok=True)
            event(root, "backlog_migrated", plan=plan)
            sync_index(root)
            write(root, journal_path, {"status": "DONE", "plan_hash": json_hash(plan), "plan": plan})
    return {"pass": True, "applied": apply, "moves": plan["moves"]}


def set_status(root, card, status, evidence=None):
    path = root / card["path"]
    text = read(path)
    if re.search(r"(?im)^Status:", text):
        text = re.sub(r"(?im)^Status:[^\n]*", "Status: **" + status + "**", text)
    else:
        first, _, tail = text.partition("\n")
        text = first + "\n\nStatus: **" + status + "**\n" + tail
    if evidence:
        meta = card["meta"] | {"evidence": evidence, "evidence_sha256": digest(inside(root, evidence))}
        text = re.sub(r"<!-- gp-meta\s*\{.*?\}\s*-->\s*", "", text, flags=re.S)
        text += "\n<!-- gp-meta " + json.dumps(meta) + " -->\n"
    write(root, path, text)
    if status == "DONE" and path.parent.name != "done":
        target = path.parent.parent / "done" / path.name
        if target.exists():
            fail("board_conflict", str(target))
        target.parent.mkdir(exist_ok=True)
        path.rename(target)
        rewrite_links(root, {str(path): str(target)})
    sync_index(root)


def sync_index(root):
    cards = board(root)
    path = root / "SPECS/INDEX.md"
    if path.exists():
        text = read(path)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not line.startswith("|"):
                continue
            for card in cards:
                if re.search(r"\[" + re.escape(card["id"]) + r"(?:\s|\])", line):
                    lines[i] = re.sub(r"\b(BACKLOG|ACTIVE|BLOCKED|REVIEW|DONE)\b(?=[^|]*\|\s*$)", card["status"], line)
                    break
        text = "\n".join(lines) + "\n"
        text = re.sub(r"\*\*\d+ specs:.*?\*\*", "**" + str(len(cards)) + " specs: " + ", ".join(str(sum(c["status"] == s for c in cards)) + " " + s for s in ["BACKLOG", "ACTIVE", "REVIEW", "BLOCKED", "DONE"]) + ".**", text)
        missing = [c for c in cards if not re.search(r"\[" + re.escape(c["id"]) + r"(?:\s|\])", text)]
        if missing:
            text += "\n## Additional indexed tasks\n\n| Spec | Dependencies | Status |\n|---|---|---|\n"
            text += "".join(f"| [{c['id']}]({Path(c['path']).relative_to('SPECS').as_posix()}) | {', '.join(c['dependencies']) or '—'} | {c['status']} |\n" for c in missing)
    else:
        text = "# Specification index\n\n| Spec | Dependencies | Status |\n|---|---|---|\n"
        text += "".join(f"| [{c['id']}]({Path(c['path']).relative_to('SPECS').as_posix()}) | {', '.join(c['dependencies']) or '—'} | {c['status']} |\n" for c in cards)
    write(root, path, text)


def policy(root):
    path = root / "pipeline/model-policy.json"
    value = load(path) if path.exists() else DEFAULT_POLICY.copy()
    contract(root, "model-policy", value)
    if value.get("version") != 1 or value.get("mode") not in {"tiered", "inherit"}:
        fail("policy_invalid", "Expected version 1 and mode tiered|inherit")
    for tier in TIERS:
        entry = value.get("tiers", {}).get(tier, {})
        if not isinstance(entry.get("model"), str) or entry.get("reasoning") not in {"low", "medium", "high", "xhigh", "max"}:
            fail("policy_invalid", tier)
    for field in ("max_concurrent_agents", "max_attempts_per_stage", "max_delegation_depth", "context_chars"):
        if type(value.get(field)) != int or value[field] < 1:
            fail("policy_invalid", field)
    return value


def route(root, request):
    p = policy(root)
    role = request.get("role", "developer")
    scope = request.get("execution_scope", "production")
    if scope == "evaluated-authoring":
        if not request.get("frozen_model") or not request.get("allowlist"):
            fail("authoring_contract_missing", "Evaluated authoring requires frozen_model and explicit neutral context allowlist")
        return {"pass": True, "tier": "frozen", "model": request["frozen_model"], "reasoning": request.get("frozen_reasoning"), "reasons": ["isolated evaluated authoring; no production tier routing"]}
    tier = request.get("complexity", "simple")
    if tier not in TIERS:
        fail("assignment_invalid", "complexity must be simple|complex|expert")
    reasons = ["declared complexity: " + tier]
    risk = request.get("risk", {})
    if role == "backlog-discovery":
        tier = "simple"
        reasons = ["Backlog discovery uses the tool's simple tier"]
    elif any(risk.get(k) for k in ("blender", "new_algorithm", "replay_codec", "concurrency", "critical_lifecycle")):
        tier = "expert"
        reasons.append("expert risk trigger")
    elif risk.get("subsystems", 1) > 1 or risk.get("uncertainty") or risk.get("data_loss"):
        tier = TIERS[max(TIERS.index(tier), 1)]
        reasons.append("cross-subsystem/uncertain/data-sensitive change")
    if role in READ_ONLY and request.get("review_floor") in TIERS:
        tier = TIERS[max(TIERS.index(tier), TIERS.index(request["review_floor"]))]
    attempt = request.get("attempt", 1)
    if type(attempt) != int or attempt < 1 or attempt > p["max_attempts_per_stage"]:
        fail("attempt_budget_exhausted", "Diagnose or split without weakening acceptance")
    failure = request.get("failure_kind")
    if failure in {"environment", "tool", "model_unavailable"}:
        fail("external_blocker", "Repair the environment/tool; a larger model does not fix missing inputs")
    if attempt > 1 and failure == "reasoning":
        tier = TIERS[min(2, TIERS.index(tier) + attempt - 1)]
        reasons.append("reasoning failure escalation")
    tool = request.get("tool", "codex")
    if tool not in {"claude", "codex"}:
        fail("assignment_invalid", "tool must be claude|codex")
    if tool == "claude":
        native = p.get("claude", {"mode": "auto", "tiers": {}})
        entry = native.get("tiers", {}).get(tier, {})
        model = {"model": entry.get("model"), "reasoning": entry.get("reasoning")}
        reasons.append("Claude Code selects its native model when this tier is unconfigured")
    elif p["mode"] == "inherit" and role != "backlog-discovery":
        model = {"model": None, "reasoning": None}
    else:
        model = DEFAULT_POLICY["tiers"]["simple"] if role == "backlog-discovery" else p["tiers"][tier]
    return {"pass": True, "tool": tool, "tier": tier, **model, "reasons": reasons, "sandbox": "read-only" if role in READ_ONLY else "workspace-write"}


def project(root):
    path = root / "pipeline/project.json"
    if not path.is_file():
        fail("project_config_missing", "Run adopt --apply to create the project map, then configure real gate commands")
    value = load(path)
    contract(root, "project", value)
    if value.get("version") != 1 or value.get("board") != "SPECS":
        fail("project_config_invalid", "All projects use board SPECS and config version 1")
    for repo in value.get("repositories", {}).values():
        if not isinstance(repo, dict) or not isinstance(repo.get("path"), str):
            fail("project_config_invalid", "repositories map names to {path, writable, version}")
    for gate in value.get("gates", []):
        safe_id(gate["id"])
        if not isinstance(gate.get("command"), list) or not gate["command"] or not all(isinstance(x, str) for x in gate["command"]):
            fail("project_config_invalid", "Gate commands must be nonempty argv arrays")
        if gate.get("result", "json-line") not in {"json-line", "json-file", "exit-code"}:
            fail("project_config_invalid", "Unknown gate result adapter")
    return value


def adopt(root, apply=False):
    godot = [p for p in files(root) if p.name == "project.godot"]
    roots = [rel(root, p.parent) or "." for p in godot]
    clean = all((root / x).is_dir() for x in ("domain", "data", "presentation", "app"))
    profile_path = root / "pipeline/profile.json"
    profile = load(profile_path) if profile_path.exists() else {}
    layers = {x: x for x in ("domain", "data", "presentation", "app")} if clean else {"domain": "sim", "data": "content", "presentation": "render", "app": "ui"}
    architecture = "clean" if clean else "simulation"
    if profile.get("dimension") == "3d" and not clean:
        architecture = "fps"
        layers = {"domain": "domain", "world": "world", "presentation": "render", "input": "input"}
    proposed = {"version": 1, "board": "SPECS", "project_dir": roots[0] if len(roots) == 1 else "game" if profile else ".",
                "architecture": {"profile": architecture, "layers": layers, "pure_domain": True},
                "repositories": {"project": {"path": ".", "writable": True, "version": None}},
                "gates": [], "context": [name for name in ("AGENTS.md", "CLAUDE.md", "SPECS/BOARD-RULES.md") if (root / name).exists()],
                "qualification": {"early": [], "final": []}, "execution_scope": "production",
                "art": {"blender": (root / "pipeline/blender").is_dir()}}
    candidates = [rel(root, p) for p in files(root) if p.parent.name != "scripts" and (p.name.startswith("verify") or p.name in {"runtest.sh", "pytest.ini"})]
    if apply:
        for name, data in (("project.json", proposed), ("model-policy.json", DEFAULT_POLICY)):
            if not (root / "pipeline" / name).exists():
                write(root, root / "pipeline" / name, data)
    return {"pass": True, "applied": apply, "project": proposed, "godot_roots": roots,
            "gate_candidates": candidates, "board_exists": (root / "SPECS").is_dir(),
            "next": "Inspect existing commands and register exact gate argv/results; no unverified harness is selected automatically"}


def repository_root(root, name="project", writable=False):
    if name == "project":
        return root
    item = project(root).get("repositories", {}).get(name)
    if not item:
        fail("repository_unmapped", name)
    if writable and item.get("writable") is not True:
        fail("repository_readonly", name)
    target = (root / item["path"]).resolve()
    if not target.is_dir() or target == target.parent or root.is_relative_to(target):
        fail("repository_invalid", name + ": map an existing independent repository, not an ancestor/drive")
    return target


def snapshot(root, include_repositories=True):
    result = {}
    for path in files(root):
        relative = rel(root, path)
        if relative.startswith(("SPECS/", "docs/evidence/")) or relative in {"STATE.md", "HANDOFF.md"}:
            continue
        if path.suffix in {".pyc", ".log"} or path.name.startswith(".env"):
            continue
        result[relative] = digest(path)
    if include_repositories and (root / "pipeline/project.json").is_file():
        config = project(root)
        for name in config.get("repositories", {}):
            if name == "project": continue
            target = repository_root(root, name)
            for key, value in snapshot(target, False).items():
                result["@" + name + "/" + key] = value
    return result


def changed(before, after):
    return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))


def run_path(root, run_id):
    return root / ".ai/gp/runs" / safe_id(run_id) / "run.json"


def run_load(root, run_id):
    value = load(run_path(root, run_id))
    contract(root, "run", value)
    return value


def claim(root, key, owner, takeover=False):
    safe_id(owner)
    cards = ready(root, board(root), key=key)
    if not cards:
        fail("spec_missing", key)
    card = cards[0]
    lock = root / ".ai/gp/claims" / (safe_id(key) + ".json")
    with mutex(root):
        if lock.exists():
            previous = load(lock)
            if not takeover or time.time() - previous["heartbeat"] < 3600:
                fail("spec_claimed", json.dumps(previous))
            other_reasons = [r for r in card["reasons"] if r != "status=ACTIVE"]
            if other_reasons:
                fail("spec_not_ready", ", ".join(other_reasons))
            event(root, "claim_recovered", previous=previous)
            old = run_load(root, previous["run_id"])
            current_card(root, old)
            old["owner"] = owner
            write(root, run_path(root, old["id"]), old)
            write(root, lock, {"run_id": old["id"], "owner": owner, "heartbeat": time.time()})
            return {"pass": True, "run_id": old["id"], "spec": key, "recovered": True, "stage": old["stage"]}
        elif not card["ready"]:
            fail("spec_not_ready", ", ".join(card["reasons"]))
        run_id = key + "-" + uuid.uuid4().hex[:12]
        run = {"version": 1, "id": run_id, "spec": key, "owner": owner, "status": "ACTIVE", "stage": "implement",
               "acceptance_sha256": card["acceptance_sha256"], "started": time.time(), "baseline": snapshot(root),
               "checkpoints": [], "gates": {}, "assignments": [], "evidence": None}
        write(root, run_path(root, run_id), run)
        write(root, lock, {"run_id": run_id, "owner": owner, "heartbeat": time.time()})
        set_status(root, card, "ACTIVE")
        event(root, "run_started", run_id=run_id, spec=key)
    return {"pass": True, "run_id": run_id, "spec": key, "baseline_files": len(run["baseline"])}


def ensure_owner(root, run):
    lock = root / ".ai/gp/claims" / (run["spec"] + ".json")
    if not lock.exists() or load(lock)["run_id"] != run["id"]:
        fail("claim_lost", run["id"])
    return lock


def current_card(root, run):
    card = next((c for c in board(root) if c["id"] == run["spec"]), None)
    if not card:
        fail("spec_missing", run["spec"])
    if card["acceptance_sha256"] != run["acceptance_sha256"]:
        fail("acceptance_changed", "The accepted scope changed; record an approved revision before starting a new run")
    return card


def checkpoint(root, run_id, stage, note):
    run = run_load(root, run_id)
    with mutex(root):
        ensure_owner(root, run)
        current_card(root, run)
        entry = {"stage": stage, "note": note, "time": time.time(), "source_sha256": json_hash(snapshot(root))}
        run["checkpoints"].append(entry)
        run["stage"] = stage
        write(root, run_path(root, run_id), run)
        write(root, ensure_owner(root, run), {"run_id": run_id, "owner": run["owner"], "heartbeat": time.time()})
    return {"pass": True, "checkpoint": entry}


def resume(root, run_id):
    run = run_load(root, run_id)
    ensure_owner(root, run)
    current_card(root, run)
    current = json_hash(snapshot(root))
    stale = [key for key, value in run["gates"].items() if value["source_sha256"] != current or not inside(root, value["path"]).is_file() or digest(inside(root, value["path"])) != value["sha256"]]
    return {"pass": True, "run_id": run_id, "stage": run["stage"], "checkpoints": run["checkpoints"][-3:],
            "changed_files": changed(run["baseline"], snapshot(root)), "stale_gates": stale,
            "assignments": run["assignments"], "next": "Resume the recorded stage; rerun stale required checks"}


def context_packet(root, request):
    p = policy(root)
    refs = request.get("context", [])
    if not isinstance(refs, list) or not refs:
        fail("context_missing", "Provide a bounded context list, with path and optional start/end lines")
    neutral = request.get("execution_scope") == "evaluated-authoring"
    allowlist = request.get("allowlist", [])
    parts, hashes = [], {}
    for ref in refs:
        if isinstance(ref, str):
            ref = {"path": ref}
        name = ref["path"]
        repo_name = ref.get("repository", "project")
        context_root = repository_root(root, repo_name)
        path = inside(context_root, name)
        identity = name if repo_name == "project" else "@" + repo_name + "/" + name
        if any(x in EXCLUDE for x in Path(name).parts) or path.name.startswith(".env") or path.suffix in {".key", ".pem"}:
            fail("context_forbidden", name)
        if neutral and (repo_name != "project" or name not in allowlist):
            fail("authoring_context_violation", name)
        if not path.is_file():
            fail("context_missing", name)
        lines = read(path).splitlines()
        start, end = ref.get("start", 1), ref.get("end", len(lines))
        if type(start) != int or type(end) != int or start < 1 or end < start or end > len(lines):
            fail("context_range_invalid", name)
        parts.append(f"SOURCE {identity}:{start}-{end}\n" + "\n".join(lines[start - 1:end]))
        hashes[identity] = digest(path)
    packet = "\n\n".join(parts)
    if len(packet) > p["context_chars"]:
        fail("context_budget_exceeded", f"{len(packet)} characters; select sections within {p['context_chars']}")
    return {"text": packet, "hashes": hashes, "chars": len(packet), "estimated_tokens": round(len(packet) / 4), "estimate_method": "chars/4, not observed usage"}


def research_cache(root, key, request=None):
    path = root / ".ai/gp/research" / (safe_id(key) + ".json")
    if request is not None:
        packet = context_packet(root, request)
        value = {"version": 1, "hashes": packet["hashes"], "summary": request.get("summary", ""), "references": request["context"], "created": time.time()}
        if not value["summary"]:
            fail("research_invalid", "A cached result needs a summary and precise source references")
        write(root, path, value)
        return {"pass": True, "status": "cached", "key": key}
    if not path.exists():
        return {"pass": True, "status": "miss", "key": key}
    value = load(path)
    stale = []
    for name, expected in value["hashes"].items():
        if name.startswith("@"):
            repo, local = name[1:].split("/", 1)
            source = inside(repository_root(root, repo), local)
        else:
            source = inside(root, name)
        if not source.is_file() or digest(source) != expected:
            stale.append(name)
    return {"pass": True, "status": "stale" if stale else "hit", "key": key,
            "summary": None if stale else value["summary"], "stale_sources": stale, "references": value["references"]}


def record_usage(root, request):
    if request.get("actor") not in {"orchestrator", "tool"}:
        fail("usage_invalid", "Agent usage belongs to finish-assignment; actor here is orchestrator|tool")
    observed = request.get("usage")
    if observed is not None and (not isinstance(observed, dict) or any(type(v) not in {int, float} or v < 0 for v in observed.values())):
        fail("usage_invalid", "Use observed nonnegative values, or null")
    if request.get("run_id"):
        run_load(root, request["run_id"])
    path = root / ".ai/gp/usage" / (uuid.uuid4().hex + ".json")
    write(root, path, {"version": 1, "time": time.time(), **request})
    return {"pass": True, "record": rel(root, path)}


def overlap(left, right):
    # Conservative overlap detection: ancestor prefixes overlap even for glob scopes.
    a = re.split(r"[?*[]", left, maxsplit=1)[0].rstrip("/")
    b = re.split(r"[?*[]", right, maxsplit=1)[0].rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/") or fnmatch.fnmatch(left, right) or fnmatch.fnmatch(right, left)


def assignment_path(root, key):
    return root / ".ai/gp/assignments" / (safe_id(key) + ".json")


def assign(root, run_id, request):
    contract(root, "assignment", request)
    p = policy(root)
    run = run_load(root, run_id)
    ensure_owner(root, run)
    current_card(root, run)
    if request.get("depth", 1) > p["max_delegation_depth"]:
        fail("delegation_depth_exceeded", "Return subtasks to the orchestrator")
    required = {"role", "goal", "context", "write_paths"}
    if not required <= request.keys() or not isinstance(request["write_paths"], list):
        fail("assignment_invalid", "Expected role, goal, context, write_paths")
    repo_name = request.get("repository", "project")
    workspace = repository_root(root, repo_name, bool(request["write_paths"]))
    for name in request["write_paths"]:
        inside(workspace, name)
        if name in {".", "**", "**/*", "*"} or name.startswith(("SPECS/", ".ai/gp/", "pipeline/", ".git/", ".env")):
            fail("assignment_scope_invalid", "Use bounded production/test paths; board/config is coordinator-owned")
    role = request["role"]
    if role in READ_ONLY and request["write_paths"]:
        fail("readonly_role", role)
    selection = route(root, request)
    packet = context_packet(root, request)
    with mutex(root):
        active = [load(path) for path in (root / ".ai/gp/assignments").glob("*.json")]
        active = [a for a in active if a["status"] == "ACTIVE"]
        if len(active) >= p["max_concurrent_agents"]:
            fail("agent_capacity", "Wait for an existing agent; do not spawn another")
        for other in active:
            if other["request"].get("repository", "project") != repo_name: continue
            for left in request["write_paths"]:
                if any(overlap(left, right) for right in other["request"]["write_paths"]):
                    fail("write_conflict", f"{left} overlaps assignment {other['id']}")
        previous = [load(path) for path in (root / ".ai/gp/assignments").glob("*.json")]
        attempts = sum(a["run_id"] == run_id and a["request"].get("stage", a["request"]["role"]) == request.get("stage", role) for a in previous)
        if attempts >= p["max_attempts_per_stage"]:
            fail("attempt_budget_exhausted", request.get("stage", role))
        key = run_id + "-" + uuid.uuid4().hex[:8]
        value = {"version": 1, "id": key, "run_id": run_id, "status": "ACTIVE", "started": time.time(),
                 "request": request, "selection": selection, "context": packet, "baseline": snapshot(root),
                 "actual_model": "unknown", "actual_reasoning": "unknown", "usage": None}
        write(root, assignment_path(root, key), value)
        run["assignments"].append(key)
        write(root, run_path(root, run_id), run)
    return {"pass": True, "assignment_id": key, "selection": selection, "context_chars": packet["chars"],
            "dispatch": dispatch(root, key)}


def dispatch(root, key):
    a = load(assignment_path(root, key))
    request, selection = a["request"], a["selection"]
    if request.get("execution_scope") == "evaluated-authoring":
        fail("isolated_workspace_required", "Export the neutral allowlist into a dedicated authoring repository before dispatch; never inherit this production workspace")
    prompt = ("Execute this bounded assignment. Do not delegate, change acceptance, edit gates, commit, or publish. "
              "Reviewers only report findings. Use Bash on every platform. Archive superseded files; never delete.\n"
              f"Assignment: {key}\nRole: {request['role']}\nGoal: {request['goal']}\n"
              f"Workspace: {repository_root(root, request.get('repository', 'project'))}\n"
              f"Allowed writes: {json.dumps(request['write_paths'])}\n"
              f"Acceptance: {json.dumps(request.get('acceptance', []))}\n"
              f"Prior failure and hypotheses: {json.dumps(request.get('repair_context', {}))}\n"
              "Return one JSON object with status, summary, changed_files, findings, checks, blockers. "
              "Do not copy full successful tool logs.\n\n" + a["context"]["text"])
    return {"tool": selection.get("tool", request.get("tool", "codex")), "model": selection.get("model"),
            "workspace": str(repository_root(root, request.get("repository", "project"))),
            "reasoning_effort": selection.get("reasoning"), "sandbox": selection.get("sandbox", "read-only"),
            "fork_history": False, "prompt": prompt,
            "instructions": "Use native subagent tools with these explicit settings; Claude selects and records a native model when null. A prompt mentioning a model alone does not select it. If unavailable, report model_unavailable; never silently substitute."}


def finish_assignment(root, key, result):
    contract(root, "result", result)
    a = load(assignment_path(root, key))
    if a["status"] != "ACTIVE":
        fail("assignment_finished", key)
    if result.get("status") not in {"DONE", "BLOCKED", "FAILED"}:
        fail("result_invalid", "status must be DONE|BLOCKED|FAILED")
    if not isinstance(result.get("changed_files", []), list):
        fail("result_invalid", "changed_files must be a list")
    changes = changed(a["baseline"], snapshot(root))
    repo_name = a["request"].get("repository", "project")
    prefix = "" if repo_name == "project" else "@" + repo_name + "/"
    claimed = result.get("changed_files", [])
    allowed = a["request"]["write_paths"]
    violations = [name for name in claimed if not any(fnmatch.fnmatch(name, pattern) or name.startswith(pattern.rstrip("/") + "/") for pattern in allowed)]
    # Changes made by other simultaneous owners are not attributed to this agent.
    peers = [load(p) for p in (root / ".ai/gp/assignments").glob("*.json") if p.stem != key]
    peer_scopes = [("" if other["request"].get("repository", "project") == "project" else "@" + other["request"]["repository"] + "/") + scope
                   for other in peers if other.get("finished", float("inf")) >= a["started"] for scope in other["request"]["write_paths"]]
    own_scopes = [prefix + name for name in allowed]
    for name in changes:
        if not any(fnmatch.fnmatch(name, pattern) or name.startswith(pattern.rstrip("/") + "/") for pattern in own_scopes + peer_scopes):
            violations.append(name)
    if violations:
        fail("write_scope_violation", ", ".join(sorted(set(violations))))
    expected = a["selection"].get("model")
    actual = result.get("actual_model", "unknown")
    if expected and actual != "unknown" and actual != expected:
        fail("model_mismatch", f"Requested {expected}; runtime reported {actual}")
    actual_reasoning = result.get("actual_reasoning", "unknown")
    if a["selection"].get("reasoning") and actual_reasoning != "unknown" and actual_reasoning != a["selection"]["reasoning"]:
        fail("reasoning_mismatch", f"Requested {a['selection']['reasoning']}; runtime reported {actual_reasoning}")
    usage = result.get("usage")
    if usage is not None and (not isinstance(usage, dict) or any(type(v) not in {int, float} or v < 0 for v in usage.values())):
        fail("usage_invalid", "Observed usage values must be nonnegative numbers, or null when unavailable")
    with mutex(root):
        a.update(status=result["status"], finished=time.time(), actual_model=actual,
                 actual_reasoning=actual_reasoning, usage=usage, result=result,
                 reviewed_source_sha256=json_hash(snapshot(root)))
        write(root, assignment_path(root, key), a)
        event(root, "assignment_finished", assignment=key, run_id=a["run_id"], result=result)
    return {"pass": True, "assignment_id": key, "status": a["status"], "actual_model": actual}


def gate_plan(root, run_id, final=False):
    config, run = project(root), run_load(root, run_id)
    card = current_card(root, run)
    delta = changed(run["baseline"], snapshot(root))
    required = card["meta"].get("gates", [])
    selected = []
    for gate in config["gates"]:
        applies = gate["id"] in required or gate.get("always", False) or any(fnmatch.fnmatch(name, pattern) for name in delta for pattern in gate.get("paths", []))
        if applies or final and gate.get("final", False):
            selected.append(gate)
    missing = set(required) - {g["id"] for g in config["gates"]}
    if missing:
        fail("gate_missing", ", ".join(sorted(missing)))
    return {"pass": True, "changed_files": delta, "gates": selected}


def run_gate(root, run_id, gate_id):
    run = run_load(root, run_id)
    ensure_owner(root, run)
    current_card(root, run)
    gate = next((g for g in project(root)["gates"] if g["id"] == gate_id), None)
    if not gate:
        fail("gate_missing", gate_id)
    stamp = uuid.uuid4().hex
    folder = root / "docs/evidence" / run["spec"] / run_id / stamp
    folder.mkdir(parents=True)
    gate_root = repository_root(root, gate.get("repository", "project"))
    argv = [x.replace("{root}", str(root)).replace("{repository}", str(gate_root)).replace("{evidence}", str(folder)) for x in gate["command"]]
    source_hash = json_hash(snapshot(root))
    started = time.time()
    log = folder / "stdout.log"
    error_log = folder / "stderr.log"
    result_file = None
    if gate.get("result") == "json-file":
        value = gate.get("result_path", "").replace("{evidence}", str(folder))
        result_file = inside(root, value)
        if not value or result_file.exists():
            fail("stale_gate_output", "JSON-file gates require a new {evidence}/ result path")
    try:
        with log.open("w", encoding="utf-8") as stdout, error_log.open("w", encoding="utf-8") as stderr:
            proc = subprocess.run(argv, cwd=inside(gate_root, gate.get("cwd", ".")), stdout=stdout, stderr=stderr,
                                  timeout=gate.get("timeout_seconds", 300), check=False)
        if gate.get("result", "json-line") == "exit-code":
            outcome = {"pass": proc.returncode == 0, "adapter": "explicit-exit-code", "exit_code": proc.returncode}
        elif result_file:
            outcome = load(result_file)
        else:
            lines = [line for line in read(log).splitlines() if line.strip()]
            if len(lines) != 1:
                fail("gate_protocol_invalid", "Gate must emit exactly one JSON line, or configure an explicit json-file/exit-code adapter")
            outcome = json.loads(lines[0])
        if not isinstance(outcome, dict) or type(outcome.get("pass")) is not bool:
            fail("gate_protocol_invalid", "Gate result needs a boolean pass")
        if proc.returncode != 0:
            outcome["pass"] = False
        if outcome.get("error_kind"):
            outcome["pass"] = False
    except subprocess.TimeoutExpired:
        outcome = {"pass": False, "error_kind": "gate_timeout"}
    except (OSError, ValueError) as exc:
        outcome = {"pass": False, "error_kind": "gate_execution_error", "errors": [str(exc)]}
    if source_hash != json_hash(snapshot(root)):
        outcome = {"pass": False, "error_kind": "source_changed_during_gate", "result": outcome}
    evidence = {"version": 1, "run_id": run_id, "gate": gate_id, "command": argv,
                "source_sha256": source_hash, "outcome": outcome, "started": started,
                "duration_seconds": time.time() - started, "stdout": rel(root, log), "stdout_sha256": digest(log),
                "stderr": rel(root, error_log), "stderr_sha256": digest(error_log)}
    path = folder / "gate.json"
    write(root, path, evidence)
    with mutex(root):
        run = run_load(root, run_id)
        run["gates"][gate_id] = {"path": rel(root, path), "sha256": digest(path), "source_sha256": source_hash}
        write(root, run_path(root, run_id), run)
    return {"pass": outcome["pass"], "gate": gate_id, "result": outcome, "evidence": rel(root, path)}


def verify_evidence(root, run, evidence):
    contract(root, "evidence", evidence)
    if evidence.get("run_id") != run["id"] or evidence.get("source_sha256") != json_hash(snapshot(root)):
        fail("evidence_stale", "Evidence must bind this run and current source snapshot")
    card = current_card(root, run)
    checks = evidence.get("acceptance", [])
    expected = card["meta"].get("acceptance_ids", [])
    if not expected:
        expected = ["AC" + str(i + 1) for i, line in enumerate([s for s in card["acceptance"].splitlines() if re.match(r"\s*(\d+[.)]|[-*])\s+", s)])]
    if not expected or {c.get("id") for c in checks} != set(expected):
        fail("acceptance_unmapped", "Provide exactly the SPEC acceptance IDs (AC1..ACn by list order unless gp-meta declares IDs)")
    if len(checks) != len(expected):
        fail("acceptance_unmapped", "Duplicate acceptance ID")
    for check in checks:
        if check.get("status") != "pass" or not check.get("evidence"):
            fail("acceptance_pending", str(check.get("id")))
        path = inside(root, check["evidence"])
        if not path.is_file() or check.get("sha256") != digest(path):
            fail("evidence_stale", str(path))
    required = gate_plan(root, run["id"], final=True)["gates"]
    if not required:
        fail("gate_missing", "Register at least one meaningful acceptance gate before completion")
    for gate in required:
        entry = run["gates"].get(gate["id"])
        if not entry:
            fail("gate_pending", gate["id"])
        path = inside(root, entry["path"])
        if not path.exists() or digest(path) != entry["sha256"]:
            fail("evidence_stale", gate["id"])
        value = load(path)
        if value["run_id"] != run["id"] or value["source_sha256"] != evidence["source_sha256"] or value["outcome"].get("pass") is not True:
            fail("gate_failed_or_stale", gate["id"])
        for field in ("stdout", "stderr"):
            log = inside(root, value[field])
            if not log.exists() or digest(log) != value[field + "_sha256"]:
                fail("evidence_stale", str(log))
    for art_id in card["meta"].get("art", []):
        asset = next((a for a in board(root, art=True) if a["id"] == art_id), None)
        if not asset or asset["status"] != "DONE" or not completion_exists(root, asset):
            fail("art_pending", art_id)
    if re.search(r"(?i)manual verification|manual_checks", read(root / card["path"])) and not evidence.get("manual"):
        fail("manual_pending", "Record the required actual manual checks, platform, performer and artifact")
    for manual in evidence.get("manual", []):
        if manual.get("status") != "pass" or not all(manual.get(k) for k in ("performer", "platform", "path", "sha256")):
            fail("manual_pending", "Incomplete manual evidence")
        path = inside(root, manual["path"])
        if not path.is_file() or digest(path) != manual["sha256"]:
            fail("evidence_stale", manual["path"])
    done = [load(assignment_path(root, key)) for key in run["assignments"]]
    if any(a["status"] == "ACTIVE" for a in done):
        fail("agents_active", "Wait for or finish all owned assignments")
    for role in ("reviewer", "verifier"):
        if not any(a["request"]["role"] == role and a["status"] == "DONE" and not a.get("result", {}).get("blockers")
                   and not any(isinstance(f, dict) and (f.get("severity") in {"blocker", "critical", "high"} or f.get("priority") in {0, 1}) for f in a.get("result", {}).get("findings", []))
                   and a.get("reviewed_source_sha256") == evidence["source_sha256"] for a in done):
            fail("independent_review_missing", role)


def close(root, run_id, state, evidence=None, reason=None):
    if state not in {"DONE", "BLOCKED", "REVIEW"}:
        fail("transition_invalid", state)
    run = run_load(root, run_id)
    if run["status"] == state and state == "DONE":
        with mutex(root):
            lock = root / ".ai/gp/claims" / (run["spec"] + ".json")
            if lock.exists() and load(lock)["run_id"] == run_id:
                target = root / "archive/gp-work/claims" / (run_id + "-reconciled.json")
                target.parent.mkdir(parents=True, exist_ok=True)
                lock.rename(target)
        return {"pass": True, "status": "DONE", "already_closed": True}
    with mutex(root):
        ensure_owner(root, run)
        card = current_card(root, run)
        if state == "DONE":
            if not evidence:
                fail("evidence_missing", "Completion requires an evidence JSON document")
            verify_evidence(root, run, evidence)
        elif not reason:
            fail("reason_missing", "BLOCKED/REVIEW must identify the concrete missing input/check")
        folder = root / "docs/evidence" / run["spec"] / run_id
        summary = {"version": 1, "run_id": run_id, "status": state, "reason": reason,
                   "changed_files": changed(run["baseline"], snapshot(root)), "evidence": evidence,
                   "closed": time.time()}
        path = folder / "completion.json"
        write(root, path, summary)
        set_status(root, card, state, rel(root, path) if state == "DONE" else None)
        run.update(status=state, evidence=rel(root, path))
        write(root, run_path(root, run_id), run)
        event(root, "run_closed", run_id=run_id, status=state, evidence=rel(root, path))
        handoff = root / ".ai/gp/handoff.md"
        write(root, handoff, f"# Execution handoff\n\nSPEC: {run['spec']}\nStatus: {state}\nRun: {run_id}\nEvidence: {rel(root, path)}\nRemaining: {reason or 'none'}\n")
        if state == "DONE":
            lock = ensure_owner(root, run)
            target = root / "archive/gp-work/claims" / (run_id + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            lock.rename(target)
    return {"pass": True, "status": state, "evidence": rel(root, path), "next": "Report completion; do not start another SPEC without batch authorization"}


def doctor(root):
    config = project(root)
    checks = []
    tools = {"python": sys.executable, "bash": "bash", "godot": os.environ.get("GODOT_BIN", "godot")}
    if config.get("art", {}).get("blender", False):
        tools["blender"] = os.environ.get("BLENDER_BIN", "blender")
    for name, executable in tools.items():
        resolved = shutil.which(executable)
        checks.append({"tool": name, "available": bool(resolved), "path": resolved})
    game = inside(root, config["project_dir"]) / "project.godot"
    checks.append({"tool": "project", "available": game.is_file(), "path": str(game)})
    if not config["gates"]:
        checks.append({"tool": "gate_registry", "available": False, "path": "pipeline/project.json"})
    return {"pass": all(c["available"] for c in checks), "checks": checks,
            "qualification": config.get("qualification", {}),
            "note": "Tool presence is not version, export-template, device or provider qualification; register those as real gates"}


def consistency(root):
    cards = board(root)
    findings = []
    lookup = {c["id"]: c for c in cards}
    visited = set()
    def walk(key, stack):
        if key in stack:
            findings.append({"kind": "dependency_cycle", "ids": stack + [key]})
            return
        if key in visited:
            return
        for dep in lookup[key]["dependencies"]:
            if dep in lookup:
                walk(dep, stack + [key])
            else:
                findings.append({"kind": "dependency_missing", "id": key, "dependency": dep})
        visited.add(key)
    for card in cards:
        walk(card["id"], [])
        if card["status"] == "DONE" and not completion_exists(root, card):
            findings.append({"kind": "completion_evidence_missing", "id": card["id"]})
    for name in ("README.md", "HANDOFF.md", "STATE.md", "SPECS/INDEX.md", "SPECS/README.md", "SPECS/SESSION.md"):
        path = root / name
        if not path.is_file():
            continue
        text = read(path)
        for match in re.finditer(r"\b(" + ID + r")\b[^.\n]{0,50}\b(?:is the next|next eligible|next slice)", text, re.I):
            key = match.group(1)
            if key in lookup and lookup[key]["status"] == "DONE":
                findings.append({"kind": "stale_next_task", "path": name, "id": key})
        for match in re.finditer(r"\[[^\]]+\]\(([^\)]+\.md)(?:#[^\)]*)?\)", text):
            target = match.group(1)
            if not re.match(r"[a-z]+:", target, re.I) and not (path.parent / target).is_file():
                findings.append({"kind": "broken_link", "path": name, "target": target})
        if name == "SPECS/INDEX.md":
            for card in cards:
                if not re.search(r"\[" + re.escape(card["id"]) + r"(?:\s|\])", text):
                    findings.append({"kind": "index_card_missing", "id": card["id"]})
            for line in text.splitlines():
                for card in cards:
                    if re.search(r"\[" + re.escape(card["id"]) + r"(?:\s|\])", line):
                        match = re.search(r"\b(BACKLOG|ACTIVE|BLOCKED|REVIEW|DONE)\b(?=[^|]*\|\s*$)", line)
                        if match and match.group(1) != card["status"]:
                            findings.append({"kind": "status_mismatch", "id": card["id"]})
                        break
    return {"pass": not findings, "findings": findings, "counts": {s: sum(c["status"] == s for c in cards) for s in sorted(STATES)}}


def metrics(root):
    records = [load(p) for p in (root / ".ai/gp/assignments").glob("*.json")]
    totals = {}
    for a in records:
        key = a.get("actual_model", "unknown")
        item = totals.setdefault(key, {"calls": 0, "done": 0, "failed": 0, "duration_seconds": 0, "observed_usage": {}, "unknown_usage_calls": 0})
        item["calls"] += 1
        item["done"] += a["status"] == "DONE"
        item["failed"] += a["status"] == "FAILED"
        item["duration_seconds"] += a.get("finished", a["started"]) - a["started"]
        if a.get("usage") is None:
            item["unknown_usage_calls"] += 1
        else:
            for kind, value in a["usage"].items():
                item["observed_usage"][kind] = item["observed_usage"].get(kind, 0) + value
    coordinator = [load(p) for p in (root / ".ai/gp/usage").glob("*.json")]
    return {"pass": True, "models": totals, "coordinator_and_tools": coordinator,
            "subscription_limits": "unavailable in portable runtime; read host usage tools when available", "api_cost": None}


def estimate_art(request):
    values = {name: request.get(name, 1) for name in ("assets", "variants", "facings", "frames")}
    if any(type(v) != int or v < 1 for v in values.values()):
        fail("art_estimate_invalid", "Counts must be positive integers")
    if any(type(request.get(name, 0)) != int or request.get(name, 0) < 0 for name in ("meshes", "rigs", "clips")):
        fail("art_estimate_invalid", "Mesh/rig/clip counts must be nonnegative integers")
    total = 1
    for value in values.values():
        total *= value
    return {"pass": True, "counts": values, "raster_outputs": total, "meshes": request.get("meshes", 0),
            "rigs": request.get("rigs", 0), "clips": request.get("clips", 0),
            "production_requires": ["approved reference sheet", "style/projection profile", "provenance", "runtime visual check"],
            "model": "Astra high for Codex Blender recipes; native expert tier for Claude; repeat builds use scripts"}


def upgrade_preview(root, generated):
    stage = inside(root, generated)
    if not stage.is_dir() or stage == root:
        fail("preview_invalid", "Provide the isolated generated directory under archive/")
    changes = []
    protected = {"STATE.md", "ROADMAP.md", "DOCUMENTATION.md", "pipeline/profile.json", "pipeline/project.json",
                 "pipeline/model-policy.json", "pipeline/qa-contract.json", "pipeline/toolchain.json"}
    for source in files(stage):
        name = rel(stage, source)
        destination = root / name
        if destination.is_file():
            preserve_file = name in protected or name.startswith(("SPECS/", "art/")) or "/specs/" in name
            if name in {"AGENTS.md", "CLAUDE.md"} and not re.search(r"Generated by game-pipeline|^# Claude adapter$", read(destination), re.M):
                preserve_file = True
            if preserve_file:
                changes.append({"path": name, "action": "preserve"})
                continue
            if source.read_bytes() == destination.read_bytes(): continue
            try:
                diff = "".join(difflib.unified_diff(read(destination).splitlines(True), read(source).splitlines(True), fromfile=name, tofile=name))
                changes.append({"path": name, "action": "update", "diff": diff[:16000], "truncated": len(diff) > 16000})
            except UnicodeError:
                changes.append({"path": name, "action": "update", "old_sha256": digest(destination), "new_sha256": digest(source)})
        else:
            changes.append({"path": name, "action": "add", "sha256": digest(source)})
    return {"pass": True, "applied": False, "generated": str(stage), "changes": changes}


def validate_schema(instance, schema, path="$"):
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool, "null": type(None)}
    expected = schema.get("type")
    if expected and (not isinstance(instance, types[expected]) or expected in {"number", "integer"} and isinstance(instance, bool)):
        fail("schema_invalid", path + ": expected " + expected)
    if "enum" in schema and instance not in schema["enum"]:
        fail("schema_invalid", path + ": invalid enum")
    if isinstance(instance, dict):
        missing = set(schema.get("required", [])) - instance.keys()
        if missing:
            fail("schema_invalid", path + ": missing " + ", ".join(sorted(missing)))
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and instance.keys() - props.keys():
            fail("schema_invalid", path + ": unknown fields")
        for key, value in instance.items():
            if key in props:
                validate_schema(value, props[key], path + "." + key)
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail("schema_invalid", path + ": too few items")
        for i, value in enumerate(instance):
            validate_schema(value, schema.get("items", {}), path + f"[{i}]")
    if isinstance(instance, str) and "pattern" in schema and not re.search(schema["pattern"], instance):
        fail("schema_invalid", path + ": pattern mismatch")
    if type(instance) in {int, float} and instance < schema.get("minimum", float("-inf")):
        fail("schema_invalid", path + ": below minimum")


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("adopt", "migrate"):
        command = sub.add_parser(name)
        command.add_argument("--apply", action="store_true")
        if name == "migrate":
            command.add_argument("--plan", required=True)
    sub.add_parser("discover").add_argument("--tool", choices=["codex", "claude"], default="codex")
    for name in ("doctor", "consistency", "metrics", "snapshot", "sync-index"):
        sub.add_parser(name)
    for name in ("next", "status"):
        command = sub.add_parser(name)
        command.add_argument("--track")
        command.add_argument("--spec")
    command = sub.add_parser("claim")
    command.add_argument("--spec", required=True)
    command.add_argument("--owner", required=True)
    command.add_argument("--recover-stale", action="store_true")
    sub.add_parser("recover-mutation").add_argument("--pid", type=int, required=True)
    for name in ("resume", "checkpoint", "assign", "gates", "gate", "close"):
        command = sub.add_parser(name)
        command.add_argument("--run", required=True)
        if name == "checkpoint":
            command.add_argument("--stage", required=True)
            command.add_argument("--note", required=True)
        if name == "assign":
            command.add_argument("--request", required=True)
        if name == "gates":
            command.add_argument("--final", action="store_true")
        if name == "gate":
            command.add_argument("--id", required=True)
        if name == "close":
            command.add_argument("--status", required=True)
            command.add_argument("--evidence")
            command.add_argument("--reason")
    for name in ("route", "context", "art-estimate", "record-usage"):
        sub.add_parser(name).add_argument("--request", required=True)
    command = sub.add_parser("research-cache")
    command.add_argument("--key", required=True)
    command.add_argument("--request")
    for name in ("dispatch", "finish-assignment"):
        command = sub.add_parser(name)
        command.add_argument("--assignment", required=True)
        if name == "finish-assignment":
            command.add_argument("--result", required=True)
    command = sub.add_parser("validate")
    command.add_argument("--schema", required=True)
    command.add_argument("--file", required=True)
    sub.add_parser("upgrade-preview").add_argument("--generated", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        fail("project_missing", str(root))
    name = args.command
    if name == "adopt": return adopt(root, args.apply)
    if name == "discover": return discover(root, args.tool)
    if name == "migrate": return migrate(root, load(inside(root, args.plan)), args.apply)
    if name in {"next", "status"}:
        rows = ready(root, board(root), args.track, args.spec)
        eligible = [row for row in rows if row["ready"]]
        return {"pass": True, "status": "ready" if eligible else "backlog_empty" if not any(c["status"] != "DONE" for c in board(root)) else "no_ready_tasks", "selected": eligible[0] if eligible else None, "tasks": rows if name == "status" else []}
    if name == "claim": return claim(root, args.spec, args.owner, args.recover_stale)
    if name == "recover-mutation": return recover_mutation(root, args.pid)
    if name == "resume": return resume(root, args.run)
    if name == "checkpoint": return checkpoint(root, args.run, args.stage, args.note)
    if name == "route": return route(root, load(inside(root, args.request)))
    if name == "context": return {"pass": True, **context_packet(root, load(inside(root, args.request)))}
    if name == "research-cache": return research_cache(root, args.key, load(inside(root, args.request)) if args.request else None)
    if name == "record-usage": return record_usage(root, load(inside(root, args.request)))
    if name == "assign": return assign(root, args.run, load(inside(root, args.request)))
    if name == "dispatch": return {"pass": True, **dispatch(root, args.assignment)}
    if name == "finish-assignment": return finish_assignment(root, args.assignment, load(inside(root, args.result)))
    if name == "gates": return gate_plan(root, args.run, args.final)
    if name == "gate": return run_gate(root, args.run, args.id)
    if name == "close": return close(root, args.run, args.status, load(inside(root, args.evidence)) if args.evidence else None, args.reason)
    if name == "doctor": return doctor(root)
    if name == "consistency": return consistency(root)
    if name == "metrics": return metrics(root)
    if name == "snapshot": return {"pass": True, "source_sha256": json_hash(snapshot(root))}
    if name == "art-estimate": return estimate_art(load(inside(root, args.request)))
    if name == "upgrade-preview": return upgrade_preview(root, args.generated)
    if name == "sync-index":
        with mutex(root): sync_index(root)
        return {"pass": True}
    if name == "validate":
        validate_schema(load(inside(root, args.file)), load(inside(root, args.schema)))
        return {"pass": True}


if __name__ == "__main__":
    try:
        output = main()
    except WorkError as exc:
        output = {"pass": False, "error_kind": exc.kind, "errors": [exc.detail]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        output = {"pass": False, "error_kind": "runtime_error", "errors": [str(exc)]}
    print(json.dumps(output, ensure_ascii=True))
    sys.exit(0 if output.get("pass") else 1)
