"""Regression checks for the catalog, result checks, and aggregation."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

import build
import checks


ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "site" / "api" / "v1"
TEST_ID = "test_gpu_8gb_fe"
TEST_CATALOG_PATH = f"gpus/desktop/nvidia/{TEST_ID}.yaml"


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


def minimal_entry(**overrides):
    entry = {
        "id": TEST_ID,
        "identity": {"name": "Test GPU", "gpu_vendor": "nvidia"},
        "classification": {"form_factor": "desktop"},
        "memory": {"capacity_gb": 8},
    }
    entry.update(overrides)
    return entry


def result_run(**overrides):
    run = {
        "gpu_id": TEST_ID,
        "game": "Test Game",
        "result": [{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 100, "p1_low": 80}],
    }
    run.update(overrides)
    return run


def community_run(**overrides):
    return result_run(submitted_by="tester", **overrides)


COMMUNITY_PATH = f"community/{TEST_ID}/result_20261003_test_tester.yaml"


def dump(value):
    return value if isinstance(value, str) else yaml.safe_dump(value, sort_keys=False)


def run_checks(files):
    """Write {relative path: data or text} into a temp data dir and run every check."""
    with tempfile.TemporaryDirectory() as temp:
        data_dir = Path(temp)
        for relative, content in files.items():
            path = data_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(dump(content), encoding="utf-8")
        catalog, issues = checks.load_catalog(data_dir)
        _, result_issues = checks.load_results(catalog, data_dir)
        return checks.Issues([*issues, *result_issues])


def expect_rule(rule, files, level="error"):
    issues = run_checks(files)
    found = {issue.rule for issue in issues if issue.level == level}
    assert rule in found, f"expected {level} '{rule}', got {[issue.format() for issue in issues]}"


def check_valid_fixtures():
    issues = run_checks({TEST_CATALOG_PATH: minimal_entry(), COMMUNITY_PATH: community_run()})
    assert not issues.errors, [issue.format() for issue in issues.errors]


def check_catalog_rules():
    base = TEST_CATALOG_PATH
    renamed = minimal_entry(identity={"name": "Test GPU", "vendor": "nvidia"})
    cases = {
        "catalog-empty": {},
        "yaml-invalid": {base: "id: test\nidentity:\n  name: 'unterminated\n"},
        "yaml-inline": {base: dump(minimal_entry()) + "power:\n  connectors: [8-pin]\n"},
        "catalog-not-mapping": {base: "- id: test_gpu_8gb_fe\n"},
        "catalog-folder": {f"gpus/desktop/amd/{TEST_ID}.yaml": minimal_entry()},
        "id-filename": {"gpus/desktop/nvidia/other.yaml": minimal_entry()},
        "id-duplicate": {base: minimal_entry(), f"gpus/laptop/nvidia/{TEST_ID}.yaml": minimal_entry()},
        "id-format": {"gpus/desktop/nvidia/Test_GPU_8gb_fe.yaml": minimal_entry(id="Test_GPU_8gb_fe")},
        "id-memory-token": {"gpus/desktop/nvidia/test_gpu_16gb_fe.yaml": minimal_entry(id="test_gpu_16gb_fe")},
        "id-generic": {"gpus/desktop/nvidia/test_gpu_8gb_generic.yaml": minimal_entry(id="test_gpu_8gb_generic")},
        "field-required": {base: {key: value for key, value in minimal_entry().items() if key != "identity"}},
        "field-renamed": {base: renamed},
        "field-unknown": {base: minimal_entry(colour="red")},
        "field-type": {base: dump(minimal_entry()) + "release:\n  date: 2022-10-12\n"},
        "field-value": {base: minimal_entry(classification={"form_factor": "tablet"})},
        "field-range": {base: minimal_entry(power={"tdp_w": 700})},
    }
    for rule, files in cases.items():
        expect_rule(rule, files)

    # Handheld ids end with the RAM size; a handheld id with a suffix is rejected.
    handheld = minimal_entry(id="test_device_16gb_x", classification={"form_factor": "handheld"}, memory={"capacity_gb": 16})
    expect_rule("id-format", {"gpus/handheld/nvidia/test_device_16gb_x.yaml": handheld})
    # _generic is a warning, not an error, on a laptop.
    laptop = minimal_entry(id="test_gpu_laptop_8gb_generic", classification={"form_factor": "laptop"})
    issues = run_checks({"gpus/laptop/nvidia/test_gpu_laptop_8gb_generic.yaml": laptop})
    assert not issues.errors and {issue.rule for issue in issues.warnings} == {"id-generic"}, issues


def check_result_rules():
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    folder = f"community/{TEST_ID}"
    no_result = {key: value for key, value in community_run().items() if key != "result"}
    no_avg = community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "p1_low": 80}])
    impossible = community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 60, "p1_low": 80}])
    no_submitter = {key: value for key, value in community_run().items() if key != "submitted_by"}
    cases = {
        "result-folder": {"community/other_gpu_8gb_fe/result_20261003_test_tester.yaml": community_run()},
        "result-unknown-gpu": {"community/missing_8gb_fe/result_20261003_test_tester.yaml": community_run(gpu_id="missing_8gb_fe")},
        "result-not-mapping": {COMMUNITY_PATH: "- gpu_id: test\n"},
        "result-list": {COMMUNITY_PATH: no_result},
        "result-field": {COMMUNITY_PATH: no_avg},
        "result-impossible": {COMMUNITY_PATH: impossible},
        "result-frame-generation": {COMMUNITY_PATH: community_run(frame_generation=True)},
        "result-form-factor": {COMMUNITY_PATH: community_run(form_factor="laptop")},
        "result-filename": {f"{folder}/cyberpunk.yaml": community_run()},
        "community-submitter": {COMMUNITY_PATH: no_submitter},
        "community-filename": {f"{folder}/result_20261003_test_someone_else.yaml": community_run()},
        "community-outlier": {
            f"official/{TEST_ID}/result_20261003_test.yaml": result_run(),
            COMMUNITY_PATH: community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 10, "p1_low": 8}]),
        },
    }
    for rule, files in cases.items():
        expect_rule(rule, {**catalog, **files})


def check_reports_every_error_and_build_stops():
    files = {
        "gpus/desktop/amd/test_gpu_8gb_fe.yaml": minimal_entry(),
        "gpus/desktop/nvidia/second_gpu_8gb_fe.yaml": minimal_entry(id="second_gpu_8gb_fe", power={"tdp_w": 9000}),
    }
    issues = run_checks(files)
    assert {issue.path.rsplit("/", 1)[-1] for issue in issues.errors} == {
        "test_gpu_8gb_fe.yaml",
        "second_gpu_8gb_fe.yaml",
    }, [issue.format() for issue in issues]

    with tempfile.TemporaryDirectory() as temp:
        data_dir, output_dir = Path(temp) / "data", Path(temp) / "api"
        for relative, content in files.items():
            (data_dir / relative).parent.mkdir(parents=True, exist_ok=True)
            (data_dir / relative).write_text(dump(content), encoding="utf-8")
        original_output = build.OUTPUT_DIR
        build.OUTPUT_DIR = output_dir
        try:
            assert build.main(data_dir) == 1
        finally:
            build.OUTPUT_DIR = original_output
        assert not output_dir.exists(), "build must not write output when checks fail"


def check_minimal_entry_builds():
    gpu = minimal_entry()
    run = result_run()
    record = build.build_record(run, run["result"][0], 0, "official", Path(f"official/{TEST_ID}/result_x.yaml"), {TEST_ID: gpu})
    assert record["tdp_w"] is None and record["vram_gb"] == 8 and record["gpu_vendor"] == "nvidia"


def check_templates_are_valid():
    for template in sorted((ROOT / "templates").glob("catalog_*.yaml")):
        entry = yaml.safe_load(template.read_text(encoding="utf-8"))
        form, vendor = entry["classification"]["form_factor"], entry["identity"]["gpu_vendor"]
        issues = run_checks({f"gpus/{form}/{vendor}/{entry['id']}.yaml": template.read_text(encoding="utf-8")})
        assert not issues.errors, (template.name, [issue.format() for issue in issues.errors])


def check_rules_are_documented():
    """Every rule name in checks.py must be a heading in the matching doc."""
    source = (ROOT / "scripts" / "checks.py").read_text(encoding="utf-8")
    rules = set(re.findall(r'issues\.(?:error|warning)\(\s*[\w\[\]]+,\s*"([a-z-]+)"', source))
    assert len(rules) > 20, rules
    for rule in rules:
        doc = checks.RESULTS_DOC if rule.startswith(("result-", "community-")) else checks.CATALOG_DOC
        text = (ROOT / doc).read_text(encoding="utf-8")
        assert f"#### `{rule}`" in text, f"rule '{rule}' needs a '#### `{rule}`' heading in {doc}"


def check_catalog_specs():
    master = load_json(API_DIR / "gpus.json")
    assert master["metadata"]["schema_version"] == "0.7"
    by_id = {gpu["id"]: gpu for gpu in master["gpus"]}
    assert len(by_id) == 11
    for gpu in master["gpus"]:
        for section in ("identity", "classification", "memory"):
            assert section in gpu, (gpu["id"], section)
        assert "vendor" not in gpu["identity"] and gpu["identity"]["gpu_vendor"] in checks.GPU_VENDORS
    flagship = by_id["rtx_4090_24gb_fe"]
    assert flagship["silicon"]["shader_cores"] == 16384
    assert flagship["memory"]["bandwidth_gbs"] == 1008
    assert flagship["release"]["msrp_usd"] == 1599
    deck = by_id["steam_deck_oled_16gb"]
    assert deck["memory"]["shared"] is True
    assert deck["memory"]["capacity_gb"] == 16
    assert by_id["arc_a770m_16gb_generic"].get("release", {}).get("date") is None

    arc_a770 = load_json(API_DIR / "community" / "arc_a770_16gb_le" / "summary.json")
    assert arc_a770["records"]
    assert all(record["vram_gb"] == 16 and record["tdp_w"] == 225 for record in arc_a770["records"])
    assert all(record["gpu_vendor"] == "intel" for record in arc_a770["records"])

    dashboard = load_json(API_DIR / "dashboard.json")
    deck_records = [record for record in dashboard["records"] if record["gpu_id"] == "steam_deck_oled_16gb"]
    assert deck_records, "expected dashboard records for steam_deck_oled_16gb"
    assert all(record["vram_gb"] is None and record["tdp_w"] == 15 for record in deck_records)


def main():
    check_valid_fixtures()
    check_catalog_rules()
    check_result_rules()
    check_reports_every_error_and_build_stops()
    check_minimal_entry_builds()
    check_rules_are_documented()
    check_templates_are_valid()
    subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, check=True)
    arc_a770 = load_json(API_DIR / "community" / "arc_a770_16gb_le" / "summary.json")
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
    print("Catalog rules, result rules, aggregation, submitter, and catalog spec checks passed")


if __name__ == "__main__":
    main()
