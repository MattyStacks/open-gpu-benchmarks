"""Regression checks for multi-profile result files and aggregation."""
import json
import subprocess
import sys
from pathlib import Path


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


def main():
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

    summary_1440p = find_summary(arc_a770["game_summaries"], "1440p")
    assert summary_1440p["run_count"] == 1
    assert summary_1440p["avg_fps"] == 60.0
    assert summary_1440p["p1_low"] == 42.3

    dashboard = load_json(API_DIR / "dashboard.json")
    assert len(dashboard["records"]) == 24
    print("Multi-profile result and matching-run aggregation checks passed")


if __name__ == "__main__":
    main()