"""Run every local check before a commit, push, or pull request, and report every failure at once.

    python scripts/preflight.py           # before a push or PR: fast checks + browser tests (+ the blog when it changed)
    python scripts/preflight.py --fast    # before a commit: Python, JS syntax, data, build, tests, housekeeping (~15 s)
    python scripts/preflight.py --all     # everything, including the blog build
    python scripts/preflight.py --only-housekeeping --base origin/main   # the PR housekeeping check alone (CI)

Claude Code runs it automatically before `git commit` (--fast) and `git push` /
`gh pr create` (full) through .claude/settings.json; people can enable the same
gate with `git config core.hooksPath .githooks`. CI runs the same steps.
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
VENV = ROOT / ".venv"
E2E_DIR = ROOT / "tests" / "e2e"
BLOG_DIR = ROOT / "blog"
# Changes only to these paths are data-only result submissions: no changelog
# line, version bump, or count refresh (a later DATA bump batches them).
DATA_ONLY_PREFIXES = ("data/community/", "data/official/", "data/games.yaml")
# A change under any of these rebuilds the blog in the default (pre-push) tier.
BLOG_INPUTS = ("blog/", "content/", "site/index.html", "scripts/build.py", "data/")
# Docs that quote the release version and the published data counts.
VERSION_DOCS = ("README.md", "docs/COPILOT_HANDOFF.md", "CLAUDE.md")
COUNT_DOCS = ("README.md", "docs/COPILOT_HANDOFF.md")
# How each count is written in prose; "no" counts as 0.
COUNT_PATTERNS = {
    "catalog GPUs": r"(\d+|no) catalog GPUs?\b",
    "reference files": r"(\d+|no) reference (?:GPU specs|files)",
    "official runs": r"(\d+|no) official (?:result )?runs?\b",
    "community runs": r"(\d+|no) community (?:result )?runs?\b",
    "dashboard summaries": r"(\d+|no) (?:combined )?dashboard summar(?:y|ies)\b",
}


# --- Shared helpers (test_build.py imports these too) ---------------------------


def quoted_counts(text):
    """{count name: number} for every count a paragraph states."""
    flat = " ".join(text.split())
    found = {}
    for name, pattern in COUNT_PATTERNS.items():
        match = re.search(pattern, flat)
        if match:
            found[name] = 0 if match.group(1) == "no" else int(match.group(1))
    return found


def api_counts(api_dir, data_dir):
    """The same counts, measured from a built API folder and its source tree."""
    def load(name):
        return json.loads((api_dir / name).read_text(encoding="utf-8"))

    return {
        "catalog GPUs": len(load("gpus.json")["gpus"]),
        "reference files": len(list((data_dir / "gpus" / "reference").rglob("*.yaml"))),
        "official runs": load("official.json")["count"],
        "community runs": load("community.json")["raw_count"],
        "dashboard summaries": len(load("dashboard.json")["records"]),
    }


def doc_paragraph(path, marker):
    """The paragraph of a doc that starts with marker (such as 'Published so far:')."""
    text = (ROOT / path).read_text(encoding="utf-8")
    start = text.find(marker)
    if start < 0:
        return None
    end = text.find("\n\n", start)
    return text[start:end if end >= 0 else None]


# Where each doc states the published counts.
PUBLISHED_MARKERS = {"README.md": "Published so far:", "docs/COPILOT_HANDOFF.md": "**Published data (`data/`).**"}


# --- Steps -----------------------------------------------------------------------


class Step:
    def __init__(self, name):
        self.name = name
        self.ok = True
        self.skipped = ""
        self.warnings = []
        self.output = ""
        self.seconds = 0.0

    def fail(self, message):
        self.ok = False
        self.output += message.rstrip() + "\n"


def run(command, cwd=ROOT, env=None):
    """(exit code, combined output) of a command."""
    completed = subprocess.run(
        command, cwd=cwd, env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    return completed.returncode, completed.stdout


def git(*args):
    status, output = run(["git", *args])
    return output.strip() if status == 0 else None


def changed_files(base):
    """Files changed since the merge base with base, committed or not, plus new untracked files."""
    merge_base = git("merge-base", "HEAD", base)
    if merge_base is None:
        return None, []
    tracked = git("diff", "--name-only", merge_base) or ""
    untracked = git("ls-files", "--others", "--exclude-standard") or ""
    return merge_base, sorted({line for line in (tracked + "\n" + untracked).splitlines() if line})


def step_py_compile(step):
    files = sorted(str(path.relative_to(ROOT)) for path in [*SCRIPTS.glob("*.py"), *(ROOT / ".claude" / "hooks").glob("*.py")])
    status, output = run([sys.executable, "-m", "py_compile", *files])
    if status:
        step.fail(output)


def step_dashboard_js(step):
    node = shutil.which("node")
    if node is None:
        step.fail("node was not found; install Node 22.12+ (the blog and the browser tests need it too)")
        return
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    if not scripts:
        step.fail("site/index.html has no inline <script>")
        return
    with tempfile.TemporaryDirectory() as temp:
        for number, script in enumerate(scripts):
            # Pad with newlines so node's line numbers match index.html.
            line = html[:html.index(script)].count("\n")
            path = Path(temp) / f"index_script_{number}.js"
            path.write_text("\n" * line + script, encoding="utf-8")
            status, output = run([node, "--check", str(path)])
            if status:
                step.fail(output.replace(str(path), "site/index.html"))


def step_command(step, *args):
    status, output = run([sys.executable, *args])
    if status:
        step.fail(output)
    else:
        step.output = output


def step_diff_check(step, base):
    merge_base = git("merge-base", "HEAD", base) if base else None
    status, output = run(["git", "diff", "--check", *([merge_base] if merge_base else [])])
    if status:
        step.fail(output or "git diff --check found whitespace problems")


def release_version(text):
    match = re.search(r'^RELEASE_VERSION = "([^"]+)"', text or "", re.MULTILINE)
    return match.group(1) if match else None


def step_housekeeping(step, base):
    """CHANGELOG line, version bump, TODO touched, and current published counts."""
    merge_base, files = changed_files(base)
    if merge_base is None:
        step.skipped = f"no merge base with {base}; fetch it first (git fetch origin main)"
        return
    if not files:
        step.skipped = f"nothing changed since {base}"
        return
    if all(path.startswith(DATA_ONLY_PREFIXES) for path in files):
        step.skipped = "data-only change: no changelog line or version bump needed"
        return
    diff = git("diff", merge_base, "--", "CHANGELOG.md") or ""
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    if not any(line.lstrip().startswith("- ") for line in added):
        step.fail("CHANGELOG.md has no new entry: add a '- ...' line for this change (see CLAUDE.md, 'Every change')")
    before = release_version(git("show", f"{merge_base}:scripts/build.py"))
    now = release_version((SCRIPTS / "build.py").read_text(encoding="utf-8"))
    if before == now:
        step.fail(
            f"RELEASE_VERSION is still {now}: bump it (MAJOR/MINOR/DATA/POST, see CLAUDE.md), rename "
            "'## Unreleased' in CHANGELOG.md to the new version and date, and update README.md, "
            "docs/COPILOT_HANDOFF.md, and CLAUDE.md"
        )
    if "docs/TODO.md" not in files:
        step.warnings.append("docs/TODO.md is unchanged: remove finished items and add anything deferred")
    # The published counts the docs quote must match data/.
    sys.path.insert(0, str(SCRIPTS))
    import build  # noqa: E402 - needs the scripts folder on the path

    with tempfile.TemporaryDirectory() as temp:
        with contextlib.redirect_stdout(io.StringIO()):
            status = build.main(build.DATA_DIR, Path(temp))
        if status:
            step.warnings.append("published counts not compared: data/ doesn't build (see the build step)")
            return
        actual = api_counts(Path(temp), build.DATA_DIR)
    for path, marker in PUBLISHED_MARKERS.items():
        paragraph = doc_paragraph(path, marker)
        if paragraph is None:
            step.fail(f"{path} lost its '{marker}' paragraph, which states the published counts")
            continue
        quoted = quoted_counts(paragraph)
        for name, value in actual.items():
            if name not in quoted:
                step.fail(f"{path} '{marker}' doesn't state the number of {name} ({value})")
            elif quoted[name] != value:
                step.fail(f"{path} '{marker}' says {quoted[name]} {name}, but data/ has {value}")


def step_blog(step):
    if not (BLOG_DIR / "node_modules").is_dir():
        step.fail("blog dependencies are missing: run `npm --prefix blog ci` once")
        return
    status, output = run(["npm", "--prefix", "blog", "run", "build"])
    if status:
        step.fail(output)


def step_browser(step):
    if not (E2E_DIR / "node_modules").is_dir():
        step.fail("browser test dependencies are missing: run `npm --prefix tests/e2e ci` and "
                  "`npx --prefix tests/e2e playwright install chromium` once")
        return
    status, output = run(["npm", "--prefix", "tests/e2e", "test", "--", "--reporter=line"], env={"PREFLIGHT": "1"})
    if status:
        step.fail(output)


# --- Main --------------------------------------------------------------------------


def use_venv():
    """Re-run under .venv's Python when it exists; refuse the global Python outside CI."""
    if os.environ.get("CI") or Path(sys.prefix).resolve() == VENV.resolve():
        return
    python = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if python.exists():
        sys.exit(subprocess.call([str(python), *sys.argv]))
    print("No .venv: create it once with `python -m venv .venv` and "
          "`.venv/bin/python -m pip install -r requirements.txt` (Windows: .venv\\Scripts\\python.exe).")
    sys.exit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    tier = parser.add_mutually_exclusive_group()
    tier.add_argument("--fast", action="store_true", help="skip the browser tests and the blog build")
    tier.add_argument("--all", action="store_true", help="also build the blog even when nothing in it changed")
    tier.add_argument("--only-housekeeping", action="store_true", help="only the changelog/version/count check")
    parser.add_argument("--no-housekeeping", action="store_true", help="skip the changelog/version/count check")
    parser.add_argument("--base", default="origin/main", help="the branch this change will merge into (default: origin/main)")
    args = parser.parse_args(argv)
    use_venv()

    _, files = changed_files(args.base)
    blog_changed = any(path.startswith(BLOG_INPUTS) for path in files)
    plan = []
    if not args.only_housekeeping:
        plan += [
            ("Python compiles", step_py_compile),
            ("Dashboard JavaScript syntax", step_dashboard_js),
            ("Data checks (validate.py)", lambda step: step_command(step, "scripts/validate.py")),
            ("Build (build.py)", lambda step: step_command(step, "scripts/build.py")),
            ("Regression tests (test_build.py)", lambda step: step_command(step, "scripts/test_build.py")),
            ("Whitespace (git diff --check)", lambda step: step_diff_check(step, args.base)),
        ]
    if not args.no_housekeeping:
        plan.append(("Housekeeping (changelog, version, counts)", lambda step: step_housekeeping(step, args.base)))
    if not (args.fast or args.only_housekeeping):
        if args.all or blog_changed:
            plan.append(("Blog build (Astro)", step_blog))
        plan.append(("Browser tests (Playwright)", step_browser))

    steps = []
    for name, action in plan:
        step = Step(name)
        started = time.monotonic()
        print(f"... {name}", flush=True)
        try:
            action(step)
        except Exception as error:  # noqa: BLE001 - a broken step is a failed step
            step.fail(f"{type(error).__name__}: {error}")
        step.seconds = time.monotonic() - started
        steps.append(step)

    print()
    for step in steps:
        mark = "SKIP" if step.skipped else ("ok  " if step.ok else "FAIL")
        note = f" ({step.skipped})" if step.skipped else ""
        print(f"{mark} {step.name} [{step.seconds:.1f}s]{note}")
        for warning in step.warnings:
            print(f"     warning: {warning}")
    failed = [step for step in steps if not step.ok]
    for step in failed:
        lines = step.output.rstrip().splitlines()
        shown = lines if len(lines) <= 60 else ["...", *lines[-60:]]
        print(f"\n=== {step.name} failed ===")
        print("\n".join(shown))
    if failed:
        print(f"\npreflight: {len(failed)} of {len(steps)} steps failed")
        return 1
    print("\npreflight: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
