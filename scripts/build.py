"""
Build static API data for the GitHub Pages dashboard.

Source data remains reviewable YAML. Raw capture files stay alongside the YAML
that references them, but are not included in the browser-facing API.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "site" / "api" / "v1"
SCHEMA_VERSION = "0.3"
RELEASE_VERSION = "0.2.0"


def load_yaml(path):
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source) or {}


def relative_path(path):
    return path.relative_to(ROOT).as_posix()


def run_id(source, path, index):
    return f"{source}-{path.parent.name}-{path.stem}-{index}"


def build_record(run, source, source_path, index, gpu_by_id, defaults):
    gpu_id = run.get("gpu_id")
    gpu = gpu_by_id.get(gpu_id)
    if not gpu:
        raise ValueError(f"{source_path}: unknown gpu_id '{gpu_id}'")

    results = run.get("results", run)
    avg_fps = results.get("avg_fps")
    p1_low = results.get("p1_low")
    if avg_fps is None or p1_low is None:
        raise ValueError(f"{source_path}: each run needs avg_fps and p1_low")
    if float(p1_low) > float(avg_fps):
        raise ValueError(f"{source_path}: p1_low cannot exceed avg_fps")

    system = run.get("system", {})
    proof = run.get("proof", {})
    raw_log = proof.get("raw_log")
    summary_source = proof.get("summary_source")
    gpu_power_w = run.get("gpu_power_w", run.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w"))))
    implementation_name = run.get("device_name", run.get("implementation_name", system.get("device_name")))
    return {
        "id": run_id(source, source_path, index),
        "source": source,
        "gpu_id": gpu_id,
        "gpu_name": gpu["name"],
        "vendor": gpu["vendor"],
        "form_factor": run.get("form_factor", gpu["form_factor"]).title(),
        "vram_gb": gpu.get("vram_gb"),
        "tdp_w": gpu.get("tdp_w"),
        "game": run.get("game", defaults.get("game")),
        "game_version": str(run.get("version", defaults.get("version", ""))),
        "resolution": run.get("resolution"),
        "graphics_preset": run.get("graphics_preset", ""),
        "upscaling": run.get("upscaling", ""),
        "frame_generation": bool(run.get("frame_generation", False)),
        "avg_fps": round(float(avg_fps), 2),
        "p1_low": round(float(p1_low), 2),
        "driver": str(system.get("driver", run.get("driver", ""))),
        "implementation_name": implementation_name or "",
        "gpu_power_w": float(gpu_power_w) if gpu_power_w is not None else None,
        "overclocked": bool(run.get("overclocked", False)),
        "cpu": str(system.get("cpu", "")),
        "memory": str(system.get("memory", system.get("ram", ""))),
        "power_mode": str(system.get("power_mode", system.get("tdp_mode", ""))),
        "display_mode": str(system.get("display_mode", "")),
        "proof_level": "raw-log" if raw_log else "summary-only",
        "proof_reference": raw_log or summary_source or "",
        "source_file": relative_path(source_path),
        "synthetic": bool(run.get("synthetic", defaults.get("synthetic", False))),
    }


def official_records(gpu_by_id):
    records = []
    official_dir = DATA_DIR / "official"
    if not official_dir.exists():
        return records

    for path in sorted(official_dir.rglob("summary.yaml")):
        summary = load_yaml(path)
        defaults = {
            "game": summary.get("game", path.parent.name.replace("_", " ").title()),
            "version": summary.get("version", ""),
            "synthetic": summary.get("synthetic", False),
        }
        for index, run in enumerate(summary.get("runs", [summary])):
            records.append(build_record(run, "official", path, index, gpu_by_id, defaults))
    return records


def community_records(gpu_by_id):
    records = []
    approved_dir = DATA_DIR / "community" / "approved"
    if not approved_dir.exists():
        return records

    for path in sorted(approved_dir.rglob("*.yaml")):
        records.append(build_record(load_yaml(path), "community", path, 0, gpu_by_id, {}))
    return records


def community_averages(records):
    return aggregate_records(records, "community-average")


def aggregate_records(records, id_prefix):
    grouped = defaultdict(list)
    for record in records:
        grouped[
            (
                record["gpu_id"],
                record["game"],
                record["resolution"],
                record["graphics_preset"],
                record["form_factor"],
                record["gpu_power_w"],
            )
        ].append(record)

    averages = []
    for runs in grouped.values():
        first = runs[0]
        implementations = [
            {
                key: run[key]
                for key in (
                    "implementation_name",
                    "gpu_power_w",
                    "overclocked",
                    "cpu",
                    "memory",
                    "power_mode",
                    "display_mode",
                    "driver",
                )
                if run[key] not in ("", None)
            }
            for run in runs
        ]
        averages.append(
            {
                **first,
                "id": f"{id_prefix}-{first['id']}",
                "run_count": len(runs),
                "avg_fps": round(sum(run["avg_fps"] for run in runs) / len(runs), 2),
                "p1_low": round(sum(run["p1_low"] for run in runs) / len(runs), 2),
                "avg_fps_range": [min(run["avg_fps"] for run in runs), max(run["avg_fps"] for run in runs)],
                "p1_low_range": [min(run["p1_low"] for run in runs), max(run["p1_low"] for run in runs)],
                "implementations": implementations,
            }
        )
    return averages


def write_json(name, payload):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / name).open("w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
        output.write("\n")


def main():
    gpus = load_yaml(DATA_DIR / "gpus.yaml")
    reviews_source = load_yaml(DATA_DIR / "reviews.yaml")
    gpu_by_id = {gpu["id"]: gpu for gpu in gpus}
    official = official_records(gpu_by_id)
    community_raw = community_records(gpu_by_id)
    official_summaries = aggregate_records(official, "official-summary")
    community = community_averages(community_raw)
    dashboard_records = sorted(
        [*official_summaries, *community],
        key=lambda record: (
            record["game"],
            record["resolution"],
            record["source"],
            -record["avg_fps"],
        ),
    )
    games = sorted({record["game"] for record in dashboard_records})
    resolutions = sorted(
        {record["resolution"] for record in dashboard_records},
        key=lambda value: (
            0,
            int(value.removesuffix("p")),
        )
        if value.endswith("p")
        else (1, value),
    )
    preset_order = ["Low", "Medium", "High", "Ultra", "Steam Deck"]
    graphics_presets = sorted(
        {*preset_order, *(record["graphics_preset"] for record in dashboard_records)},
        key=lambda preset: (
            preset_order.index(preset) if preset in preset_order else len(preset_order),
            preset,
        ),
    )
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "release_version": os.getenv("RELEASE_VERSION", RELEASE_VERSION),
        "commit": os.getenv("GITHUB_SHA", "local")[:12],
        "generated_at": datetime.now(UTC).isoformat(),
        "synthetic_data": any(record["synthetic"] for record in dashboard_records),
        "comparison_policy": {
            "group_by": ["gpu_id", "form_factor", "gpu_power_w", "game", "resolution", "graphics_preset"],
            "game_version_is_not_a_grouping_key": True,
            "frame_generation": "off",
            "community_outlier_threshold": 0.5,
        },
    }

    write_json("gpus.json", {"metadata": metadata, "gpus": gpus})
    write_json("official.json", {"metadata": metadata, "records": official, "count": len(official)})
    write_json(
        "community.json",
        {"metadata": metadata, "records": community, "count": len(community), "raw_count": len(community_raw)},
    )
    write_json(
        "dashboard.json",
        {
            "metadata": metadata,
            "games": games,
            "resolutions": resolutions,
            "graphics_presets": graphics_presets,
            "records": dashboard_records,
            "reviews": reviews_source.get("reviews", []),
        },
    )

    print(
        f"GPUs: {len(gpus)} | Official: {len(official)} | "
        f"Community summaries: {len(community)} | Output: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
