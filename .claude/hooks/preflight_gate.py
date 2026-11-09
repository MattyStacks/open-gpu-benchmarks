"""Claude Code PreToolUse gate: run scripts/preflight.py before a commit, push, or PR.

.claude/settings.json runs this before every Bash call. It reads the hook JSON
on stdin and does nothing (exit 0, instantly) unless the command runs
`git commit` (-> preflight.py --fast) or `git push` / `gh pr create`
(-> the full preflight.py). When a check fails it exits 2 and prints the
failures on stderr, which blocks the command and shows Claude what to fix.

Escape hatch for emergencies only: run the command with SKIP_PREFLIGHT=1 set
in the environment of the Claude Code session (or `SKIP_PREFLIGHT=1 git ...`
inside the command itself). Say why in the commit or PR when you use it.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
MAX_LINES = 150
HEADER = ("preflight failed — fix these before committing/pushing "
          "(each message says why the rule exists and how to fix it):")
# A command word: start of the string or after a shell separator, ignoring env assignments.
PREFIX = r"(?:^|[;&|(]\s*|\n\s*)(?:\w+=\S*\s+)*"
COMMIT = re.compile(PREFIX + r"git\s+(?:-C\s+\S+\s+)?commit\b")
PUSH = re.compile(PREFIX + r"(?:git\s+(?:-C\s+\S+\s+)?push\b|gh\s+pr\s+create\b)")


def python():
    for candidate in (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def failure_part(output):
    """The part of preflight's output after the step summary: the failure details."""
    lines = output.rstrip().splitlines()
    start = next((index for index, line in enumerate(lines) if line.startswith("=== ")), None)
    if start is None:
        # No detail block: fall back to the summary lines (FAIL/SKIP/warning).
        start = next((index for index, line in enumerate(lines) if line == ""), 0)
    shown = lines[start:]
    if len(shown) > MAX_LINES:
        shown = shown[:MAX_LINES] + [f"... ({len(lines) - start - MAX_LINES} more lines; run the command yourself to see them)"]
    return "\n".join(shown)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if PUSH.search(command):
        args = []
    elif COMMIT.search(command):
        args = ["--fast"]
    else:
        return 0
    if os.environ.get("SKIP_PREFLIGHT") == "1" or re.search(r"\bSKIP_PREFLIGHT=1\b", command):
        return 0
    result = subprocess.run(
        [python(), str(ROOT / "scripts" / "preflight.py"), *args],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode == 0:
        return 0
    print(HEADER, file=sys.stderr)
    print(failure_part(result.stdout), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
