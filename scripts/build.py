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
SCHEMA_VERSION = "0.1"


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

    proof = run.get("proof", {})
    raw_log = proof.get("raw_log")
    summary_source = proof.get("summary_source")
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
        "settings": run.get("settings"),
        "avg_fps": round(float(avg_fps), 2),
        "p1_low": round(float(p1_low), 2),
        "driver": str(run.get("system", {}).get("driver", run.get("driver", ""))),
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
    grouped = defaultdict(list)
    for record in records:
        grouped[
            (
                record["gpu_id"],
                record["game"],
                record["game_version"],
                record["resolution"],
                record["settings"],
            )
        ].append(record)

    averages = []
    for runs in grouped.values():
        first = runs[0]
        averages.append(
            {
                **first,
                "id": f"community-average-{first['id']}",
                "run_count": len(runs),
                "avg_fps": round(sum(run["avg_fps"] for run in runs) / len(runs), 2),
                "p1_low": round(sum(run["p1_low"] for run in runs) / len(runs), 2),
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
    gpu_by_id = {gpu["id"]: gpu for gpu in gpus}
    official = official_records(gpu_by_id)
    community_raw = community_records(gpu_by_id)
    community = community_averages(community_raw)
    dashboard_records = sorted(
        [*official, *community],
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
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "release_version": os.getenv("RELEASE_VERSION", "0.1.0"),
        "commit": os.getenv("GITHUB_SHA", "local")[:12],
        "generated_at": datetime.now(UTC).isoformat(),
        "synthetic_data": any(record["synthetic"] for record in dashboard_records),
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
            "records": dashboard_records,
        },
    )

    print(
        f"GPUs: {len(gpus)} | Official: {len(official)} | "
        f"Community summaries: {len(community)} | Output: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
