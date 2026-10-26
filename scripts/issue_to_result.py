"""
issue_to_result.py - a "Benchmark result" GitHub issue -> community result YAML

It reads three kinds of issue:
- the "Benchmark result" form (.github/ISSUE_TEMPLATE/benchmark.yml), which
  asks for the same fields as templates/community_submission.yaml;
- the "Benchmark result (file)" form (benchmark_file.yml), with a result file
  attached or pasted;
- any other issue with the benchmark label and one attached
  (github.com/user-attachments/files/...) or pasted (```yaml / ```json)
  result file, such as an Open GPU Benchmarker export.
Submitting the issue releases the results under CC BY 4.0; there is no box to
tick. The script writes data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
and runs the normal checks on it. .github/workflows/benchmark-issue.yml then
pushes the file to a benchmark/issue-<N> branch and opens a pull request for a
maintainer.

    python scripts/issue_to_result.py --body-file body.md --issue 42 --author octocat --out-dir out

It writes these into --out-dir:
    comment.md   the reply for the issue (what was created, or what to fix)
    pr_body.md   the pull request description (only on success)
    title.txt    the pull request title (only on success)
    path.txt     the new file's path relative to the repo (only on success)

Exit codes: 0 the file was written and passes the checks, 1 the issue needs a
fix (comment.md says what), 2 a usage error, 3 the issue has attachments the
bot can't convert (raw captures, screenshots), so a maintainer takes it over
(docs/PROCESSING_ISSUES.md).

Everything in the issue is untrusted text. It reaches the YAML file only
through yaml.dump, and the markdown output escapes it. Attachments are fetched
only from github.com/user-attachments/files/, through redirects to
*.githubusercontent.com, with a size and time cap, and saved under --out-dir.

Keep FIELDS, FILE_FIELDS, CAPTURE_TOOLS, WHO_RAN_IT, OSES, and GRAPHICS_APIS in
step with the issue forms; scripts/test_build.py checks that they match.
"""
import argparse
import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
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
    "Memory (GB)": "memory_gb",
    "Memory type": "memory_type",
    "Memory channels": "memory_channels",
    "GPU driver": "driver",
    "OS version": "os_detail",
    "Graphics API": "graphics_api",
    "Credit": "credit",
}
# The file form's headings.
FILE_FIELDS = {
    "Result file": "file",
    "Credit": "credit",
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
NO_RESPONSE = ("", "_no response_", "none")
MAX_BODY = 20_000
MAX_TEXT = 200
MAX_RUNS = 20
CHECKBOX = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s*(.+?)\s*$")
RESOLUTION_SIZE = re.compile(r"^(\d{3,5})\s*[x×]\s*(\d{3,5})$", re.IGNORECASE)
MARKER = "<!-- benchmark-bot -->"
ISSUES_URL = "https://github.com/MattyStacks/open-gpu-benchmarks/issues/new"
LICENSE_URL = f"{checks.REPO_URL}/data/LICENSE"

# Attached or pasted result files.
ATTACHMENT = re.compile(r"https://github\.com/user-attachments/files/(\d+)/([\w.-]+)")
ANY_ATTACHMENT = re.compile(r"https://github\.com/user-attachments/(?:files|assets)/[\w./-]+")
FENCED = re.compile(r"^(`{3,}|~{3,})[ \t]*(yaml|yml|json)[ \t]*\n(.*?)^\1[ \t]*$", re.MULTILINE | re.DOTALL | re.IGNORECASE)
RESULT_SUFFIXES = (".yaml", ".yml", ".json")
DOWNLOAD_HOSTS = (".githubusercontent.com",)
MAX_FILE_BYTES = 1_000_000
DOWNLOAD_SECONDS = 20
# Never taken from a submitted file: the bot sets submitted_by from the Credit
# box, and the others belong to official or test data only.
DROPPED_KEYS = ("submitted_by", "testbench_id", "source", "synthetic")


class SubmissionError(Exception):
    """A problem the submitter can fix by editing the issue."""


class NeedsMaintainer(Exception):
    """Attachments the bot can't convert; a maintainer takes the issue over."""


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
            heading = line[4:].strip()
            key, lines = FIELDS.get(heading) or FILE_FIELDS.get(heading), []
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
    hint = f" Did you mean {', '.join(f'`{match}`' for match in dict.fromkeys(names[name] for name in close))}?" if close else ""
    raise SubmissionError(
        f"**GPU** {code(text)} is not in the catalog. Use the exact catalog ID or product name.{hint} "
        "If the GPU is missing from the catalog, say so in a comment and a maintainer will add it."
    )


def find_game(games, text):
    """A data/games.yaml entry by ID, or by its exact name (any case). The form never adds a game."""
    lowered = text.strip().lower()
    for game in games:
        if lowered in (game["id"], game["name"].lower()):
            return game
    names = {game["id"]: game["id"] for game in games}
    names.update({game["name"].lower(): game["id"] for game in games})
    close = difflib.get_close_matches(lowered, list(names), n=3, cutoff=0.5)
    hint = f" Did you mean {', '.join(f'`{match}`' for match in dict.fromkeys(names[name] for name in close))}?" if close else ""
    raise SubmissionError(
        f"**Game** {code(text)} is not in data/games.yaml. Use the game's exact ID or name from "
        f"[data/games.yaml]({checks.REPO_URL}/data/games.yaml).{hint} "
        "If the game isn't listed, it has to be added first by its own pull request to data/games.yaml "
        f"(see [Adding a game or benchmark]({docs_link('#adding-a-game-or-benchmark')})); "
        "once that's merged, edit this issue and it's checked again."
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


def check_day(day):
    if not checks.FULL_DATE.match(day):
        raise SubmissionError(f"**Date** {code(day)} must be written YYYY-MM-DD, such as 2026-10-03.")
    try:
        date.fromisoformat(day)
    except ValueError:
        raise SubmissionError(f"**Date** {code(day)} is not a real calendar day.") from None
    return day


def build_run(fields, author, catalog, games, data_dir):
    """The result file's contents from the parsed issue form. Raises SubmissionError."""
    gpu = find_gpu(catalog, text_field(fields, "gpu", "GPU", required=True))
    runs = list(known_runs(data_dir))
    game_id = find_game(games, text_field(fields, "game", "Game", required=True))["id"]
    day = check_day(text_field(fields, "date", "Date", required=True))

    presets = {
        str(entry.get("graphics_preset"))
        for run in runs if run.get("game_id") == game_id and isinstance(run.get("result"), list)
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

    run = {"gpu_id": gpu["id"], "game_id": game_id, "date": day}
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
    for key, label in (("os_detail", "OS version"), ("cpu", "CPU"), ("driver", "GPU driver")):
        value = text_field(fields, key, label)
        if value:
            system[key] = value
    memory_fields(fields, system)
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


def memory_fields(fields, system):
    """Optional RAM fields: '32' or '32 GB' -> memory_gb 32; 'dual' or '2' -> memory_channels 2."""
    size = text_field(fields, "memory_gb", "Memory (GB)")
    if size:
        memory_gb = checks.memory_gb_from_text(size)
        if not memory_gb or memory_gb > checks.MAX_MEMORY_GB:
            raise SubmissionError(f"**Memory (GB)** must be a number of GB such as `32`, not {code(size)}.")
        system["memory_gb"] = memory_gb
    kind = text_field(fields, "memory_type", "Memory type")
    if kind:
        system["memory_type"] = kind
    channels = text_field(fields, "memory_channels", "Memory channels").lower().removesuffix(" channel")
    if channels:
        count = checks.CHANNEL_WORDS.get(channels) or (int(channels) if channels.isdigit() else 0)
        if not 1 <= count <= checks.MAX_MEMORY_CHANNELS:
            raise SubmissionError(f"**Memory channels** must be a whole number such as `2` (dual channel), not {code(channels)}.")
        system["memory_channels"] = count


# --- Attached or pasted result files -------------------------------------------------


class GitHubRedirects(urllib.request.HTTPRedirectHandler):
    """Follow an attachment's redirect only to GitHub's own file storage."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urllib.parse.urlsplit(newurl)
        if parts.scheme != "https" or not (parts.hostname or "").endswith(DOWNLOAD_HOSTS):
            raise SubmissionError("The attached file redirected somewhere other than GitHub's file storage.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_attachment(url, attachment_dir):
    """An attachment's text: from GitHub, or from attachment_dir/<id>/<name> in tests."""
    file_id, name = ATTACHMENT.fullmatch(url).groups()
    if attachment_dir:
        path = attachment_dir / file_id / name
        if not path.is_file():
            raise SubmissionError(f"The attached file {code(name)} couldn't be downloaded.")
        data = path.read_bytes()
    else:
        deadline = time.monotonic() + DOWNLOAD_SECONDS
        chunks, size = [], 0
        try:
            with urllib.request.build_opener(GitHubRedirects).open(url, timeout=DOWNLOAD_SECONDS) as response:
                while size <= MAX_FILE_BYTES and time.monotonic() < deadline:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                else:
                    if size <= MAX_FILE_BYTES:
                        raise SubmissionError(f"The attached file {code(name)} took too long to download.")
        except (urllib.error.URLError, OSError, ValueError):
            raise SubmissionError(f"The attached file {code(name)} couldn't be downloaded. Attach it again.") from None
        data = b"".join(chunks)
    if len(data) > MAX_FILE_BYTES:
        raise SubmissionError(f"The attached file {code(name)} is larger than {MAX_FILE_BYTES // 1000:,} KB.")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SubmissionError(f"The attached file {code(name)} is not UTF-8 text.") from None


def issue_file(body, fields, attachment_dir=None, save_dir=None):
    """(label, text, is_json) for the one result file attached to or pasted into the issue."""
    links = list(dict.fromkeys(match.group(0) for match in ATTACHMENT.finditer(body)))
    attached = [url for url in links if url.lower().endswith(RESULT_SUFFIXES)]
    pasted = [(match.group(2).lower(), match.group(3)) for match in FENCED.finditer(body)]
    section = fields.get("file", "")
    if not attached and not pasted and section and not ANY_ATTACHMENT.search(section):
        # The file form's box with the file pasted in as plain text.
        pasted = [("yaml", section)]
    found = len(attached) + len(pasted)
    if found > 1:
        raise SubmissionError(
            f"This issue has {found} result files. Put one result file in each issue, "
            "or open a pull request for bulk uploads."
        )
    if attached:
        url = attached[0]
        name = ATTACHMENT.fullmatch(url).group(2)
        text = fetch_attachment(url, attachment_dir)
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            (save_dir / name).write_text(text, encoding="utf-8")
        return f"the attached file {code(name)}", text, name.lower().endswith(".json")
    if pasted:
        language, text = pasted[0]
        return "the pasted file", text, language == "json"
    if ANY_ATTACHMENT.search(body):
        raise NeedsMaintainer()
    raise SubmissionError(
        "The bot couldn't find a result in this issue. Fill in the "
        f"[Benchmark result]({ISSUES_URL}?template=benchmark.yml) form, or attach a result file "
        "(`.yaml`, `.yml`, or `.json`) with the "
        f"[Benchmark result (file)]({ISSUES_URL}?template=benchmark_file.yml) form "
        "or by dragging it into this issue's description."
    )


class NoAliasLoader(yaml.SafeLoader):
    """A SafeLoader that refuses YAML aliases, so a small file can't expand into a huge one."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise SubmissionError("The result file uses a YAML alias (`*name`). Write each value out instead.")
        return super().compose_node(parent, index)


def load_file(label, text, is_json):
    try:
        data = json.loads(text) if is_json else yaml.load(text, Loader=NoAliasLoader)
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        problem = " ".join(str(error).split())[:300]
        raise SubmissionError(f"{label[0].upper()}{label[1:]} isn't valid {'JSON' if is_json else 'YAML'}:\n\n{fence(problem)}") from None
    if not isinstance(data, dict):
        raise SubmissionError(f"{label[0].upper()}{label[1:]} isn't a result file: it needs `gpu_id`, `game_id`, `date`, and `result`.")
    return data


def run_from_file(data, author, credit_me, catalog, games):
    """A submitted result file, cleaned up for the community folder. Raises SubmissionError."""
    missing = [key for key in ("gpu_id", "game_id", "date", "result") if not data.get(key)]
    if missing:
        raise SubmissionError(f"The result file is missing {', '.join(f'`{key}`' for key in missing)}.")
    data = {key: value for key, value in data.items() if key not in DROPPED_KEYS}
    gpu = find_gpu(catalog, str(data.pop("gpu_id")))
    run = {"gpu_id": gpu["id"]}
    if credit_me:
        run["submitted_by"] = author
    run.update(data)
    run["game_id"] = find_game(games, str(run["game_id"]))["id"]
    if isinstance(run["date"], date):
        run["date"] = run["date"].isoformat()
    check_day(str(run["date"]))
    if isinstance(run.get("result"), list) and len(run["result"]) > MAX_RUNS:
        raise SubmissionError(f"The result file has more than {MAX_RUNS} runs. Open a pull request for bulk uploads.")
    return run


def target_path(data_dir, run):
    """The next free result_YYYYMMDD_<game_id>[_N].yaml in the GPU's community folder."""
    folder = data_dir / "community" / run["gpu_id"]
    stem = f"result_{run['date'].replace('-', '')}_{run['game_id']}"
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
        "# Released under CC BY 4.0 (see data/LICENSE).\n"
    )
    return header + yaml.dump(run, Dumper=IndentedDumper, sort_keys=False, default_flow_style=False, allow_unicode=True)


def check_file(path, data_dir, games):
    """The checks' issues for just this file."""
    catalog, _ = checks.load_catalog(data_dir)
    _, issues = checks.load_results(catalog, data_dir, games)
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


def pr_body(run, gpu, game, text, relative, issue, author, issues):
    notes = f"\n### Notes from the checks\n\n{fence(issue_lines(issues))}\n" if issues else ""
    return (
        f"Adds a community result submitted by @{author} in #{issue}.\n\n"
        f"- **GPU:** `{run['gpu_id']}` ({inline(checks.spec(gpu, 'identity', 'name', default=''))})\n"
        f"- **Game:** `{run['game_id']}` ({inline(game['name'])})\n"
        f"- **Runs:** {len(run['result'])}\n"
        f"- **File:** `{relative}`\n\n"
        f"{fence(text, 'yaml')}\n{notes}\n"
        f"Submitted under [CC BY 4.0]({LICENSE_URL}): submitting the issue releases the results.\n\n"
        "### Reviewer checklist\n\n"
        "- [ ] The numbers look plausible for this GPU, game, and preset.\n"
        "- [ ] Nothing suggests frame generation was on.\n"
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
    # Tests read attachments from <dir>/<id>/<name> instead of GitHub.
    parser.add_argument("--attachment-dir", type=Path, default=None, help=argparse.SUPPRESS)
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
    games, _ = checks.load_games(data_dir)
    fields = parse_issue_body(body)
    try:
        if "gpu" in fields:
            run = build_run(fields, args.author, catalog, games, data_dir)
        else:
            label, text, is_json = issue_file(body, fields, args.attachment_dir, args.out_dir / "attachments")
            credit_me = CREDIT_ME in checked(fields.get("credit", ""))
            run = run_from_file(load_file(label, text, is_json), args.author, credit_me, catalog, games)
        path = target_path(data_dir, run)
    except NeedsMaintainer:
        (args.out_dir / "comment.md").write_text(
            f"{MARKER}\n**Thanks! A maintainer will add this one by hand.** "
            "The bot only reads result files (`.yaml`, `.yml`, or `.json`), and this issue has other attachments, "
            "such as a raw capture or a screenshot. "
            f"Submitting it releases the results under [CC BY 4.0]({LICENSE_URL}).",
            encoding="utf-8",
        )
        print("Attachments need a maintainer")
        return 3
    except SubmissionError as error:
        return fail(str(error))

    text = file_text(run, args.issue)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    issues = check_file(path, data_dir, games)
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
    game = next(game for game in games if game["id"] == run["game_id"])
    (args.out_dir / "path.txt").write_text(relative, encoding="utf-8")
    (args.out_dir / "title.txt").write_text(f"Benchmark: {name}, {' '.join(game['name'].split())[:80]} (#{args.issue})", encoding="utf-8")
    (args.out_dir / "pr_body.md").write_text(pr_body(run, gpu, game, text, relative, args.issue, args.author, issues), encoding="utf-8")
    runs = len(run["result"])
    (args.out_dir / "comment.md").write_text(
        f"{MARKER}\n**Thanks!** This issue became `{relative}` with {runs} run{'s' if runs != 1 else ''}. "
        "A maintainer will review the pull request below. "
        "Edit this issue if something is wrong and the pull request updates by itself. "
        f"Your results are public data under [CC BY 4.0]({LICENSE_URL}).",
        encoding="utf-8",
    )
    print(f"Wrote {relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
