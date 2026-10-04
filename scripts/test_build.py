"""Regression checks for multi-profile result files and aggregation."""
import json
import subprocess
import sys
from pathlib import Path

from validate import gpu_catalog, validate_file


ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "site" / "api" / "v1"


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def find_summary(summaries, resolution):
    return next(
        summary
        for summary in summaries
        if summary["game"] == "Helldivers 2"
        and summary["resolution"] == resolution
        and summary["graphics_preset"] == "Ultra"
    )


def check_submitter_validation():
    catalog = gpu_catalog()
    folder = ROOT / "data" / "community" / "arc_a770"
    data = {
        "gpu_id": "arc_a770",
        "submitted_by": "MattyStacks",
        "game": "Helldivers 2",
        "result": [{"resolution": "1080p", "graphics_preset": "Ultra", "avg_fps": 70, "p1_low": 50}],
        "proof": {"summary_source": "test"},
    }
    errors, _, _ = validate_file(folder / "result_20261003_helldivers_mattystacks.yaml", data, catalog)
    assert not errors, errors
    errors, _, _ = validate_file(folder / "result_20261003_helldivers_arc_a770.yaml", data, catalog)
    assert any("file name" in error for error in errors), errors
    missing = {key: value for key, value in data.items() if key != "submitted_by"}
    errors, _, _ = validate_file(folder / "result_20261003_helldivers_mattystacks.yaml", missing, catalog)
    assert any("missing submitted_by" in error for error in errors), errors


def main():
    check_submitter_validation()
    subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, check=True)
    arc_a770 = load_json(API_DIR / "community" / "arc_a770" / "summary.json")
    assert arc_a770["run_count"] == 3
    assert arc_a770["game_summary_count"] == 2

    summary_1080p = find_summary(arc_a770["game_summaries"], "1080p")
    assert summary_1080p["run_count"] == 2
    assert summary_1080p["avg_fps"] == 71.0
    assert summary_1080p["p1_low"] == 51.0
    assert summary_1080p["avg_fps_range"] == [70.0, 72.0]
    assert summary_1080p["p1_low_range"] == [50.0, 52.0]
    assert summary_1080p["contributors"] == ["MattyStacks"]
    assert all(record["submitted_by"] for record in arc_a770["records"])

    summary_1440p = find_summary(arc_a770["game_summaries"], "1440p")
    assert summary_1440p["run_count"] == 1
    assert summary_1440p["avg_fps"] == 60.0
    assert summary_1440p["p1_low"] == 42.3

    dashboard = load_json(API_DIR / "dashboard.json")
    assert len(dashboard["records"]) == 24
    print("Multi-profile result, matching-run aggregation, and submitter checks passed")


if __name__ == "__main__":
    main()