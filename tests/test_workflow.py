"""Behavioral tests of the portable workflow; fixtures are retained under out/."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import uuid

# The default tests pin the project-local archive; SharedArchiveTests opts in explicitly.
os.environ.pop("PET_ARCHIVE_ROOT", None)
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "templates/common/scripts/gp_work.py"
spec = importlib.util.spec_from_file_location("work", SOURCE)
work = importlib.util.module_from_spec(spec)
spec.loader.exec_module(work)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "out/workflow-tests" / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        work.adopt(self.root, True)
        (self.root / "SPECS/backlog").mkdir(parents=True)
        (self.root / "SPECS/done").mkdir()

    def put(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text if isinstance(text, str) else json.dumps(text), encoding="utf-8")
        return p

    def card(self, key="TASK-1", deps=(), status="BACKLOG", meta=None):
        where = "done" if status == "DONE" else "backlog"
        text = f"# {key} — Observable behavior\n\nStatus: **{status}**\n\n## Goal\nA useful result.\n\n## Dependencies\n"
        text += "\n".join("- " + d for d in deps)
        text += "\n\n## Acceptance criteria\n1. The observable behavior works.\n"
        if meta:
            text += "\n<!-- gp-meta " + json.dumps(meta) + " -->\n"
        return self.put(f"SPECS/{where}/{key}.md", text)

    def assert_error(self, kind, callable, *args, **kwargs):
        with self.assertRaises(work.WorkError) as exc:
            callable(*args, **kwargs)
        self.assertEqual(kind, exc.exception.kind, str(exc.exception))

    def run_start(self):
        self.card()
        self.put("domain/rule.py", "VALUE = 1\n")
        return work.claim(self.root, "TASK-1", "test-session")["run_id"]

    def request(self, role="developer", paths=None):
        return {"role": role, "goal": "Implement the bounded rule", "tool": "codex", "complexity": "simple",
                "context": ["SPECS/backlog/TASK-1.md"], "write_paths": paths if paths is not None else ["domain/rule.py"]}

    def light_request(self, role="developer", tool="codex", risk=None):
        return {"role": role, "goal": "exercise light routing", "tool": tool, "complexity": "simple", "profile": "light",
                "risk": risk or {}, "context": ["SPECS/backlog/TASK-1.md"],
                "write_paths": [] if role in {"reviewer", "verifier"} else ["domain/rule.py"], "attempt": 1}

    def finish(self, assignment, changed=None):
        return work.finish_assignment(self.root, assignment, {"status": "DONE", "summary": "Checked", "changed_files": changed or [],
                                                              "findings": [], "checks": [], "blockers": []})

    def test_parse_plain_dependencies_and_metadata_hash(self):
        self.card(deps=["TASK-2"])
        c = work.board(self.root)[0]
        self.assertEqual(["TASK-2"], c["dependencies"])
        evidence = self.put("docs/evidence/TASK-1/summary.json", {"pass": True})
        work.set_status(self.root, c, "DONE", str(evidence))
        after = work.board(self.root)[0]
        self.assertEqual(c["acceptance_sha256"], after["acceptance_sha256"])
        self.assertTrue(work.completion_exists(self.root, after))
        evidence.write_text("tampered", encoding="utf-8")
        self.assertFalse(work.completion_exists(self.root, after))

    def test_ready_requires_dependency_evidence_and_acceptance(self):
        self.card("TASK-1", status="DONE")
        self.card("TASK-2", deps=["TASK-1"])
        rows = work.ready(self.root, work.board(self.root))
        self.assertFalse(next(c for c in rows if c["id"] == "TASK-2")["ready"])
        self.put("SPECS/backlog/TASK-3.md", "# TASK-3 — Empty\nStatus: BACKLOG\n")
        self.assert_error("spec_not_ready", work.claim, self.root, "TASK-3", "session")

    def test_numeric_card_does_not_crash(self):
        p = self.put("SPECS/backlog/001-feature.md", "# Small feature\n\n## Acceptance criteria\n1. It works.\n")
        self.assertEqual("general", work.parse_card(self.root, p)["track"])

    def test_shared_board_order_and_track(self):
        self.card("H12")
        self.card("C01")
        self.put("SPECS/INDEX.md", "# Board\n\n| [H12](backlog/H12.md) | BACKLOG |\n| [C01](backlog/C01.md) | BACKLOG |\n")
        self.assertEqual("H12", work.ready(self.root, work.board(self.root))[0]["id"])
        self.assertEqual("C01", work.ready(self.root, work.board(self.root), "C")[0]["id"])

    def test_claim_conflict_and_same_run_recovery(self):
        run_id = self.run_start()
        work.checkpoint(self.root, run_id, "test", "Implement complete")
        self.assert_error("spec_claimed", work.claim, self.root, "TASK-1", "other")
        claim_path = self.root / ".ai/gp/claims/TASK-1.json"
        claim = work.load(claim_path)
        claim["heartbeat"] = time.time() - 7200
        work.write(self.root, claim_path, claim)
        recovered = work.claim(self.root, "TASK-1", "new-owner", True)
        self.assertEqual(run_id, recovered["run_id"])
        self.assertEqual("test", recovered["stage"])
        self.assertEqual("new-owner", work.run_load(self.root, run_id)["owner"])

    def test_resume_detects_acceptance_change(self):
        run_id = self.run_start()
        path = self.root / "SPECS/backlog/TASK-1.md"
        path.write_text(work.read(path).replace("behavior works", "behavior changes"), encoding="utf-8")
        self.assert_error("acceptance_changed", work.resume, self.root, run_id)

    def test_codex_exact_tiers_and_claude_policy(self):
        for tier, model, effort in [("simple", "gpt-5.6-luna", "xhigh"), ("complex", "gpt-5.6-sol", "xhigh"), ("expert", "gpt-6-astra", "high")]:
            selected = work.route(self.root, {"complexity": tier})
            self.assertEqual((model, effort), (selected["model"], selected["reasoning"]))
        self.assertEqual("expert", work.route(self.root, {"risk": {"blender": True}})["tier"])
        self.assertEqual("complex", work.route(self.root, {"attempt": 2, "failure_kind": "reasoning"})["tier"])
        self.assert_error("external_blocker", work.route, self.root, {"attempt": 2, "failure_kind": "environment"})
        # The spawn carries the tier model; effort is the developer agent's pinned xhigh.
        for tier, model, effort in [("simple", "claude-sonnet-5", "medium"), ("complex", "claude-sonnet-5", "xhigh"), ("expert", "claude-opus-5", "xhigh")]:
            selected = work.route(self.root, {"tool": "claude", "role": "developer", "complexity": tier})
            self.assertEqual((model, effort, "xhigh", "agent-frontmatter"),
                             (selected["model"], selected["tier_reasoning"], selected["reasoning"], selected["effort_source"]))
        docs = work.route(self.root, {"tool": "claude", "role": "docs", "complexity": "expert"})
        self.assertEqual(("claude-opus-5", "medium", "xhigh"), (docs["model"], docs["reasoning"], docs["tier_reasoning"]))
        self.assertTrue(any("no per-spawn effort" in reason for reason in docs["reasons"]))
        config = work.policy(self.root)
        config["claude"] = {"mode": "auto", "tiers": {}, "orchestrator": {}}
        self.put("pipeline/model-policy.json", config)
        legacy = work.route(self.root, {"tool": "claude", "role": "developer"})
        self.assertEqual(("claude-sonnet-5", "xhigh"), (legacy["model"], legacy["reasoning"]))
        config["claude"]["tiers"]["simple"] = {"model": "native-test-model", "reasoning": "high"}
        config["claude"]["role_tiers"] = {"developer": "simple"}
        self.put("pipeline/model-policy.json", config)
        explicit = work.route(self.root, {"tool": "claude", "role": "developer"})
        self.assertEqual(("native-test-model", "high", "high"), (explicit["model"], explicit["reasoning"], explicit["tier_reasoning"]))
        config["claude"]["mode"] = "native"
        self.put("pipeline/model-policy.json", config)
        native = work.route(self.root, {"tool": "claude"})
        self.assertEqual((None, None, "session"), (native["model"], native["reasoning"], native["effort_source"]))
        for broken in ({"tiers": {"simple": {"model": "m", "reasoning": "extreme"}}}, {"role_tiers": {"docs": "huge"}}, {"max_turns": {"runner": 0}}):
            self.put("pipeline/model-policy.json", config | {"claude": broken})
            self.assert_error("policy_invalid", work.policy, self.root)
        self.put("pipeline/model-policy.json", config | {"claude": {"mode": "guess"}})
        self.assert_error("schema_invalid", work.policy, self.root)

    def test_claude_dispatch_reports_pinned_effort_strictly(self):
        run_id = self.run_start()
        a = work.assign(self.root, run_id, self.request() | {"tool": "claude"})
        d = a["dispatch"]
        self.assertEqual(("claude", "claude-sonnet-5", "xhigh", "medium", "agent-frontmatter"),
                         (d["tool"], d["model"], d["reasoning_effort"], d["tier_reasoning_effort"], d["effort_source"]))
        self.put("domain/rule.py", "VALUE = 2\n")
        result = {"status": "DONE", "summary": "Changed", "changed_files": ["domain/rule.py"], "findings": [], "checks": [],
                  "blockers": [], "actual_model": "claude-sonnet-5", "actual_reasoning": "medium"}
        self.assert_error("reasoning_mismatch", work.finish_assignment, self.root, a["assignment_id"], result)
        result["actual_reasoning"] = "xhigh"
        self.assertEqual("DONE", work.finish_assignment(self.root, a["assignment_id"], result)["status"])

    def test_light_profile_derives_from_tiers_for_both_tools(self):
        # Zero-config default: no policy.profiles.light configured anywhere.
        limits = work.profile_config(work.policy(self.root), "light")
        self.assertEqual((1, 2, 12000), (limits["max_concurrent_agents"], limits["max_attempts_per_stage"], limits["context_chars"]))
        codex_dev = work.route(self.root, self.light_request("developer", "codex"))
        self.assertEqual(("gpt-6-astra", "high", "light", "light-implementer"),
                         (codex_dev["model"], codex_dev["reasoning"], codex_dev["profile"], codex_dev["tier"]))
        for role in ("reviewer", "verifier"):
            closer = work.route(self.root, self.light_request(role, "codex"))
            self.assertEqual(("gpt-5.6-luna", "xhigh", "read-only"), (closer["model"], closer["reasoning"], closer["sandbox"]))
        claude_dev = work.route(self.root, self.light_request("developer", "claude"))
        self.assertEqual(("claude-opus-5", "xhigh", "xhigh", "agent-frontmatter"),
                         (claude_dev["model"], claude_dev["reasoning"], claude_dev["tier_reasoning"], claude_dev["effort_source"]))
        claude_closer = work.route(self.root, self.light_request("reviewer", "claude"))
        # reviewer's pinned frontmatter effort (xhigh, the "complex" default) does not match the
        # light/simple target (medium): reported honestly instead of silently claimed.
        self.assertEqual(("claude-sonnet-5", "xhigh", "medium"), (claude_closer["model"], claude_closer["reasoning"], claude_closer["tier_reasoning"]))
        self.assertTrue(any("no per-spawn effort" in reason for reason in claude_closer["reasons"]))

    def test_light_profile_explicit_override_and_guards(self):
        config = work.policy(self.root)
        config["profiles"] = {"light": {"implementer": {"model": "custom-impl", "reasoning": "high"},
                                         "closer": {"model": "custom-closer", "reasoning": "low"},
                                         "max_concurrent_agents": 1, "max_attempts_per_stage": 2, "context_chars": 500}}
        config["claude"]["profiles"] = {"light": {"implementer": {"model": "claude-custom", "reasoning": "high"}}}
        self.put("pipeline/model-policy.json", config)
        self.assertEqual("custom-impl", work.route(self.root, self.light_request("developer", "codex"))["model"])
        self.assertEqual("custom-closer", work.route(self.root, self.light_request("reviewer", "codex"))["model"])
        self.assertEqual("claude-custom", work.route(self.root, self.light_request("developer", "claude"))["model"])
        self.assert_error("light_role_not_allowed", work.route, self.root, self.light_request("tester", "codex"))
        self.assert_error("light_profile_incompatible", work.route, self.root,
                          self.light_request("developer", "codex") | {"execution_scope": "evaluated-authoring", "frozen_model": "x", "allowlist": ["x"]})
        for risk in ("blender", "replay_codec", "concurrency", "critical_lifecycle", "data_loss"):
            self.assert_error("light_risk_requires_standard", work.route, self.root, self.light_request("developer", "codex", {risk: True}))
        self.assert_error("external_blocker", work.route, self.root, self.light_request("developer", "codex") | {"failure_kind": "environment"})
        self.assert_error("attempt_budget_exhausted", work.route, self.root, self.light_request("developer", "codex") | {"attempt": 3})
        for broken in ({"implementer": {"model": 1, "reasoning": "high"}}, {"max_attempts_per_stage": 0}):
            self.put("pipeline/model-policy.json", config | {"profiles": {"light": broken}})
            self.assert_error("policy_invalid", work.policy, self.root)

    def test_claim_light_profile_recovery_and_metrics(self):
        self.card()
        self.put("domain/rule.py", "VALUE = 1\n")
        claimed = work.claim(self.root, "TASK-1", "session-a", profile_name="light")
        self.assertEqual("light", claimed["profile"])
        self.assertEqual("light", work.resume(self.root, claimed["run_id"])["profile"])
        run_path = self.root / ".ai/gp/runs" / claimed["run_id"] / "run.json"
        run = json.loads(run_path.read_text())
        run["owner"], run["stage"] = "session-a", "review"
        run_path.write_text(json.dumps(run))
        lock = self.root / ".ai/gp/claims/TASK-1.json"
        lock_value = json.loads(lock.read_text())
        lock_value["heartbeat"] -= 7200
        lock.write_text(json.dumps(lock_value))
        self.assert_error("profile_mismatch", work.claim, self.root, "TASK-1", "session-b", True, "standard")
        recovered = work.claim(self.root, "TASK-1", "session-b", True, "light")
        self.assertEqual("light", recovered["profile"])
        self.assertEqual({"light": 1}, work.metrics(self.root)["profiles"])

    def test_context_budget_and_explicit_allowlist(self):
        self.card()
        packet = work.context_packet(self.root, self.request())
        self.assertIn("TASK-1", packet["text"])
        self.assertIn("SPECS/backlog/TASK-1.md", packet["hashes"])
        self.assert_error("authoring_context_violation", work.context_packet, self.root, self.request() | {"execution_scope": "evaluated-authoring", "allowlist": []})
        self.put("large.md", "x" * 25000)
        self.assert_error("context_budget_exceeded", work.context_packet, self.root, {"context": ["large.md"]})

    def test_research_cache_invalidates_on_source_change(self):
        self.card()
        work.research_cache(self.root, "rules", self.request() | {"summary": "The contract has one observable acceptance criterion"})
        self.assertEqual("hit", work.research_cache(self.root, "rules")["status"])
        self.card(meta={"acceptance_ids": ["AC1"]})
        self.assertEqual("stale", work.research_cache(self.root, "rules")["status"])

    def test_mapped_repository_hashes_and_write_boundary(self):
        sdk = self.root.parent / ("sdk-" + uuid.uuid4().hex)
        sdk.mkdir()
        (sdk / "contract.md").write_text("# SDK contract\n", encoding="utf-8")
        config = work.project(self.root)
        config["repositories"]["sdk"] = {"path": str(sdk), "writable": False, "version": "v1"}
        self.put("pipeline/project.json", config)
        before = work.json_hash(work.snapshot(self.root))
        packet = work.context_packet(self.root, {"context": [{"repository": "sdk", "path": "contract.md"}]})
        self.assertIn("@sdk/contract.md", packet["hashes"])
        self.assert_error("repository_readonly", work.repository_root, self.root, "sdk", True)
        (sdk / "contract.md").write_text("# SDK v2\n", encoding="utf-8")
        self.assertNotEqual(before, work.json_hash(work.snapshot(self.root)))

    def test_coordinator_usage_is_observed_not_estimated(self):
        work.record_usage(self.root, {"actor": "orchestrator", "model": "unknown", "usage": None})
        metrics = work.metrics(self.root)
        self.assertIsNone(metrics["coordinator_and_tools"][0]["usage"])
        self.assertIsNone(metrics["api_cost"])

    def test_assign_dispatch_ownership_and_observed_model(self):
        run_id = self.run_start()
        a = work.assign(self.root, run_id, self.request())
        self.assertEqual("gpt-5.6-luna", a["dispatch"]["model"])
        self.assertFalse(a["dispatch"]["fork_history"])
        self.assert_error("write_conflict", work.assign, self.root, run_id, self.request())
        self.put("domain/rule.py", "VALUE = 2\n")
        result = {"status": "DONE", "summary": "Changed", "changed_files": ["domain/rule.py"], "findings": [], "checks": [], "blockers": [], "actual_model": "gpt-6-astra"}
        self.assert_error("model_mismatch", work.finish_assignment, self.root, a["assignment_id"], result)
        result["actual_model"] = "gpt-5.6-luna"
        work.finish_assignment(self.root, a["assignment_id"], result)
        self.assertEqual(1, work.metrics(self.root)["models"]["gpt-5.6-luna"]["done"])

    def test_readonly_and_attempt_budget(self):
        run_id = self.run_start()
        self.assert_error("readonly_role", work.assign, self.root, run_id, self.request("reviewer"))
        for _ in range(3):
            a = work.assign(self.root, run_id, self.request("reviewer", []))
            self.finish(a["assignment_id"])
        self.assert_error("attempt_budget_exhausted", work.assign, self.root, run_id, self.request("reviewer", []))

    def configure_gate(self, code="print('{\"pass\":true}')", adapter="json-line"):
        config = work.project(self.root)
        config["gates"] = [{"id": "behavior", "command": [sys.executable, "-c", code], "always": True, "result": adapter}]
        self.put("pipeline/project.json", config)

    def test_real_process_gate_retains_and_invalidates_evidence(self):
        self.configure_gate()
        run_id = self.run_start()
        result = work.run_gate(self.root, run_id, "behavior")
        self.assertTrue(result["pass"])
        self.assertEqual([], work.resume(self.root, run_id)["stale_gates"])
        self.put("domain/rule.py", "VALUE = 3\n")
        self.assertEqual(["behavior"], work.resume(self.root, run_id)["stale_gates"])

    def test_gate_error_cannot_pass(self):
        self.configure_gate("print('{\"pass\":true,\"error_kind\":\"missing_device\"}')")
        run_id = self.run_start()
        self.assertFalse(work.run_gate(self.root, run_id, "behavior")["pass"])

    def test_complete_end_to_end_and_idempotency(self):
        self.configure_gate()
        run_id = self.run_start()
        gate = work.run_gate(self.root, run_id, "behavior")
        for role in ("reviewer", "verifier"):
            assignment = work.assign(self.root, run_id, self.request(role, []))
            self.finish(assignment["assignment_id"])
        path = self.root / gate["evidence"]
        evidence = {"run_id": run_id, "source_sha256": work.json_hash(work.snapshot(self.root)),
                    "acceptance": [{"id": "AC1", "status": "pass", "evidence": gate["evidence"], "sha256": work.digest(path)}]}
        work.close(self.root, run_id, "DONE", evidence)
        self.assertTrue((self.root / "SPECS/done/TASK-1.md").exists())
        self.assertFalse((self.root / ".ai/gp/claims/TASK-1.json").exists())
        self.assertTrue(work.close(self.root, run_id, "DONE", evidence)["already_closed"])
        self.assertTrue(work.completion_exists(self.root, work.board(self.root)[0]))
        self.assertTrue(work.consistency(self.root)["pass"])

    def test_missing_acceptance_evidence_cannot_close(self):
        run_id = self.run_start()
        self.assert_error("evidence_missing", work.close, self.root, run_id, "DONE")
        self.assertEqual("ACTIVE", work.board(self.root)[0]["status"])

    def test_consistency_missing_index_and_stale_next(self):
        self.card()
        self.put("SPECS/INDEX.md", "# Empty index\n")
        self.assertIn("index_card_missing", [f["kind"] for f in work.consistency(self.root)["findings"]])
        work.sync_index(self.root)
        self.assertNotIn("index_card_missing", [f["kind"] for f in work.consistency(self.root)["findings"]])

    def test_cli_bad_argument_one_json_line(self):
        proc = subprocess.run([sys.executable, str(SOURCE), "--root", str(self.root), "nonsense"], capture_output=True, text=True)
        self.assertNotEqual(0, proc.returncode)
        self.assertEqual("bad_usage", json.loads(proc.stdout)["error_kind"])
        self.assertEqual("", proc.stderr)

    def test_adopt_preserves_custom_config(self):
        config = work.project(self.root)
        config["architecture"]["profile"] = "custom"
        self.put("pipeline/project.json", config)
        work.adopt(self.root, True)
        self.assertEqual("custom", work.project(self.root)["architecture"]["profile"])

    def test_upgrade_preview_shows_diff_and_preserves_user_config(self):
        self.put(".codex/commands/gp.md", "old instruction\n")
        self.put("archive/render/.codex/commands/gp.md", "new instruction\n")
        self.put("archive/render/pipeline/model-policy.json", {"custom": False})
        before = (self.root / "pipeline/model-policy.json").read_bytes()
        plan = work.upgrade_preview(self.root, "archive/render")
        self.assertFalse(plan["applied"])
        self.assertIn("-old instruction", next(x for x in plan["changes"] if x["action"] == "update")["diff"])
        self.assertEqual(before, (self.root / "pipeline/model-policy.json").read_bytes())


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "out/workflow-migration" / uuid.uuid4().hex
        self.root.mkdir(parents=True)

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_absence_and_empty_board(self):
        self.assertEqual("gpt-5.6-luna", work.discover(self.root)["dispatch"]["model"])
        claude = work.discover(self.root, "claude")["dispatch"]
        self.assertEqual(("claude-sonnet-5", "medium", "medium"), (claude["model"], claude["reasoning"], claude["tier_reasoning"]))
        result = work.migrate(self.root, {"version": 1, "moves": []}, True)
        self.assertEqual("backlog_empty", result["status"])
        self.assertEqual([], work.board(self.root))

    def test_migrate_preserves_active_status_and_repairs_links(self):
        src = self.put(".claude/specs/active/TASK-1.md", "# TASK-1 — Feature\n[Guide](../../../docs/guide.md)\n\n## Acceptance criteria\n1. It works.\n")
        self.put("docs/guide.md", "# Guide\n[Task](../.claude/specs/active/TASK-1.md)\n")
        plan = {"version": 1, "moves": [{"source": ".claude/specs/active/TASK-1.md", "target": "SPECS/backlog/TASK-1.md", "sha256": work.digest(src)}]}
        work.migrate(self.root, plan, True)
        self.assertEqual("ACTIVE", work.board(self.root)[0]["status"])
        self.assertIn("../../docs/guide.md", work.read(self.root / "SPECS/backlog/TASK-1.md"))
        self.assertIn("../SPECS/backlog/TASK-1.md", work.read(self.root / "docs/guide.md"))
        self.assertTrue(list((self.root / "archive/gp-work").glob("**/TASK-1.md")))

    def test_reject_hidden_card_destination(self):
        src = self.put("backlog/TASK-1.md", "# TASK-1 — Feature\n")
        plan = {"version": 1, "moves": [{"source": "backlog/TASK-1.md", "target": "SPECS/INDEX.md", "sha256": work.digest(src)}]}
        with self.assertRaises(work.WorkError):
            work.migrate(self.root, plan, True)
        self.assertTrue(src.exists())
        self.assertFalse((self.root / "SPECS").exists())

    def test_bad_encoding_fails_before_any_move(self):
        src = self.put("backlog/TASK-1.md", "# TASK-1 — Feature\n")
        (self.root / "bad.md").write_bytes(b"\xff\xff")
        plan = {"version": 1, "moves": [{"source": "backlog/TASK-1.md", "target": "SPECS/backlog/TASK-1.md", "sha256": work.digest(src)}]}
        with self.assertRaises(UnicodeDecodeError):
            work.migrate(self.root, plan, True)
        self.assertTrue(src.exists())


class SharedArchiveTests(unittest.TestCase):
    """PET_ARCHIVE_ROOT routes every superseded file out of the project."""

    def setUp(self):
        self.shared = ROOT / "out/shared-archive" / uuid.uuid4().hex
        os.environ["PET_ARCHIVE_ROOT"] = str(self.shared)
        self.addCleanup(os.environ.pop, "PET_ARCHIVE_ROOT", None)
        self.root = ROOT / "out/workflow-tests" / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        work.adopt(self.root, True)
        (self.root / "SPECS/backlog").mkdir(parents=True)
        self.day_dir = self.shared / self.root.name / time.strftime("%Y-%m-%d")

    def test_mutations_archive_outside_project_and_log_each_folder_once(self):
        card = self.root / "SPECS/backlog/TASK-1.md"
        card.write_text("# TASK-1 — Feature\n\nStatus: **BACKLOG**\n\n## Acceptance criteria\n1. It works.\n", encoding="utf-8")
        work.claim(self.root, "TASK-1", "test-session")
        work.adopt(self.root, True)
        self.assertFalse((self.root / "archive").exists())
        self.assertTrue(list((self.day_dir / "gp-work/locks").glob("*.json")))
        lines = (self.shared / "INDEX.md").read_text(encoding="utf-8").splitlines()
        folders = [line.split(" | ")[2] for line in lines]
        self.assertIn((self.day_dir / "gp-work/locks").as_posix(), folders)
        self.assertEqual(len(folders), len(set(folders)))

    def test_upgrade_preview_accepts_stage_in_shared_archive(self):
        stage = self.day_dir / "gp-bootstrap/run.test/generated"
        (stage / ".codex/commands").mkdir(parents=True)
        (stage / ".codex/commands/gp.md").write_text("new instruction\n", encoding="utf-8")
        (self.root / ".codex/commands").mkdir(parents=True)
        (self.root / ".codex/commands/gp.md").write_text("old instruction\n", encoding="utf-8")
        plan = work.upgrade_preview(self.root, str(stage))
        self.assertIn("-old instruction", next(x for x in plan["changes"] if x["action"] == "update")["diff"])

    def test_upgrade_preview_still_rejects_unrelated_directories(self):
        elsewhere = ROOT / "out/workflow-tests" / uuid.uuid4().hex
        elsewhere.mkdir(parents=True)
        with self.assertRaises(work.WorkError) as exc:
            work.upgrade_preview(self.root, str(elsewhere))
        self.assertEqual("path_outside_project", exc.exception.kind)


if __name__ == "__main__":
    unittest.main(verbosity=2)
