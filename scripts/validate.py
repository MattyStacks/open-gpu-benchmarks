"""Validate GPU-rooted community benchmark result files."""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml")
    sys.exit(1)

from build import catalog_form_factor, validate_gpu_catalog


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTLIER_RATIO = 0.5
GITHUB_USER_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
RESULT_GLOBS = ("result_*.yaml", "result_*.yml")


def load_yaml(path):
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source) or {}


def result_paths(source):
    paths = set()
    for pattern in RESULT_GLOBS:
        paths.update((DATA_DIR / source).glob(f"*/{pattern}"))
    return sorted(paths)


def result_entries(data, path):
    entries = data.get("result")
    if not isinstance(entries, list) or not entries:
        return None, [f"{path}: result must be a non-empty list"]
    if not all(isinstance(entry, dict) for entry in entries):
        return None, [f"{path}: every result entry must be a mapping"]
    return entries, []


def gpu_catalog():
    return {gpu["id"]: gpu for gpu in validate_gpu_catalog(load_yaml(DATA_DIR / "gpus.yaml"))}


def gpu_power_w(data):
    system = data.get("system", {})
    return data.get(
        "gpu_power_w",
        data.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w"))),
    )


def official_records(catalog):
    records = []
    for path in result_paths("official"):
        data = load_yaml(path)
        entries, errors = result_entries(data, path)
        if errors or data.get("benchmark_type", "game") != "game":
            continue
        gpu = catalog.get(data.get("gpu_id"))
        if not gpu:
            continue
        for result in entries:
            records.append(
                {
                    "gpu_id": data.get("gpu_id"),
                    "game": data.get("game"),
                    "resolution": result.get("resolution"),
                    "graphics_preset": result.get("graphics_preset"),
                    "form_factor": data.get("form_factor", catalog_form_factor(gpu)),
                    "gpu_power_w": gpu_power_w(data),
                    "avg_fps": result.get("avg_fps"),
                }
            )
    return records


def matching_official_baseline(data, result, baselines, catalog):
    gpu = catalog[data["gpu_id"]]
    form_factor = data.get("form_factor", catalog_form_factor(gpu))
    power = gpu_power_w(data)
    candidates = [
        record
        for record in baselines
        if record["gpu_id"] == data["gpu_id"]
        and record["game"] == data.get("game")
        and record["resolution"] == result.get("resolution")
        and record["graphics_preset"] == result.get("graphics_preset")
        and form_factor.lower() == str(record["form_factor"]).lower()
        and (power is None or record["gpu_power_w"] in (None, power))
        and record["avg_fps"] is not None
    ]
    if not candidates:
        return None
    return sum(float(record["avg_fps"]) for record in candidates) / len(candidates)


def submitter_errors(path, data):
    submitted_by = data.get("submitted_by")
    if not submitted_by:
        return ["missing submitted_by; set it to your GitHub username"]
    submitted_by = str(submitted_by)
    if not GITHUB_USER_PATTERN.match(submitted_by):
        return [f"submitted_by '{submitted_by}' is not a valid GitHub username"]
    expected = rf"^result_\d{{8}}_.+_{re.escape(submitted_by.lower())}$"
    if not re.match(expected, path.stem.lower()):
        return [
            f"file name '{path.name}' must follow "
            f"result_YYYYMMDD_<game>_{submitted_by.lower()}{path.suffix}"
        ]
    return []


def validate_file(path, data, catalog):
    errors = []
    warnings = []
    gpu_id = data.get("gpu_id")
    if path.parent.name != gpu_id:
        errors.append(f"gpu_id '{gpu_id}' must match GPU folder '{path.parent.name}'")
    if gpu_id not in catalog:
        return [*errors, f"unknown gpu_id '{gpu_id}'"], warnings, None
    errors.extend(submitter_errors(path, data))

    form_factor = str(data.get("form_factor", catalog_form_factor(catalog[gpu_id]))).lower()
    if form_factor != catalog_form_factor(catalog[gpu_id]):
        errors.append(
            f"form_factor '{form_factor}' does not match catalog value "
            f"'{catalog_form_factor(catalog[gpu_id])}'"
        )
    entries, entry_errors = result_entries(data, path)
    errors.extend(entry_errors)
    if entries is None:
        return errors, warnings, None

    benchmark_type = data.get("benchmark_type", "game")
    if benchmark_type != "game":
        return errors, warnings, entries
    if not data.get("game"):
        errors.append("missing game")
    if data.get("frame_generation", False):
        errors.append("frame generation must be disabled for comparable game runs")
    if form_factor == "laptop" and gpu_power_w(data) is None:
        warnings.append("laptop submission has no TGP; add it when discoverable")
    if not data.get("system", {}).get("driver"):
        warnings.append("missing optional driver; add it when available")
    proof = data.get("proof", {})
    if not proof.get("raw_log"):
        if proof.get("summary_source"):
            warnings.append("summary-only submission; raw proof is encouraged")
        else:
            warnings.append("no raw_log or summary_source proof reference")

    for result_index, result in enumerate(entries):
        label = f"result[{result_index}]"
        for field in ("resolution", "graphics_preset", "avg_fps", "p1_low"):
            if result.get(field) is None:
                errors.append(f"{label} missing {field}")
        if (
            result.get("avg_fps") is not None
            and result.get("p1_low") is not None
            and float(result["p1_low"]) > float(result["avg_fps"])
        ):
            errors.append(
                f"{label} p1_low {result['p1_low']} > avg_fps {result['avg_fps']} is impossible"
            )
        if result.get("frame_generation", False):
            errors.append(f"{label} must disable frame generation for comparable game runs")
    return errors, warnings, entries


def main():
    catalog = gpu_catalog()
    community_paths = result_paths("community")
    if not community_paths:
        print("No community result files")
        return 0

    baselines = official_records(catalog)
    failed = False
    for path in community_paths:
        print(f"\nChecking {path.relative_to(ROOT)}")
        try:
            data = load_yaml(path)
        except yaml.YAMLError as error:
            print(f"::error:: Invalid YAML {path}: {error}")
            failed = True
            continue

        errors, warnings, entries = validate_file(path, data, catalog)
        for error in errors:
            print(f"::error:: {path}: {error}")
        for warning in warnings:
            print(f"::warning:: {path}: {warning}")
        failed = failed or bool(errors)

        if errors or data.get("benchmark_type", "game") != "game":
            continue
        for result_index, result in enumerate(entries):
            baseline = matching_official_baseline(data, result, baselines, catalog)
            avg_fps = result.get("avg_fps")
            if baseline and avg_fps:
                difference = abs(float(avg_fps) - baseline) / baseline
                if difference > OUTLIER_RATIO:
                    print(
                        f"::error:: {path}: result[{result_index}] avg_fps {avg_fps} differs "
                        f"{difference:.0%} from matching official baseline {baseline:.1f}; "
                        "correct, explain the profile difference, or remove the entry"
                    )
                    failed = True
            elif not baseline:
                print(
                    f"::warning:: result[{result_index}] has no matching official baseline; "
                    "maintainer review is required"
                )

    print("\nValidation done" + (" - FAILED" if failed else " - PASSED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
