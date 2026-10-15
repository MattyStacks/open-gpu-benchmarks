"""
issue_to_result.py - a "Benchmark result" GitHub issue -> community result YAML

The issue form (.github/ISSUE_TEMPLATE/benchmark.yml) asks for the same fields
as templates/community_submission.yaml. This script reads the issue body,
writes data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml, and runs the
normal checks on it. .github/workflows/benchmark-issue.yml then pushes the file
to a benchmark/issue-<N> branch and opens a pull request for a maintainer.

    python scripts/issue_to_result.py --body-file body.md --issue 42 --author octocat --out-dir out

It writes these into --out-dir:
    comment.md   the reply for the issue (what was created, or what to fix)
    pr_body.md   the pull request description (only on success)
    title.txt    the pull request title (only on success)
    path.txt     the new file's path relative to the repo (only on success)

Exit codes: 0 the file was written and passes the checks, 1 the issue needs a
fix (comment.md says what), 2 a usage error.

Everything in the issue is untrusted text. It reaches the YAML file only
through yaml.dump, and the markdown output escapes it.

Keep FIELDS, CAPTURE_TOOLS, WHO_RAN_IT, OSES, and GRAPHICS_APIS in step with
the issue form; scripts/test_build.py checks that they match.
"""
import argparse
import difflib
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install -r requirements.txt"); sys.exit(2)

import checks
from import_cyberpunk import RESOLUTIONS, IndentedDumper

# Issue-form heading -> key. The headings are the form's field labels.
FIELDS = {
    "GPU": "gpu",
    "Game": "game",
    "Game version": "version",
    "Date": "date",
    "Who ran it?": "who",
    "Source link": "source_url",
    "Creator name": "creator",
    "Results": "results",
    "Upscaler the preset turned on": "upscaling",
    "Operating system": "os",
    "Capture tool": "method",
    "Proof link": "proof_url",
    "CPU": "cpu",
    "Memory": "memory",
    "GPU driver": "driver",
    "OS version": "os_detail",
    "Graphics API": "graphics_api",
    "Credit": "credit",
    "Confirmations": "confirmations",
}
# Dropdown option -> proof.method. One option per checks.PROOF_METHODS value.
CAPTURE_TOOLS = {
    "PresentMon (recommended)": "presentmon",
    "CapFrameX": "capframex",
    "NVIDIA FrameView": "frameview",
    "MSI Afterburner / RivaTuner (RTSS)": "msi_afterburner",
    "MangoHud (Linux)": "mangohud",
    "OCAT": "ocat",
    "AMD Software: Adrenalin Edition": "amd_adrenalin",
    "The game's built-in benchmark": "in_game_benchmark",
    "3DMark or another synthetic benchmark": "synthetic_benchmark",
    "Something else, or the source doesn't say": "other",
}
SELF = "I ran it myself"
FOUND = "Someone else: I found it in a video, review, or post"
WHO_RAN_IT = (SELF, FOUND)
OSES = {"Windows": "windows", "Linux": "linux"}
GRAPHICS_APIS = ("DX12", "DX11", "Vulkan")
CREDIT_ME = "Credit me as my GitHub username"
FRAME_GENERATION_OFF = "Frame generation was off"
CC0_AGREEMENT = "I release these results under CC0"
NO_RESPONSE = ("", "_no response_", "none")
MAX_BODY = 20_000
MAX_TEXT = 200
MAX_RUNS = 20
CHECKBOX = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s*(.+?)\s*$")
RESOLUTION_SIZE = re.compile(r"^(\d{3,5})\s*[x×]\s*(\d{3,5})$", re.IGNORECASE)
MARKER = "<!-- benchmark-bot -->"


class SubmissionError(Exception):
    """A problem the submitter can fix by editing the issue."""


def code(text):
    """Untrusted text as an inline code span it can't break out of (mentions don't fire inside one)."""
    return "`" + " ".join(str(text).split()).replace("`", "'")[:80] + "`"


# --- Reading the issue ---------------------------------------------------------


def parse_issue_body(body):
    """Return {key: text} for every form heading in the issue body."""
    sections, key, lines = {}, None, []
    for line in body.splitlines():
        if line.startswith("### "):
            if key:
                sections[key] = "\n".join(lines).strip()
            key, lines = FIELDS.get(line[4:].strip()), []
        elif key:
            lines.append(line)
    if key:
        sections[key] = "\n".join(lines).strip()
    return {key: ("" if value.lower() in NO_RESPONSE else value) for key, value in sections.items()}


def checked(text):
    """The labels of the ticked boxes in a checkboxes section."""
    boxes = (CHECKBOX.match(line) for line in text.splitlines())
    return {match.group(2) for match in boxes if match and match.group(1).lower() == "x"}


def text_field(fields, key, label, required=False):
    value = " ".join(fields.get(key, "").split())
    if required and not value:
        raise SubmissionError(f"**{label}** is required.")
    if len(value) > MAX_TEXT:
        raise SubmissionError(f"**{label}** is longer than {MAX_TEXT} characters.")
    return value


def choice(fields, key, label, options):
    value = text_field(fields, key, label, required=True)
    if value not in options:
        raise SubmissionError(f"**{label}** must be one of the form's options, not {code(value)}.")
    return options[value] if isinstance(options, dict) else value


# --- Matching what's already in data/ --------------------------------------------


def find_gpu(catalog, text):
    """A catalog entry by ID, or by its exact product name (any case)."""
    lowered = text.strip().lower()
    for entry in catalog:
        if lowered in (entry["id"], str(checks.spec(entry, "identity", "name", default="")).lower()):
            return entry
    names = {entry["id"]: entry["id"] for entry in catalog}
    names.update({str(checks.spec(entry, "identity", "name", default="")).lower(): entry["id"] for entry in catalog})
    close = difflib.get_close_matches(lowered, list(names), n=3, cutoff=0.5)
    hint = f" Did you mean {', '.join(f'`{names[name]}`' for name in close)}?" if close else ""
    raise SubmissionError(
        f"**GPU** {code(text)} is not in the catalog. Use the exact catalog ID or product name.{hint} "
        "If the GPU is missing from the catalog, say so in a comment and a maintainer will add it."
    )


def known_runs(data_dir):
    for source in checks.RESULT_SOURCES:
        for path in checks.result_paths(data_dir, source):
            try:
                run = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if isinstance(run, dict):
                yield run


def canonical(value, known):
    """Reuse an existing spelling that differs only in case, so dashboard groups don't split."""
    return next((name for name in sorted(known) if name.lower() == value.lower()), value)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "game"


# --- Building the run ---------------------------------------------------------------


def parse_number(text, label, line_number):
    cleaned = re.sub(r"\s*fps$", "", text.strip(), flags=re.IGNORECASE)
    try:
        value = float(cleaned)
    except ValueError:
        raise SubmissionError(f"**Results** line {line_number}: {label} {code(text)} is not a number.") from None
    if not 0 < value < 10_000:
        raise SubmissionError(f"**Results** line {line_number}: {label} {code(text)} is out of range.")
    return int(value) if value.is_integer() else value


def parse_resolution(text):
    size = RESOLUTION_SIZE.match(text.strip())
    if size:
        return RESOLUTIONS.get((int(size.group(1)), int(size.group(2))), f"{size.group(1)}x{size.group(2)}")
    return "4K" if text.strip().lower() in ("4k", "2160p") else text.strip()


def parse_results(text, known_presets):
    """One run per line: resolution, preset, avg_fps, optional 1% low."""
    entries = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line).strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        parts = [part.strip() for part in re.split(r"[,|\t]", line)]
        if len(parts) not in (3, 4) or not all(parts[:3]):
            raise SubmissionError(
                f"**Results** line {line_number} {code(line)} needs 3 or 4 comma-separated values: "
                "resolution, preset, average FPS, and optionally the 1% low, such as `1440p, Ultra, 79.1, 65.0`."
            )
        entry = {
            "resolution": parse_resolution(parts[0]),
            "graphics_preset": canonical(parts[1], known_presets),
            "avg_fps": parse_number(parts[2], "average FPS", line_number),
        }
        if len(parts) == 4 and parts[3]:
            entry["p1_low"] = parse_number(parts[3], "1% low", line_number)
        if len(entry["resolution"]) > MAX_TEXT or len(entry["graphics_preset"]) > MAX_TEXT:
            raise SubmissionError(f"**Results** line {line_number} is too long.")
        entries.append(entry)
    if not entries:
        raise SubmissionError("**Results** has no runs. Add one line per run, such as `1440p, Ultra, 79.1, 65.0`.")
    if len(entries) > MAX_RUNS:
        raise SubmissionError(f"**Results** has more than {MAX_RUNS} runs. Open a pull request for bulk uploads.")
    return entries


def build_run(fields, author, catalog, data_dir):
    """The result file's contents from the parsed issue form. Raises SubmissionError."""
    confirmations = checked(fields.get("confirmations", ""))
    if not any(label.startswith(CC0_AGREEMENT) for label in confirmations):
        raise SubmissionError("Tick the **CC0** box: results are only accepted as public data.")
    if not any(label.startswith(FRAME_GENERATION_OFF) for label in confirmations):
        raise SubmissionError("Tick the **frame generation** box. Runs with frame generation on aren't accepted.")

    gpu = find_gpu(catalog, text_field(fields, "gpu", "GPU", required=True))
    runs = list(known_runs(data_dir))
    game = canonical(text_field(fields, "game", "Game", required=True), {str(run.get("game")) for run in runs if run.get("game")})
    day = text_field(fields, "date", "Date", required=True)
    if not checks.FULL_DATE.match(day):
        raise SubmissionError(f"**Date** {code(day)} must be written YYYY-MM-DD, such as 2026-10-03.")
    try:
        date.fromisoformat(day)
    except ValueError:
        raise SubmissionError(f"**Date** {code(day)} is not a real calendar day.") from None

    presets = {
        str(entry.get("graphics_preset"))
        for run in runs if run.get("game") == game and isinstance(run.get("result"), list)
        for entry in run["result"] if isinstance(entry, dict) and entry.get("graphics_preset")
    }
    entries = parse_results(fields.get("results", ""), presets)
    upscaler = text_field(fields, "upscaling", "Upscaler the preset turned on")
    if upscaler.lower() in checks.UPSCALING_OFF:
        upscaler = ""
    for entry in entries:
        if upscaler:
            entry["upscaling"] = upscaler
            entry["preset_upscaling"] = True

    run = {"gpu_id": gpu["id"], "game": game, "date": day}
    version = text_field(fields, "version", "Game version")
    if version:
        run["version"] = version
    if CREDIT_ME in checked(fields.get("credit", "")):
        run["submitted_by"] = author
    if choice(fields, "who", "Who ran it?", WHO_RAN_IT) == FOUND:
        credit = {"source_url": text_field(fields, "source_url", "Source link")}
        if not credit["source_url"]:
            raise SubmissionError("**Source link** is required for a result you found: the video, review, or post with the numbers.")
        creator = text_field(fields, "creator", "Creator name")
        if creator:
            credit["name"] = creator
        run["credit"] = credit
    run["result"] = entries

    system = {"os": choice(fields, "os", "Operating system", OSES)}
    for key, label in (("os_detail", "OS version"), ("cpu", "CPU"), ("memory", "Memory"), ("driver", "GPU driver")):
        value = text_field(fields, key, label)
        if value:
            system[key] = value
    api = text_field(fields, "graphics_api", "Graphics API")
    if api:
        system["graphics_api"] = choice(fields, "graphics_api", "Graphics API", GRAPHICS_APIS)
    run["system"] = system

    proof = {"method": choice(fields, "method", "Capture tool", CAPTURE_TOOLS)}
    proof_url = text_field(fields, "proof_url", "Proof link")
    if proof_url:
        if not checks.is_https(proof_url):
            raise SubmissionError("**Proof link** must be an https:// link.")
        proof["summary_source"] = proof_url
    run["proof"] = proof
    return run


def target_path(data_dir, run):
    """The next free result_YYYYMMDD_<game>[_N].yaml in the GPU's community folder."""
    folder = data_dir / "community" / run["gpu_id"]
    stem = f"result_{run['date'].replace('-', '')}_{slug(run['game'])}"
    repeat = 1
    while True:
        path = folder / f"{stem}{'' if repeat == 1 else f'_{repeat}'}.yaml"
        if not path.exists():
            break
        repeat += 1
    community = (data_dir / "community").resolve()
    if community not in path.resolve().parents:
        raise SubmissionError("The result file would land outside data/community.")
    return path


def file_text(run, issue):
    header = (
        f"# Submitted through issue #{issue} and written by scripts/issue_to_result.py.\n"
        "# Released under CC0 (see data/LICENSE).\n"
    )
    return header + yaml.dump(run, Dumper=IndentedDumper, sort_keys=False, default_flow_style=False, allow_unicode=True)


def check_file(path, data_dir):
    """The checks' issues for just this file."""
    catalog, _ = checks.load_catalog(data_dir)
    _, issues = checks.load_results(catalog, data_dir)
    mine = checks.relative_path(path)
    return checks.Issues(issue for issue in issues if issue.path == mine)


# --- Markdown output ----------------------------------------------------------------


def fence(text, language=""):
    """A code fence longer than any backtick run inside the text."""
    ticks = "`" * max(3, max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    return f"{ticks}{language}\n{text.rstrip()}\n{ticks}"


def inline(text):
    """Untrusted text, safe to show in a markdown sentence."""
    return re.sub(r"[\\`*_<>\[\]|@#]", lambda match: "\\" + match.group(0), " ".join(str(text).split()))


def issue_lines(issues):
    return "\n".join(f"{issue.level}: [{issue.rule}] {issue.message}" for issue in issues)


def docs_link(anchor=""):
    return f"{checks.REPO_URL}/{checks.RESULTS_DOC}{anchor}"


def failure_comment(problem):
    return (
        f"{MARKER}\n**This result can't be added yet.**\n\n{problem}\n\n"
        "Edit this issue to fix it and the check runs again by itself. "
        f"The rules are in [COMMUNITY_SUBMISSIONS.md]({docs_link('#submit-through-an-issue')})."
    )


def pr_body(run, gpu, text, relative, issue, author, issues):
    notes = f"\n### Notes from the checks\n\n{fence(issue_lines(issues))}\n" if issues else ""
    return (
        f"Adds a community result submitted by @{author} in #{issue}.\n\n"
        f"- **GPU:** `{run['gpu_id']}` ({inline(checks.spec(gpu, 'identity', 'name', default=''))})\n"
        f"- **Game:** {inline(run['game'])}\n"
        f"- **Runs:** {len(run['result'])}\n"
        f"- **File:** `{relative}`\n\n"
        f"{fence(text, 'yaml')}\n{notes}\n"
        "The submitter ticked the box releasing these results under "
        f"[CC0]({checks.REPO_URL}/data/LICENSE).\n\n"
        "### Reviewer checklist\n\n"
        "- [ ] The numbers look plausible for this GPU, game, and preset.\n"
        "- [ ] The proof or source link, if any, backs them up.\n"
        "- [ ] The preset and resolution names match the existing dashboard groups.\n\n"
        "Fix anything small by pushing to this branch, or ask on the issue. "
        "Editing the issue regenerates this pull request and replaces any commits on the branch.\n\n"
        f"Closes #{issue}\n"
    )


# --- Entry point ----------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--body-file", type=Path, required=True, help="the issue body, as markdown")
    parser.add_argument("--issue", type=int, required=True, help="the issue number")
    parser.add_argument("--author", required=True, help="the issue author's GitHub username")
    parser.add_argument("--out-dir", type=Path, required=True, help="where to write comment.md, pr_body.md, title.txt, path.txt")
    parser.add_argument("--data-dir", type=Path, default=checks.DATA_DIR, help="source tree to write into (default: data)")
    args = parser.parse_args(argv)
    if not checks.GITHUB_USER_PATTERN.match(args.author):
        parser.error(f"--author '{args.author}' is not a GitHub username")
    data_dir = args.data_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    def fail(problem):
        (args.out_dir / "comment.md").write_text(failure_comment(problem), encoding="utf-8")
        print(problem)
        return 1

    body = args.body_file.read_text(encoding="utf-8")
    if len(body) > MAX_BODY:
        return fail(f"The issue is longer than {MAX_BODY:,} characters. Open a pull request for large submissions.")
    catalog, _ = checks.load_catalog(data_dir)
    try:
        run = build_run(parse_issue_body(body), args.author, catalog, data_dir)
        path = target_path(data_dir, run)
    except SubmissionError as error:
        return fail(str(error))

    text = file_text(run, args.issue)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    issues = check_file(path, data_dir)
    if issues.errors:
        path.unlink()
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
        return fail(f"The checks found these problems:\n\n{fence(issue_lines(issues.errors))}")

    try:
        relative = path.relative_to(checks.ROOT).as_posix()
    except ValueError:
        relative = path.as_posix()
    gpu = next(entry for entry in catalog if entry["id"] == run["gpu_id"])
    name = checks.spec(gpu, "identity", "name", default=run["gpu_id"])
    (args.out_dir / "path.txt").write_text(relative, encoding="utf-8")
    (args.out_dir / "title.txt").write_text(f"Benchmark: {name}, {' '.join(run['game'].split())[:80]} (#{args.issue})", encoding="utf-8")
    (args.out_dir / "pr_body.md").write_text(pr_body(run, gpu, text, relative, args.issue, args.author, issues), encoding="utf-8")
    runs = len(run["result"])
    (args.out_dir / "comment.md").write_text(
        f"{MARKER}\n**Thanks!** This issue became `{relative}` with {runs} run{'s' if runs != 1 else ''}. "
        "A maintainer will review the pull request below. "
        "Edit this issue if something is wrong and the pull request updates by itself.",
        encoding="utf-8",
    )
    print(f"Wrote {relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
