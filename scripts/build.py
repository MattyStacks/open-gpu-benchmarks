"""Build GPU-rooted API data for the GitHub Pages dashboard."""
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

import checks
from checks import DATA_DIR, ROOT, relative_path, spec


OUTPUT_DIR = ROOT / "site" / "api" / "v1"
SCHEMA_VERSION = "0.9"
RELEASE_VERSION = "0.5.0"


def load_yaml(path):
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source) or {}


def catalog_name(gpu):
    return spec(gpu, "identity", "name")


def catalog_vendor(gpu):
    return spec(gpu, "identity", "gpu_vendor")


def catalog_form_factor(gpu):
    return spec(gpu, "classification", "form_factor")


def catalog_vram_gb(gpu):
    if spec(gpu, "memory", "shared", default=False):
        return None
    return spec(gpu, "memory", "capacity_gb")


def catalog_tdp_w(gpu):
    return spec(gpu, "power", "tdp_w")


def run_id(source, path, result_index):
    return f"{source}-{path.parent.name}-{path.stem}-{result_index}"


def build_record(run, result, result_index, source, source_path, gpu_by_id):
    """Expand one checked result entry into a flat run record."""
    gpu = gpu_by_id[run["gpu_id"]]
    benchmark_type = run.get("benchmark_type", "game")
    system = run.get("system") or {}
    proof = run.get("proof") or {}
    raw_log = proof.get("raw_log")
    summary_source = proof.get("summary_source")
    gpu_power_w = checks.gpu_power_w(run)
    implementation_name = run.get(
        "device_name", run.get("implementation_name", system.get("device_name"))
    )
    record = {
        "id": run_id(source, source_path, result_index),
        "source": source,
        "gpu_id": run["gpu_id"],
        "gpu_name": catalog_name(gpu),
        "gpu_vendor": catalog_vendor(gpu),
        "form_factor": catalog_form_factor(gpu).title(),
        "vram_gb": catalog_vram_gb(gpu),
        "tdp_w": catalog_tdp_w(gpu),
        "benchmark_type": benchmark_type,
        "metrics": result,
        "game": run.get("game", ""),
        "game_version": str(run.get("version", "")),
        "resolution": result.get("resolution", ""),
        "graphics_preset": result.get("graphics_preset", ""),
        "upscaling": result.get("upscaling", run.get("upscaling", "")),
        "frame_generation": bool(result.get("frame_generation", run.get("frame_generation", False))),
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
        "submitted_by": str(run.get("submitted_by", "")),
        "synthetic": bool(run.get("synthetic", False)),
    }
    if benchmark_type == "game":
        record["avg_fps"] = round(float(result["avg_fps"]), 2)
        record["p1_low"] = round(float(result["p1_low"]), 2)
    return record


def source_records(runs, source, gpu_by_id):
    return [
        build_record(run, result, result_index, source, path, gpu_by_id)
        for path, run in runs[source]
        for result_index, result in enumerate(run["result"])
    ]


def aggregate_game_records(records, id_prefix):
    grouped = defaultdict(list)
    for record in records:
        if record["benchmark_type"] != "game":
            continue
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

    summaries = []
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
                    "submitted_by",
                )
                if run[key] not in ("", None)
            }
            for run in runs
        ]
        summaries.append(
            {
                **first,
                "id": f"{id_prefix}-{first['id']}",
                "run_count": len(runs),
                "avg_fps": round(sum(run["avg_fps"] for run in runs) / len(runs), 2),
                "p1_low": round(sum(run["p1_low"] for run in runs) / len(runs), 2),
                "avg_fps_range": [
                    min(run["avg_fps"] for run in runs),
                    max(run["avg_fps"] for run in runs),
                ],
                "p1_low_range": [
                    min(run["p1_low"] for run in runs),
                    max(run["p1_low"] for run in runs),
                ],
                "implementations": implementations,
                "contributors": sorted(
                    {run["submitted_by"] for run in runs if run["submitted_by"]},
                    key=str.lower,
                ),
            }
        )
    return summaries


def write_json(path, payload):
    destination = OUTPUT_DIR / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2)
        output.write("\n")


def gpu_summary(source, gpu, records, metadata):
    gpu_records = [record for record in records if record["gpu_id"] == gpu["id"]]
    summaries = aggregate_game_records(gpu_records, f"{source}-summary")
    return {
        "metadata": metadata,
        "gpu": gpu,
        "source": source,
        "run_count": len(gpu_records),
        "game_summary_count": len(summaries),
        "records": gpu_records,
        "game_summaries": summaries,
    }


def main(data_dir=DATA_DIR):
    gpus, catalog_issues = checks.load_catalog(data_dir)
    runs, result_issues = checks.load_results(gpus, data_dir)
    issues = checks.Issues([*catalog_issues, *result_issues])
    if checks.report(issues, "Checks (run validate.py for warnings)", show_warnings=False):
        print("Build stopped: fix the errors above; nothing was written to site/api.")
        return 1
    reviews_source = load_yaml(data_dir / "reviews.yaml")
    gpu_by_id = {gpu["id"]: gpu for gpu in gpus}
    official = source_records(runs, "official", gpu_by_id)
    community_raw = source_records(runs, "community", gpu_by_id)
    official_summaries = aggregate_game_records(official, "official-summary")
    community_summaries = aggregate_game_records(community_raw, "community-summary")
    dashboard_records = sorted(
        [*official_summaries, *community_summaries],
        key=lambda record: (
            record["game"],
            record["resolution"],
            record["source"],
            -record["avg_fps"],
        ),
    )
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "release_version": os.getenv("RELEASE_VERSION", RELEASE_VERSION),
        "commit": os.getenv("GITHUB_SHA", "local")[:12],
        "generated_at": datetime.now(UTC).isoformat(),
        "synthetic_data": any(record["synthetic"] for record in dashboard_records),
        "comparison_policy": {
            "group_by": [
                "gpu_id",
                "form_factor",
                "gpu_power_w",
                "game",
                "resolution",
                "graphics_preset",
            ],
            "game_version_is_not_a_grouping_key": True,
            "frame_generation": "off",
            "community_outlier_threshold": 0.5,
        },
    }

    official_by_gpu = {}
    community_by_gpu = {}
    for gpu in gpus:
        official_by_gpu[gpu["id"]] = gpu_summary("official", gpu, official, metadata)
        community_by_gpu[gpu["id"]] = gpu_summary("community", gpu, community_raw, metadata)
        write_json(
            Path("official") / gpu["id"] / "summary.json",
            official_by_gpu[gpu["id"]],
        )
        write_json(
            Path("community") / gpu["id"] / "summary.json",
            community_by_gpu[gpu["id"]],
        )

    master_gpus = [
        {
            **gpu,
            "links": {
                "official_summary": f"official/{gpu['id']}/summary.json",
                "community_summary": f"community/{gpu['id']}/summary.json",
            },
            "official": {
                "run_count": official_by_gpu[gpu["id"]]["run_count"],
                "game_summaries": official_by_gpu[gpu["id"]]["game_summaries"],
            },
            "community": {
                "run_count": community_by_gpu[gpu["id"]]["run_count"],
                "game_summaries": community_by_gpu[gpu["id"]]["game_summaries"],
            },
        }
        for gpu in gpus
    ]
    games = sorted({record["game"] for record in dashboard_records})
    resolutions = sorted(
        {record["resolution"] for record in dashboard_records},
        key=lambda value: (0, int(value.removesuffix("p")))
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

    write_json("gpus.json", {"metadata": metadata, "gpus": master_gpus})
    write_json("official.json", {"metadata": metadata, "records": official, "count": len(official)})
    write_json(
        "community.json",
        {
            "metadata": metadata,
            "records": community_summaries,
            "count": len(community_summaries),
            "raw_count": len(community_raw),
        },
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
        f"GPUs: {len(gpus)} | Official runs: {len(official)} | "
        f"Community runs: {len(community_raw)} | Dashboard summaries: "
        f"{len(dashboard_records)} | Output: {OUTPUT_DIR}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
