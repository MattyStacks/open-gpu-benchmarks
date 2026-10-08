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


def find_summary(summaries, resolution, os_name="windows"):
    return next(
        summary
        for summary in summaries
        if summary["game"] == "Helldivers 2"
        and summary["resolution"] == resolution
        and summary["graphics_preset"] == "Ultra"
        and summary["os"] == os_name
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


TEST_REF = "test_ref_8gb"
TEST_REF_PATH = f"gpus/reference/nvidia/{TEST_REF}.yaml"


def reference_entry(**overrides):
    entry = {
        "id": TEST_REF,
        "identity": {"name": "Test Reference", "gpu_vendor": "nvidia"},
        "silicon": {"shader_cores": 1024},
        "memory": {"capacity_gb": 8, "type": "GDDR6"},
        "clocks": {"base_mhz": 1500, "boost_mhz": 2000},
        "features": {"outputs": ["HDMI 2.1"]},
    }
    entry.update(overrides)
    return entry


def result_run(**overrides):
    run = {
        "gpu_id": TEST_ID,
        "game": "Test Game",
        "result": [{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 100, "p1_low": 80}],
        "system": {"os": "windows"},
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
        "base-unknown": {base: minimal_entry(base="missing_ref")},
        "base-mismatch": {
            f"gpus/reference/amd/{TEST_REF}.yaml": reference_entry(identity={"name": "Test Reference", "gpu_vendor": "amd"}),
            base: minimal_entry(base=TEST_REF),
        },
        "reference-field": {TEST_REF_PATH: reference_entry(classification={"form_factor": "desktop"})},
        "field-not-allowed": {base: minimal_entry(platform={"oem": "Test"})},
    }
    source = {"url": "https://example.com/specs", "title": "Test", "accessed": "2026-10-08", "covers": ["memory"]}
    bad_sources = {
        "not a list": "https://example.com",
        "http url": [{**source, "url": "http://example.com/specs"}],
        "missing url": [{key: value for key, value in source.items() if key != "url"}],
        "unknown key": [{**source, "link": "x"}],
        "unknown section": [{**source, "covers": ["vram"]}],
        "accessed not a date": [{**source, "accessed": "October 2026"}],
    }
    for label, sources in bad_sources.items():
        cases[f"source-invalid ({label})"] = {base: minimal_entry(sources=sources)}
    cases["source-invalid (unquoted accessed)"] = {
        base: dump(minimal_entry()) + "sources:\n  - url: https://example.com/specs\n    accessed: 2026-10-08\n"
    }
    cases["source-invalid (msrp source)"] = {
        base: minimal_entry(release={"msrp_history": [{"date": "2024-01", "price_usd": 1, "source": "ftp://x"}]})
    }
    for rule, files in cases.items():
        expect_rule(rule.split(" (")[0], files)
    # A file without sources passes with a warning; a valid sources list passes cleanly.
    expect_rule("sources-missing", {base: minimal_entry()}, level="warning")
    issues = run_checks({base: minimal_entry(sources=[source])})
    assert not issues, [issue.format() for issue in issues]

    # Handheld ids end with the RAM size; a handheld id with a suffix is rejected.
    handheld = minimal_entry(id="test_device_16gb_x", classification={"form_factor": "handheld"}, memory={"capacity_gb": 16})
    expect_rule("id-format", {"gpus/handheld/nvidia/test_device_16gb_x.yaml": handheld})
    # A handheld's platform power range must run low to high.
    handheld = minimal_entry(
        id="test_device_16gb",
        classification={"form_factor": "handheld"},
        memory={"capacity_gb": 16},
        platform={"power_min_w": 30, "power_max_w": 9},
    )
    expect_rule("field-range", {"gpus/handheld/nvidia/test_device_16gb.yaml": handheld})
    # A reference in the wrong vendor folder, and board_partner on a laptop.
    expect_rule("catalog-folder", {f"gpus/reference/amd/{TEST_REF}.yaml": reference_entry()})
    laptop_partner = minimal_entry(
        id="test_gpu_laptop_8gb_test_model",
        classification={"form_factor": "laptop"},
        identity={"name": "Test", "gpu_vendor": "nvidia", "board_partner": "Test"},
    )
    expect_rule("field-not-allowed", {"gpus/laptop/nvidia/test_gpu_laptop_8gb_test_model.yaml": laptop_partner})
    # _generic is a warning, not an error, on a laptop.
    laptop = minimal_entry(id="test_gpu_laptop_8gb_generic", classification={"form_factor": "laptop"})
    issues = run_checks({"gpus/laptop/nvidia/test_gpu_laptop_8gb_generic.yaml": laptop})
    assert not issues.errors and {issue.rule for issue in issues.warnings} == {"id-generic", "sources-missing"}, issues


def check_result_rules():
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    folder = f"community/{TEST_ID}"
    no_result = {key: value for key, value in community_run().items() if key != "result"}
    no_avg = community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "p1_low": 80}])
    impossible = community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 60, "p1_low": 80}])
    no_submitter = {key: value for key, value in community_run().items() if key != "submitted_by"}
    cases = {
        "result-folder": {"community/other_gpu_8gb_fe/result_20261003_test_tester.yaml": community_run()},
        "result-reference-id": {
            TEST_REF_PATH: reference_entry(),
            f"community/{TEST_REF}/result_20261003_test_tester.yaml": community_run(gpu_id=TEST_REF),
        },
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
    no_os = {key: value for key, value in community_run().items() if key != "system"}
    os_cases = {
        "result-os (missing)": no_os,
        "result-os (capitalized)": community_run(system={"os": "Windows"}),
        "result-os (free text)": community_run(system={"os": "Windows 11"}),
        "result-os (macos)": community_run(system={"os": "macos"}),
        "result-os (top level)": {**no_os, "os": "windows"},
        "result-os-field (proton on windows)": community_run(system={"os": "windows", "proton": "GE-Proton9-20"}),
        "result-os-field (game_mode on linux)": community_run(system={"os": "linux", "game_mode": True}),
        "result-os-field (bool as text)": community_run(system={"os": "windows", "hags": "yes"}),
        "result-os-field (number as text)": community_run(system={"os": "linux", "kernel": 6.8}),
        "result-os-field (runtime)": community_run(system={"os": "linux", "runtime": "steam"}),
    }
    for label, run in os_cases.items():
        cases[label] = {COMMUNITY_PATH: run}
    for rule, files in cases.items():
        expect_rule(rule.split(" (")[0], {**catalog, **files})
    expect_rule("result-system-field", {**catalog, COMMUNITY_PATH: community_run(system={"os": "linux", "kernal": "6.8"})}, level="warning")
    # A full Linux run passes; a Linux community run is never outlier-checked against Windows numbers.
    linux = {
        "os": "linux", "distro": "Bazzite", "kernel": "6.9.12", "mesa": "24.1.5", "runtime": "proton",
        "proton": "GE-Proton9-20", "gamemode": True, "resizable_bar": True,
    }
    slow_linux = community_run(system=linux, result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 10, "p1_low": 8}])
    issues = run_checks({**catalog, f"official/{TEST_ID}/result_20261003_test.yaml": result_run(), COMMUNITY_PATH: slow_linux})
    assert not issues.errors, [issue.format() for issue in issues.errors]
    assert "result-no-baseline" in {issue.rule for issue in issues.warnings}


def check_os_grouping():
    """Windows and Linux runs of the same profile build separate summaries."""
    gpu = minimal_entry()
    windows, linux = result_run(), result_run(system={"os": "linux", "distro": "CachyOS"})
    windows["result"][0]["avg_fps"], linux["result"][0]["avg_fps"] = 100, 90
    records = [
        build.build_record(run, run["result"][0], 0, "official", Path(f"official/{TEST_ID}/result_{name}.yaml"), {TEST_ID: gpu})
        for name, run in (("windows", windows), ("linux", linux))
    ]
    summaries = build.aggregate_game_records(records, "official-summary")
    assert sorted((summary["os"], summary["run_count"], summary["avg_fps"]) for summary in summaries) == [
        ("linux", 1, 90.0), ("windows", 1, 100.0),
    ], summaries
    linux_summary = next(summary for summary in summaries if summary["os"] == "linux")
    assert linux_summary["distro"] == "CachyOS" and linux_summary["implementations"][0]["distro"] == "CachyOS"


def check_parse_mangohud():
    """MangoHud logs with the os/kernel/driver preamble parse to real FPS, not 0."""
    import parse

    text = (
        "os,cpu,gpu,ram,kernel,driver,cpuscheduler\n"
        "SteamOS,AMD APU,AMD GPU,16GB,6.5.0-valve22,Mesa 24.1.0,performance\n"
        "fps,frametime,cpu_load\n60,20.0,30\n60,20.0,30\n60,25.0,30\n"
    )
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "mangohud.csv"
        path.write_text(text, encoding="utf-8")
        result = parse.detect_and_load(path)
    assert result["format"] == "mangohud" and result["frame_count"] == 3, result
    assert round(result["avg"], 2) == 46.67, result
    assert result["kernel"] == "6.5.0-valve22" and result["driver"] == "Mesa 24.1.0", result


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


def check_base_merge():
    shared = {"url": "https://example.com/shared", "covers": ["release"]}
    product = minimal_entry(
        base=TEST_REF,
        clocks={"boost_mhz": 2100},
        features={"outputs": ["DP 2.1"]},
        sources=[{"url": "https://example.com/board", "covers": ["power"]}, shared],
    )
    reference = reference_entry(sources=[{**shared, "covers": ["silicon"]}, {"url": "https://example.com/chip"}])
    with tempfile.TemporaryDirectory() as temp:
        data_dir = Path(temp)
        for relative, content in {TEST_REF_PATH: reference, TEST_CATALOG_PATH: product}.items():
            (data_dir / relative).parent.mkdir(parents=True, exist_ok=True)
            (data_dir / relative).write_text(dump(content), encoding="utf-8")
        catalog, issues = checks.load_catalog(data_dir)
    assert not issues.errors, [issue.format() for issue in issues.errors]
    assert [entry["id"] for entry in catalog] == [TEST_ID], "reference files are not products"
    merged = catalog[0]
    assert merged["base"] == TEST_REF
    assert merged["silicon"]["shader_cores"] == 1024, "inherited from the reference"
    assert merged["clocks"] == {"base_mhz": 1500, "boost_mhz": 2100}, "product value wins, siblings kept"
    assert merged["features"]["outputs"] == ["DP 2.1"], "lists are replaced whole"
    assert merged["identity"]["name"] == "Test GPU"
    assert [source["url"] for source in merged["sources"]] == [
        "https://example.com/board", "https://example.com/shared", "https://example.com/chip",
    ], "sources add up, product first, each URL once"
    assert merged["sources"][1]["covers"] == ["release", "silicon"], "covers combine for a shared URL"


def check_templates_are_valid():
    """Each catalog template passes the checks alongside the real reference files."""
    references = {
        path.relative_to(ROOT / "data").as_posix(): path.read_text(encoding="utf-8")
        for path in (ROOT / "data" / "gpus" / "reference").rglob("*.yaml")
    }
    for template in sorted((ROOT / "templates").glob("catalog_*.yaml")):
        text = template.read_text(encoding="utf-8")
        entry = yaml.safe_load(text)
        vendor = entry["identity"]["gpu_vendor"]
        folder = "reference" if template.stem == "catalog_reference" else entry["classification"]["form_factor"]
        issues = run_checks({**references, f"gpus/{folder}/{vendor}/{entry['id']}.yaml": text})
        assert not issues.errors, (template.name, [issue.format() for issue in issues.errors])

    # The community template passes the result checks once the placeholder username is filled in.
    catalog = {
        path.relative_to(ROOT / "data").as_posix(): path.read_text(encoding="utf-8")
        for path in (ROOT / "data" / "gpus").rglob("*.yaml")
    }
    text = (ROOT / "templates" / "community_submission.yaml").read_text(encoding="utf-8")
    text = text.replace("your-github-username", "tester")
    gpu_id = yaml.safe_load(text)["gpu_id"]
    issues = run_checks({**catalog, f"community/{gpu_id}/result_20261003_cyberpunk_tester.yaml": text})
    assert not issues.errors, ("community_submission.yaml", [issue.format() for issue in issues.errors])


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
    assert master["metadata"]["schema_version"] == build.SCHEMA_VERSION == "0.10"
    assert "os" in master["metadata"]["comparison_policy"]["group_by"]
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
    assert flagship["base"] == "rtx_4090_24gb" and flagship["identity"]["board_partner"] == "NVIDIA"
    assert "rtx_4090_24gb" not in by_id, "reference files never appear as catalog products"
    ally = by_id["rog_ally_z1_extreme_16gb"]
    assert ally["base"] == "z1_extreme" and ally["silicon"]["shader_cores"] == 768
    assert ally["memory"]["shared"] is True and ally["memory"]["type"] == "LPDDR5"
    assert ally["platform"]["ram_mts"] == 6400 and ally["platform"]["oem"] == "ASUS"
    deck = by_id["steam_deck_oled_16gb"]
    assert deck["memory"]["shared"] is True
    assert deck["memory"]["capacity_gb"] == 16
    assert "base" not in deck, "base is optional"
    for gpu in master["gpus"]:
        assert gpu.get("sources"), f"{gpu['id']} has no sources"
        assert all(source["url"].startswith("https://") for source in gpu["sources"])
    flagship_sources = by_id["rtx_4090_24gb_fe"]["sources"]
    assert len(flagship_sources) == 1 and "silicon" in flagship_sources[0]["covers"] and "release" in flagship_sources[0]["covers"]
    assert by_id["arc_a770m_16gb_generic"].get("release", {}).get("date") is None

    arc_a770 = load_json(API_DIR / "community" / "arc_a770_16gb_le" / "summary.json")
    assert arc_a770["records"]
    assert all(record["vram_gb"] == 16 and record["tdp_w"] == 225 for record in arc_a770["records"])
    assert all(record["gpu_vendor"] == "intel" for record in arc_a770["records"])

    dashboard = load_json(API_DIR / "dashboard.json")
    deck_records = [record for record in dashboard["records"] if record["gpu_id"] == "steam_deck_oled_16gb"]
    assert deck_records, "expected dashboard records for steam_deck_oled_16gb"
    assert all(record["vram_gb"] is None and record["tdp_w"] == 15 for record in deck_records)
    assert all(record["os"] == "linux" and record["distro"] == "SteamOS" for record in deck_records)
    assert all(record["os"] in checks.RESULT_OSES for record in dashboard["records"])
    xtx_alan_wake = [
        record for record in dashboard["records"]
        if record["gpu_id"] == "rx_7900_xtx_24gb_reference" and record["game"] == "Alan Wake 2"
    ]
    assert sorted(record["os"] for record in xtx_alan_wake) == ["linux", "windows"], "one summary per OS"


def main():
    check_valid_fixtures()
    check_catalog_rules()
    check_result_rules()
    check_os_grouping()
    check_parse_mangohud()
    check_reports_every_error_and_build_stops()
    check_minimal_entry_builds()
    check_base_merge()
    check_rules_are_documented()
    check_templates_are_valid()
    subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, check=True)
    arc_a770 = load_json(API_DIR / "community" / "arc_a770_16gb_le" / "summary.json")
    assert arc_a770["run_count"] == 4
    assert arc_a770["game_summary_count"] == 3

    summary_1080p = find_summary(arc_a770["game_summaries"], "1080p")
    assert summary_1080p["run_count"] == 2
    assert summary_1080p["avg_fps"] == 71.0
    assert summary_1080p["p1_low"] == 51.0
    assert summary_1080p["avg_fps_range"] == [70.0, 72.0]
    assert summary_1080p["p1_low_range"] == [50.0, 52.0]
    assert summary_1080p["contributors"] == ["MattyStacks"]
    assert all(record["submitted_by"] for record in arc_a770["records"])

    linux_1080p = find_summary(arc_a770["game_summaries"], "1080p", "linux")
    assert linux_1080p["run_count"] == 1 and linux_1080p["avg_fps"] == 63.0, "Linux runs never average with Windows"
    assert linux_1080p["distro"] == "Fedora"

    summary_1440p = find_summary(arc_a770["game_summaries"], "1440p")
    assert summary_1440p["run_count"] == 1
    assert summary_1440p["avg_fps"] == 60.0
    assert summary_1440p["p1_low"] == 42.3

    dashboard = load_json(API_DIR / "dashboard.json")
    assert len(dashboard["records"]) == 30
    check_catalog_specs()
    print("Catalog rules, result rules, aggregation, submitter, and catalog spec checks passed")


if __name__ == "__main__":
    main()
