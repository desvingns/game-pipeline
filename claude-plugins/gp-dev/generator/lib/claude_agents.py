"""Pin Claude Code model/effort in rendered role frontmatter from the effective model policy.

Usage: claude_agents.py AGENTS_DIR PREFIX ENGINE GP_WORK_PY POLICY_ROOT

Claude Code accepts a per-spawn model but reads effort only from agent frontmatter,
so each role carries its default tier. Policy semantics are imported from the staged
gp_work.py, keeping one implementation for bootstrap and runtime routing.
"""
import importlib.util
from pathlib import Path
import sys


def load_work(path):
    # The staged scripts directory is deployed verbatim; never leave __pycache__ in it.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("gp_work", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pin(path, setting, max_turns):
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: missing frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError(f"{path.name}: unterminated frontmatter")
    front = [line for line in lines[1:end] if not line.startswith(("model:", "effort:", "maxTurns:"))]
    if setting:
        front += ["model: " + setting["model"], "effort: " + setting["reasoning"]]
    if max_turns:
        front.append(f"maxTurns: {max_turns}")
    path.write_text("\n".join([lines[0], *front, *lines[end:]]), encoding="utf-8", newline="\n")


def main(agents_dir, prefix, engine, work_script, policy_root):
    work = load_work(work_script)
    try:
        policy = work.policy(Path(policy_root))
    except work.WorkError as exc:
        raise ValueError(f"{exc.kind}: {exc.detail}") from exc
    for path in sorted(Path(agents_dir).glob("*.md")):
        role = path.stem.removeprefix(prefix + "-").removesuffix("-" + engine)
        pin(path, work.claude_role_setting(policy, role), work.claude_role_max_turns(policy, role))


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    try:
        main(*sys.argv[1:])
    except (OSError, ValueError) as exc:
        sys.exit("claude agents: " + str(exc))
