"""Shared rules for catalog entries and benchmark result files.

build.py and validate.py both run these checks, so every rule is written once.
Checks append an Issue instead of raising, so a single run reports every
problem in every file. Each Issue names a rule; the rule name is a heading in
data/gpus/README.md (catalog) or docs/COMMUNITY_SUBMISSIONS.md (results).
"""
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CATALOG_DOC = "data/gpus/README.md"
RESULTS_DOC = "docs/COMMUNITY_SUBMISSIONS.md"
REPO_URL = "https://github.com/MattyStacks/open-gpu-benchmarks/blob/main"

GPU_VENDORS = ("amd", "intel", "nvidia")
GPU_FORM_FACTORS = ("desktop", "laptop", "handheld", "igpu")
RESULT_SOURCES = ("official", "community")
RESULT_GLOBS = ("result_*.yaml", "result_*.yml")
OUTLIER_RATIO = 0.5
GITHUB_USER_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
MEMORY_TOKEN = re.compile(r"^(\d+)gb$")
FULL_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_OR_DATE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?$")
# A value that starts with { or [ after "key:" or "-" is inline (flow) YAML.
INLINE_STYLE = re.compile(r"""^\s*(?:-\s+)*(?:[^\s#'"][^:#'"]*:\s+)?[\[{]""")

# Every catalog field and its kind. Unknown keys are rejected so typos surface.
CATALOG_FIELDS = {
    "identity": {"name": "string", "codename": "string", "gpu_vendor": "string"},
    "classification": {"form_factor": "string", "architecture": "string"},
    "silicon": {
        "process": "string",
        "die_size_mm2": "number",
        "transistors_b": "number",
        "shader_cores": "number",
        "rt_cores": "number",
        "tmus": "number",
        "rops": "number",
    },
    "memory": {
        "capacity_gb": "number",
        "type": "string",
        "bus_width_bits": "number",
        "bandwidth_gbs": "number",
        "shared": "bool",
    },
    "clocks": {"base_mhz": "number", "boost_mhz": "number", "mem_mhz": "number"},
    "power": {"tdp_w": "number", "connectors": "string_list", "pcie": "string"},
    "release": {"date": "full_date", "msrp_usd": "number", "msrp_history": "msrp_history"},
    "features": {
        "dlss": "string",
        "fsr": "string",
        "xess": "string",
        "av1": "string",
        "outputs": "string_list",
    },
}
CATALOG_TOP_LEVEL = ("id", "notes", *CATALOG_FIELDS)
CATALOG_REQUIRED = (
    ("id",),
    ("identity", "name"),
    ("identity", "gpu_vendor"),
    ("classification", "form_factor"),
    ("memory", "capacity_gb"),
)
CATALOG_RANGES = {
    ("memory", "capacity_gb"): (1, 512, "GB"),
    ("memory", "bus_width_bits"): (32, 512, "bits"),
    ("power", "tdp_w"): (5, 600, "W"),
}
RESULT_ENTRY_REQUIRED = ("resolution", "graphics_preset", "avg_fps", "p1_low")


@dataclass
class Issue:
    path: str
    level: str  # "error" or "warning"
    rule: str
    message: str

    def doc(self):
        in_results = any(part in ("official", "community") for part in self.path.split("/"))
        return RESULTS_DOC if in_results or self.rule.startswith(("result-", "community-")) else CATALOG_DOC

    def format(self):
        see = f"See {REPO_URL}/{self.doc()}#{self.rule}"
        if os.getenv("GITHUB_ACTIONS") == "true":
            return f"::{self.level} file={self.path}::[{self.rule}] {self.message}. {see}"
        return f"{self.level}: {self.path}: [{self.rule}] {self.message}\n    {see}"


class Issues(list):
    def error(self, path, rule, message):
        self.append(Issue(relative_path(path), "error", rule, message))

    def warning(self, path, rule, message):
        self.append(Issue(relative_path(path), "warning", rule, message))

    @property
    def errors(self):
        return [issue for issue in self if issue.level == "error"]

    @property
    def warnings(self):
        return [issue for issue in self if issue.level == "warning"]


def relative_path(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def report(issues, label, show_warnings=True):
    """Print the issues plus a one-line summary; return True when errors exist."""
    shown = issues if show_warnings else issues.errors
    for issue in sorted(shown, key=lambda issue: (issue.path, issue.level != "error", issue.rule)):
        print(issue.format())
    errors, warnings = len(issues.errors), len(issues.warnings)
    print(f"{label}: {errors} error(s), {warnings} warning(s) - {'FAILED' if errors else 'PASSED'}")
    return bool(errors)


def spec(entry, *path, default=None):
    value = entry
    for key in path:
        if not isinstance(value, dict) or value.get(key) is None:
            return default
        value = value[key]
    return value


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def load_yaml_file(path, issues):
    """Return (parsed, data) for one YAML file, reporting syntax and inline-style problems."""
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if INLINE_STYLE.match(line):
            issues.error(
                path,
                "yaml-inline",
                f"line {number} uses inline {{ }} or [ ] YAML; write each item on its own line "
                "(lists use '- item', and omit empty fields instead of writing {} or [])",
            )
    try:
        return True, yaml.safe_load(text)
    except yaml.YAMLError as error:
        issues.error(path, "yaml-invalid", " ".join(f"YAML could not be parsed: {error}".split()))
        return False, None


# --- Catalog -----------------------------------------------------------------


def catalog_paths(data_dir):
    gpus_dir = data_dir / "gpus"
    return sorted(path for path in gpus_dir.rglob("*") if path.suffix in (".yaml", ".yml"))


def check_value(path, issues, label, kind, value):
    if kind == "string" and not is_text(value):
        hint = f" (quote it: '{value}')" if is_number(value) else ""
        issues.error(path, "field-type", f"'{label}' must be text{hint}")
    elif kind == "number" and not is_number(value):
        issues.error(path, "field-type", f"'{label}' must be a number, got '{value}'")
    elif kind == "bool" and not isinstance(value, bool):
        issues.error(path, "field-type", f"'{label}' must be true or false")
    elif kind == "full_date" and not (isinstance(value, str) and FULL_DATE.match(value)):
        hint = " (quote it: '2022-10-12')" if isinstance(value, (date, datetime)) else ""
        issues.error(path, "field-type", f"'{label}' must be a quoted 'YYYY-MM-DD' date{hint}")
    elif kind == "string_list" and (
        not isinstance(value, list) or not value or not all(is_text(item) for item in value)
    ):
        issues.error(path, "field-type", f"'{label}' must be a list with one text item per '-' line")
    elif kind == "msrp_history":
        check_msrp_history(path, issues, label, value)


def check_msrp_history(path, issues, label, history):
    if not isinstance(history, list) or not history:
        issues.error(path, "field-type", f"'{label}' must be a list with one '-' item per price")
        return
    for index, row in enumerate(history):
        row_label = f"{label}[{index}]"
        if not isinstance(row, dict):
            issues.error(path, "field-type", f"'{row_label}' must have date and price_usd fields")
            continue
        for key in row:
            if key not in ("date", "price_usd", "label"):
                issues.error(path, "field-unknown", f"'{row_label}.{key}' is not a known field")
        row_date = row.get("date")
        if not (isinstance(row_date, str) and MONTH_OR_DATE.match(row_date)):
            issues.error(path, "field-type", f"'{row_label}.date' must be a quoted 'YYYY-MM' or 'YYYY-MM-DD' date")
        if not is_number(row.get("price_usd")):
            issues.error(path, "field-type", f"'{row_label}.price_usd' must be a number")
        if "label" in row and not is_text(row["label"]):
            issues.error(path, "field-type", f"'{row_label}.label' must be text")


def check_catalog_fields(path, entry, issues):
    for key, value in entry.items():
        if key not in CATALOG_TOP_LEVEL:
            issues.error(path, "field-unknown", f"'{key}' is not a known catalog field")
        elif key in CATALOG_FIELDS:
            if not isinstance(value, dict):
                issues.error(path, "field-type", f"'{key}' must be a section with indented fields")
                continue
            for field, field_value in value.items():
                label = f"{key}.{field}"
                if key == "identity" and field == "vendor":
                    issues.error(path, "field-renamed", "rename 'identity.vendor' to 'identity.gpu_vendor'")
                elif field not in CATALOG_FIELDS[key]:
                    issues.error(path, "field-unknown", f"'{label}' is not a known catalog field")
                elif field_value is not None:
                    check_value(path, issues, label, CATALOG_FIELDS[key][field], field_value)
        elif key == "notes" and not is_text(value):
            issues.error(path, "field-type", "'notes' must be text")

    for field_path in CATALOG_REQUIRED:
        label = ".".join(field_path)
        if spec(entry, *field_path) is None and not (
            field_path == ("identity", "gpu_vendor") and spec(entry, "identity", "vendor") is not None
        ):
            issues.error(path, "field-required", f"'{label}' is required")

    vendor = spec(entry, "identity", "gpu_vendor")
    if vendor is not None and vendor not in GPU_VENDORS:
        issues.error(path, "field-value", f"gpu_vendor '{vendor}' must be one of {', '.join(GPU_VENDORS)}")
    form_factor = spec(entry, "classification", "form_factor")
    if form_factor is not None and form_factor not in GPU_FORM_FACTORS:
        issues.error(
            path, "field-value", f"form_factor '{form_factor}' must be one of {', '.join(GPU_FORM_FACTORS)}"
        )
    for field_path, (low, high, unit) in CATALOG_RANGES.items():
        value = spec(entry, *field_path)
        if is_number(value) and not low <= value <= high:
            issues.error(path, "field-range", f"'{'.'.join(field_path)}' {value} is outside {low}-{high} {unit}")


def check_catalog_id(path, entry, issues):
    gpu_id = entry.get("id")
    if not isinstance(gpu_id, str):
        return
    if path.stem != gpu_id or path.suffix != ".yaml":
        issues.error(path, "id-filename", f"file must be named '{gpu_id}.yaml' to match its id")
    if not ID_PATTERN.match(gpu_id):
        issues.error(path, "id-format", f"id '{gpu_id}' may only use lowercase letters, digits, and single underscores")
        return

    tokens = gpu_id.split("_")
    memory_positions = [index for index, token in enumerate(tokens) if MEMORY_TOKEN.match(token)]
    if len(memory_positions) != 1:
        issues.error(path, "id-memory-token", f"id '{gpu_id}' must contain exactly one memory size token such as '16gb'")
        return
    position = memory_positions[0]
    capacity = spec(entry, "memory", "capacity_gb")
    token_gb = int(MEMORY_TOKEN.match(tokens[position]).group(1))
    if is_number(capacity) and capacity != token_gb:
        issues.error(
            path, "id-memory-token", f"id says {token_gb}gb but memory.capacity_gb is {capacity}"
        )

    form_factor = spec(entry, "classification", "form_factor")
    before, after = tokens[:position], tokens[position + 1:]
    shapes = {
        "desktop": (bool(before) and bool(after), "<gpu_model>_<vram>gb_<brand>_<product_line> (or _fe, _reference, _le)"),
        "laptop": (bool(before) and bool(after), "<gpu_model>_<vram>gb_<oem>_<model> (or _generic)"),
        "handheld": (bool(before) and not after, "<device>_<chip>_<ram>gb, ending with the RAM size"),
        "igpu": (bool(before), "<chip>_<ram>gb_..."),
    }
    if form_factor in shapes and not shapes[form_factor][0]:
        issues.error(path, "id-format", f"{form_factor} ids follow {shapes[form_factor][1]}")

    if "generic" in tokens:
        if form_factor != "laptop":
            issues.error(path, "id-generic", "'generic' is only allowed in laptop ids")
        elif after != ["generic"]:
            issues.error(path, "id-generic", "'generic' replaces the whole <oem>_<model> part: <gpu_model>_<vram>gb_generic")
        else:
            issues.warning(path, "id-generic", "laptop model is unknown; replace '_generic' with <oem>_<model> when known")


def check_catalog_folder(path, entry, gpus_dir, issues):
    parts = path.relative_to(gpus_dir).parts
    form_factor = spec(entry, "classification", "form_factor")
    vendor = spec(entry, "identity", "gpu_vendor", default=spec(entry, "identity", "vendor"))
    expected = f"data/gpus/{form_factor}/{vendor}/{entry.get('id')}.yaml"
    if len(parts) != 3 or parts[0] != form_factor or parts[1] != vendor:
        issues.error(path, "catalog-folder", f"file belongs at {expected} (data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml)")


def load_catalog(data_dir=DATA_DIR):
    """Return (entries, issues). Entries include every mapping with a string id."""
    issues = Issues()
    gpus_dir = data_dir / "gpus"
    entries = []
    seen = {}
    paths = catalog_paths(data_dir)
    if not paths:
        issues.error(gpus_dir, "catalog-empty", "no catalog entries found under data/gpus/")
    for path in paths:
        parsed, entry = load_yaml_file(path, issues)
        if not parsed:
            continue
        if not isinstance(entry, dict):
            issues.error(path, "catalog-not-mapping", "a catalog file holds one entry with fields at the left margin, not an empty file or a '-' list")
            continue
        gpu_id = entry.get("id")
        if not is_text(gpu_id):
            issues.error(path, "field-required", "'id' is required and must be text")
            continue
        if gpu_id in seen:
            issues.error(path, "id-duplicate", f"id '{gpu_id}' is already used by {relative_path(seen[gpu_id])}")
            continue
        seen[gpu_id] = path
        check_catalog_fields(path, entry, issues)
        check_catalog_id(path, entry, issues)
        check_catalog_folder(path, entry, gpus_dir, issues)
        entries.append(entry)
    entries.sort(
        key=lambda entry: (
            GPU_FORM_FACTORS.index(spec(entry, "classification", "form_factor"))
            if spec(entry, "classification", "form_factor") in GPU_FORM_FACTORS
            else len(GPU_FORM_FACTORS),
            str(spec(entry, "identity", "gpu_vendor", default="")),
            entry["id"],
        )
    )
    return entries, issues


# --- Results -----------------------------------------------------------------


def result_paths(data_dir, source):
    paths = set()
    for pattern in RESULT_GLOBS:
        paths.update((data_dir / source).glob(f"*/{pattern}"))
    return sorted(paths)


def stray_result_paths(data_dir, source):
    """YAML files sitting in a GPU folder that the build would silently skip."""
    return sorted(
        path
        for path in (data_dir / source).glob("*/*")
        if path.suffix in (".yaml", ".yml") and not path.name.startswith("result_")
    )


def gpu_power_w(run):
    system = run.get("system") or {}
    return run.get("gpu_power_w", run.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w"))))


def submitter_errors(path, run, issues):
    submitted_by = run.get("submitted_by")
    if not submitted_by:
        issues.error(path, "community-submitter", "missing submitted_by; set it to your GitHub username")
        return
    submitted_by = str(submitted_by)
    if not GITHUB_USER_PATTERN.match(submitted_by):
        issues.error(path, "community-submitter", f"submitted_by '{submitted_by}' is not a valid GitHub username")
        return
    expected = rf"^result_\d{{8}}_.+_{re.escape(submitted_by.lower())}$"
    if not re.match(expected, path.stem.lower()):
        issues.error(
            path,
            "community-filename",
            f"file name '{path.name}' must follow result_YYYYMMDD_<game>_{submitted_by.lower()}{path.suffix}",
        )


def community_warnings(path, run, gpu, issues):
    if gpu is not None and spec(gpu, "classification", "form_factor") == "laptop" and gpu_power_w(run) is None:
        issues.warning(path, "result-laptop-tgp", "laptop submission has no TGP; add gpu_power_w when discoverable")
    if not (run.get("system") or {}).get("driver") and not run.get("driver"):
        issues.warning(path, "result-no-driver", "missing optional driver; add it when available")
    proof = run.get("proof") or {}
    if not proof.get("raw_log"):
        if proof.get("summary_source"):
            issues.warning(path, "result-no-proof", "summary-only submission; raw proof is encouraged")
        else:
            issues.warning(path, "result-no-proof", "no raw_log or summary_source proof reference")


def check_result_file(source, path, run, catalog_by_id, issues):
    """Check one result file; return its result entries when they are usable."""
    if not isinstance(run, dict):
        issues.error(path, "result-not-mapping", "a result file holds fields at the left margin, not an empty file or a '-' list")
        return None
    gpu_id = run.get("gpu_id")
    if path.parent.name != gpu_id:
        issues.error(path, "result-folder", f"gpu_id '{gpu_id}' must match its folder '{path.parent.name}'")
    gpu = catalog_by_id.get(gpu_id)
    if gpu is None:
        issues.error(path, "result-unknown-gpu", f"gpu_id '{gpu_id}' is not in the catalog under data/gpus/")
    if source == "community":
        submitter_errors(path, run, issues)

    entries = run.get("result")
    if not isinstance(entries, list) or not entries:
        issues.error(path, "result-list", "result must be a list with one '-' item per resolution/preset profile")
        return None
    if not all(isinstance(entry, dict) for entry in entries):
        issues.error(path, "result-list", "every result item must hold fields such as resolution and avg_fps")
        return None

    if gpu is not None:
        catalog_form = spec(gpu, "classification", "form_factor")
        form_factor = str(run.get("form_factor", catalog_form)).lower()
        if form_factor != catalog_form:
            issues.error(path, "result-form-factor", f"form_factor '{form_factor}' does not match catalog value '{catalog_form}'")

    if run.get("benchmark_type", "game") != "game":
        return entries
    if not run.get("game"):
        issues.error(path, "result-field", "missing game")
    if run.get("frame_generation", False):
        issues.error(path, "result-frame-generation", "frame generation must be disabled for comparable game runs")
    if source == "community":
        community_warnings(path, run, gpu, issues)

    usable = True
    for index, entry in enumerate(entries):
        label = f"result[{index}]"
        entry_ok = True
        for field in RESULT_ENTRY_REQUIRED:
            if entry.get(field) is None:
                issues.error(path, "result-field", f"{label} missing {field}")
                entry_ok = False
        for field in ("avg_fps", "p1_low"):
            if entry.get(field) is not None and not is_number(entry[field]):
                issues.error(path, "result-field", f"{label} {field} must be a number")
                entry_ok = False
        usable = usable and entry_ok
        if entry_ok and float(entry["p1_low"]) > float(entry["avg_fps"]):
            issues.error(path, "result-impossible", f"{label} p1_low {entry['p1_low']} > avg_fps {entry['avg_fps']} is impossible")
        if entry.get("frame_generation", False):
            issues.error(path, "result-frame-generation", f"{label} must disable frame generation for comparable game runs")
    return entries if usable else None


def official_baseline(run, entry, official_runs):
    power = gpu_power_w(run)
    matches = [
        float(other_entry["avg_fps"])
        for other, other_entries in official_runs
        if other.get("gpu_id") == run.get("gpu_id") and other.get("game") == run.get("game")
        for other_entry in other_entries
        if other_entry.get("resolution") == entry.get("resolution")
        and other_entry.get("graphics_preset") == entry.get("graphics_preset")
        and (power is None or gpu_power_w(other) in (None, power))
    ]
    return sum(matches) / len(matches) if matches else None


def check_outliers(community_runs, official_runs, issues):
    for path, run, entries in community_runs:
        if run.get("benchmark_type", "game") != "game":
            continue
        for index, entry in enumerate(entries):
            baseline = official_baseline(run, entry, official_runs)
            if baseline is None:
                issues.warning(path, "result-no-baseline", f"result[{index}] has no matching official baseline; maintainer review is required")
            elif baseline > 0 and abs(float(entry["avg_fps"]) - baseline) / baseline > OUTLIER_RATIO:
                difference = abs(float(entry["avg_fps"]) - baseline) / baseline
                issues.error(
                    path,
                    "community-outlier",
                    f"result[{index}] avg_fps {entry['avg_fps']} differs {difference:.0%} from the matching "
                    f"official baseline {baseline:.1f}; correct it, explain the profile difference, or remove the entry",
                )


def load_results(catalog, data_dir=DATA_DIR):
    """Return ({source: [(path, run)]}, issues) for every usable result file."""
    issues = Issues()
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    runs = {}
    for source in RESULT_SOURCES:
        runs[source] = []
        for path in stray_result_paths(data_dir, source):
            issues.error(path, "result-filename", "result files must be named result_YYYYMMDD_<...>.yaml or the build skips them")
        for path in result_paths(data_dir, source):
            parsed, run = load_yaml_file(path, issues)
            if not parsed:
                continue
            entries = check_result_file(source, path, run, catalog_by_id, issues)
            if entries is not None:
                runs[source].append((path, run, entries))
    official = [(run, entries) for _, run, entries in runs["official"] if run.get("benchmark_type", "game") == "game"]
    check_outliers(runs["community"], official, issues)
    return {source: [(path, run) for path, run, _ in items] for source, items in runs.items()}, issues
