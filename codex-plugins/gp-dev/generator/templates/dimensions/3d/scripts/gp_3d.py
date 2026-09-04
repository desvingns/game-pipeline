"""Bounded, evidence-producing Godot gates. Bash is the public interface."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid


class GateError(Exception):
    def __init__(self, kind, message):
        self.kind = kind
        super().__init__(message)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise GateError("bad_usage", message)


def read_json(path):
    def invalid(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def inside(value, root=None):
    root = (root or Path.cwd()).resolve()
    value = str(value)
    if os.name == "nt" and re.match(r"^/[a-zA-Z]/", value):
        value = value[1] + ":" + value[2:]
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise GateError("bad_path", "Path escapes project: " + value)
    return path


def run_dir(label, base="out/gp-runs"):
    path = Path(base) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + label + "-" + uuid.uuid4().hex[:10])
    path.mkdir(parents=True)
    return path.resolve()


def run_process(args, log, timeout=180):
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 3600:
        raise GateError("bad_usage", "Timeout must be within (0, 3600] seconds")
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    started = time.monotonic()
    proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", **kwargs)
    expired = False
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=15)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate(timeout=15)
    Path(log).write_text(output, encoding="utf-8")
    if expired:
        raise GateError("process_timeout", "Deadline exceeded; log: " + str(log))
    if proc.returncode != 0 or re.search(r"(?:SCRIPT ERROR:|Parse Error:|^ERROR:|Traceback \(most recent call last\))", output, re.M):
        raise GateError("process_failed", "Process failed (%s); log: %s" % (proc.returncode, log))
    return output, time.monotonic() - started


def binary(kind):
    env_name = "GODOT_BIN" if kind == "godot" else "BLENDER_BIN"
    specified = os.environ.get(env_name)
    if specified:
        path = Path(specified)
        found = shutil.which(specified) or (str(path) if path.is_file() else None)
        if found:
            return found
        raise GateError(kind + "_not_found", "Invalid " + env_name)
    candidates = ["godot4", "godot"] if kind == "godot" else ["blender"]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    if kind == "blender":
        roots = [Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Blender Foundation"]
        for root in roots:
            found = sorted(root.glob("Blender */blender.exe"), reverse=True)
            if found:
                return str(found[0])
        mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
        if mac.is_file():
            return str(mac)
    raise GateError(kind + "_not_found", "Set " + env_name + " to the executable")


def version(kind, exe, directory):
    out, _ = run_process([exe, "--version"], directory / (kind + "-version.log"), 20)
    first = out.strip().splitlines()[0]
    pins = Path("pipeline/toolchain.json")
    if pins.is_file():
        expected = read_json(pins).get(kind)
        if expected and expected != first:
            raise GateError("toolchain_mismatch", "%s: expected %r, observed %r" % (kind, expected, first))
    return first


def payload(output, marker):
    lines = [line[len(marker):] for line in output.splitlines() if line.startswith(marker)]
    if len(lines) != 1:
        raise GateError("harness_contract", "Expected exactly one " + marker + " payload")
    try:
        value = json.loads(lines[0], parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    except ValueError as exc:
        raise GateError("harness_contract", str(exc)) from exc
    if not isinstance(value, dict):
        raise GateError("harness_contract", "Payload must be an object")
    return value


def project_path(value):
    path = inside(value)
    if not (path / "project.godot").is_file():
        raise GateError("project_missing", "No project.godot under " + str(path))
    return path


def init_harness(args):
    project = project_path(args.project)
    target = project / "tools/gates"
    target.mkdir(parents=True, exist_ok=True)
    created, preserved = [], []
    for source in Path("pipeline/harness").glob("*.gd"):
        dest = target / source.name
        if dest.exists():
            preserved.append(str(dest))
        else:
            shutil.copy2(source, dest)
            created.append(str(dest))
    for name, data in (("gp_suites.json", []), ("gp_scenarios.json", {})):
        dest = project / "tests" / name
        if not dest.exists():
            write_json(dest, data)
            created.append(str(dest))
    export_template = Path("pipeline/harness/export_presets.cfg")
    if not (project / "export_presets.cfg").exists() and export_template.is_file():
        shutil.copy2(export_template, project / "export_presets.cfg")
        created.append(str(project / "export_presets.cfg"))
    if not created and not preserved:
        raise GateError("harness_missing", "No bundled harness templates")
    return {"pass": True, "action": "init_harness", "created": created, "preserved": preserved,
            "readiness": "Register actual suites and scenario scenes; empty manifests fail gates."}


def runner(args):
    project = project_path(args.project)
    exe = binary("godot")
    directory = run_dir("build")
    engine = version("godot", exe, directory)
    run_process([exe, "--headless", "--path", project, "--import"], directory / "import.log", args.timeout)
    test_script = project / "tools/gates/unit_runner.gd"
    if not test_script.is_file():
        raise GateError("test_harness_missing", "Run fps-godot.sh --init-harness, then register suites")
    out, _ = run_process([exe, "--headless", "--path", project, "--script", "res://tools/gates/unit_runner.gd"], directory / "tests.log", args.timeout)
    tests = payload(out, "GP_TEST_RESULT=")
    if tests.get("pass") is not True or type(tests.get("assertions")) is not int or tests["assertions"] < 1 or tests.get("failures") != []:
        raise GateError("tests_failed", "No passing assertions or failures reported; " + str(directory / "tests.log"))
    result = {"pass": True, "import": "ok", "tests": tests, "export": "skipped", "godot": engine, "logs": str(directory)}
    if args.export:
        output = inside(args.out or os.environ.get("GP_EXPORT_OUT", "build/{{PREFIX}}.exe"))
        if output.suffix.lower() != ".exe":
            raise GateError("bad_usage", "Windows output must end in .exe")
        # Export to a fresh staging folder: old executables/PCK files cannot pass.
        package = directory / "package"
        package.mkdir()
        artifact = package / output.name
        run_process([exe, "--headless", "--path", project, "--export-release", os.environ.get("GP_EXPORT_PRESET", "Windows Desktop"), artifact], directory / "export.log", args.timeout)
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise GateError("export_missing", "Exporter produced no executable")
        # Smoke runs the exported game, with its normal main scene and QA bridge.
        run_id = uuid.uuid4().hex
        out, _ = run_process([artifact, "--headless", "--", "--gp-export-smoke=1", "--gp-scenario=smoke", "--gp-run-id=" + run_id, "--gp-seed=4242"], directory / "exe-smoke.log", args.timeout)
        smoke = payload(out, "GP_QA_RESULT=")
        validate_qa(smoke, "smoke", run_id, 4242)
        # Deliver the complete package in its own directory; retain previous files.
        output.parent.mkdir(parents=True, exist_ok=True)
        for item in package.iterdir():
            if not item.is_file():
                raise GateError("export_layout", "Unexpected subdirectory in export package")
            dest = output.parent / item.name
            if dest.exists():
                previous = directory / "previous-package"
                previous.mkdir(exist_ok=True)
                shutil.move(str(dest), previous / dest.name)
            shutil.copy2(item, dest)
        result.update(export=str(output), executable_smoke=smoke)
    return result


def validate_qa(data, scenario, run_id, seed):
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1 or data.get("run_id") != run_id or data.get("scenario") != scenario or type(data.get("seed")) is not int or data["seed"] != seed:
        raise GateError("harness_contract", "Scenario/seed/run identity mismatch")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise GateError("harness_contract", "No behavioral checks ran")
    ids = set()
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str) or type(check.get("pass")) is not bool or not str(check.get("observed", "")).strip():
            raise GateError("harness_contract", "Every check requires id, boolean pass and observed evidence")
        if check["id"] in ids:
            raise GateError("harness_contract", "Duplicate check id")
        ids.add(check["id"])
    required = read_json("pipeline/qa-contract.json")["scenarios"].get(scenario)
    if not required or not set(required).issubset(ids):
        raise GateError("harness_contract", "Missing required scenario checks: " + str(required))
    if data.get("pass") is not True or not all(check["pass"] for check in checks):
        raise GateError("scenario_failed", "Behavioral checks failed for " + scenario)
    if scenario == "network":
        peers = data.get("peers")
        if not isinstance(peers, list) or len(peers) < 2:
            raise GateError("peer_evidence_missing", "Network scenarios require at least two process receipts")
        pids = set()
        for peer in peers:
            if not isinstance(peer, dict) or type(peer.get("pid")) is not int or peer["pid"] <= 0 or peer["pid"] in pids or peer.get("run_id") != run_id:
                raise GateError("peer_evidence_invalid", "Expected distinct process ids with this run id")
            pids.add(peer["pid"])
            log = inside(peer.get("log", ""))
            if not log.is_file() or ("GP_PEER_READY=" + run_id) not in log.read_text(encoding="utf-8"):
                raise GateError("peer_evidence_invalid", "Peer log lacks the current connection-ready marker")


def scenarios(args):
    if args.init_harness:
        return init_harness(args)
    project = project_path(args.project)
    exe = binary("godot")
    contract = read_json("pipeline/qa-contract.json")
    selected = list(contract["scenarios"]) if args.all else [args.scenario or "smoke"]
    if not args.all and selected[0] not in contract["scenarios"]:
        raise GateError("bad_usage", "Unknown scenario")
    directory = run_dir("playtest")
    engine = version("godot", exe, directory)
    results = []
    for scenario in selected:
        run_id = uuid.uuid4().hex
        screenshot = directory / (scenario + ".png")
        rendered = scenario in ("visual", "perf", "ui")
        command = [exe, "--path", project]
        if not rendered:
            command.append("--headless")
        else:
            command += ["--resolution", "1280x720", "--position", "80,80"]
        # The host loads actual game-specific tests. Missing registration fails.
        command += ["--script", "res://tools/gates/qa_host.gd", "--", "--gp-scenario=" + scenario,
                    "--gp-run-id=" + run_id, "--gp-seed=" + str(args.seed), "--gp-shot=" + str(screenshot)]
        out, elapsed = run_process(command, directory / (scenario + ".log"), args.timeout)
        data = payload(out, "GP_QA_RESULT=")
        validate_qa(data, scenario, run_id, args.seed)
        if rendered:
            if not screenshot.is_file() or screenshot.stat().st_size < 100:
                raise GateError("screenshot_missing", "No fresh rendered screenshot")
            if screenshot.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                raise GateError("screenshot_invalid", "Capture is not PNG")
        if scenario == "perf":
            metrics = data.get("metrics", {})
            limits = contract["performance"]
            for name in ("frames", "fps", "p95_frame_ms", "width", "height"):
                value = metrics.get(name)
                if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
                    raise GateError("harness_contract", "Invalid measured metric: " + name)
            if metrics["frames"] < limits["min_frames"] or metrics["fps"] < limits["min_fps"] or metrics["p95_frame_ms"] > limits["max_p95_frame_ms"] or [metrics["width"], metrics["height"]] != [1280, 720]:
                raise GateError("performance_failed", "Measured frame timings/resolution violate pipeline/qa-contract.json; " + str(directory))
        results.append({"scenario": scenario, "pass": True, "elapsed_seconds": round(elapsed, 3), "result": data,
                        "screenshot": str(screenshot) if rendered else None})
    return {"pass": True, "godot": engine, "scenarios": results, "logs": str(directory),
            "review_required": ["control feel", "visual quality", "audio", "difficulty"]}


def main():
    parser = Parser(add_help=False)
    parser.add_argument("action", choices=["runner", "fps", "doctor", "replay"])
    parser.add_argument("--project", default=os.environ.get("GP_PROJECT_DIR", "game"))
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--out")
    parser.add_argument("--init-harness", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true")
    group.add_argument("--scenario")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args()
    if args.action == "runner":
        return runner(args)
    if args.action == "fps":
        return scenarios(args)
    if args.action == "replay":
        if not 2 <= args.runs <= 20:
            raise GateError("bad_usage", "Replay requires 2 to 20 independent processes")
        project = project_path(args.project)
        if not (project / "tests/gp_replay.gd").is_file():
            raise GateError("harness_missing", "Implement the pure-rules tests/gp_replay.gd")
        exe = binary("godot")
        directory = run_dir("replay")
        engine = version("godot", exe, directory)
        hashes = []
        for index in range(args.runs):
            out, _ = run_process([exe, "--headless", "--path", project, "--script", "res://tools/gates/replay_runner.gd", "--", "--gp-seed=" + str(args.seed)], directory / (str(index) + ".log"), args.timeout)
            data = payload(out, "GP_REPLAY_RESULT=")
            if data.get("seed") != args.seed or not re.fullmatch("[0-9a-f]{64}", str(data.get("hash", ""))):
                raise GateError("harness_contract", "Invalid replay result")
            hashes.append(data["hash"])
        return {"pass": len(set(hashes)) == 1, "scope": "pure_rules", "godot": engine, "seed": args.seed, "runs": args.runs, "hashes": hashes, "logs": str(directory)}
    directory = run_dir("doctor")
    return {"pass": True, "python": sys.version.split()[0], **{kind: version(kind, binary(kind), directory) for kind in ("godot", "blender")}, "logs": str(directory)}


def entry(function):
    try:
        result = function()
    except GateError as exc:
        result = {"pass": False, "error_kind": exc.kind, "errors": [str(exc)]}
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        result = {"pass": False, "error_kind": "contract_invalid", "errors": [str(exc)]}
    except Exception as exc:
        result = {"pass": False, "error_kind": "internal_error", "errors": [type(exc).__name__ + ": " + str(exc)]}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    entry(main)
