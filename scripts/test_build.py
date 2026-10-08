"""Regression checks for multi-profile result files and aggregation."""
import copy
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from build import validate_gpu_catalog
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


def valid_gpu_entry():
    return {
        "id": "test_gpu",
        "identity": {"name": "Test GPU", "codename": "T100", "vendor": "nvidia"},
        "classification": {"form_factor": "desktop", "architecture": "Test Arch"},
        "memory": {
            "capacity_gb": 8,
            "type": "GDDR6",
            "bus_width_bits": 128,
            "bandwidth_gbs": 256,
        },
        "clocks": {"boost_mhz": 2000},
        "power": {"tdp_w": 150},
    }


def check_catalog_validation():
    assert validate_gpu_catalog([valid_gpu_entry()])

    def expect_error(mutator, fragment):
        entry = valid_gpu_entry()
        mutator(entry)
        try:
            validate_gpu_catalog([entry])
        except ValueError as error:
            assert fragment in str(error), str(error)
        else:
            raise AssertionError(f"expected a '{fragment}' validation error")

    expect_error(lambda entry: entry["clocks"].pop("boost_mhz"), "clocks.boost_mhz")
    expect_error(lambda entry: entry["identity"].update(vendor="via"), "vendor 'via'")
    expect_error(lambda entry: entry["power"].update(tdp_w=700), "tdp_w 700")
    expect_error(lambda entry: entry["memory"].update(bus_width_bits=16), "bus_width_bits 16")
    expect_error(
        lambda entry: entry.update(release={"date": date(2022, 1, 1)}),
        "quote it",
    )
    expect_error(
        lambda entry: entry.update(release={"msrp_history": [{"date": "2022-01"}]}),
        "msrp_history",
    )
    try:
        validate_gpu_catalog([valid_gpu_entry(), valid_gpu_entry()])
    except ValueError as error:
        assert "duplicate gpu id" in str(error), str(error)
    else:
        raise AssertionError("expected a duplicate gpu id validation error")


def check_catalog_specs():
    master = load_json(API_DIR / "gpus.json")
    assert master["metadata"]["schema_version"] == "0.6"
    by_id = {gpu["id"]: gpu for gpu in master["gpus"]}
    assert len(by_id) == 11
    for gpu in master["gpus"]:
        for section in ("identity", "classification", "memory", "clocks", "power"):
            assert section in gpu, (gpu["id"], section)
    flagship = by_id["rtx_4090"]
    assert flagship["silicon"]["shader_cores"] == 16384
    assert flagship["memory"]["bandwidth_gbs"] == 1008
    assert flagship["release"]["msrp_usd"] == 1599
    deck = by_id["steam_deck_oled"]
    assert deck["memory"]["shared"] is True
    assert deck["memory"]["capacity_gb"] == 16
    assert by_id["arc_a770m"].get("release", {}).get("date") is None

    arc_a770 = load_json(API_DIR / "community" / "arc_a770" / "summary.json")
    assert arc_a770["records"]
    assert all(record["vram_gb"] == 16 and record["tdp_w"] == 225 for record in arc_a770["records"])

    dashboard = load_json(API_DIR / "dashboard.json")
    deck_records = [record for record in dashboard["records"] if record["gpu_id"] == "steam_deck_oled"]
    assert deck_records, "expected dashboard records for steam_deck_oled"
    assert all(record["vram_gb"] is None and record["tdp_w"] == 15 for record in deck_records)


def main():
    check_submitter_validation()
    check_catalog_validation()
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
    check_catalog_specs()
    print("Multi-profile result, matching-run aggregation, submitter, and catalog spec checks passed")


if __name__ == "__main__":
    main()