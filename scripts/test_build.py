"""Regression checks for the catalog, result checks, and aggregation."""
import contextlib
import io
import json
import re
import tempfile
from pathlib import Path

import yaml

import build
import checks


ROOT = Path(__file__).resolve().parent.parent
# The synthetic runs live here, never in data/; they build into a temp folder so
# nothing synthetic reaches site/api (build.yml deploys site/ after this test).
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "data"
TEST_ID = "test_gpu_8gb_fe"
TEST_CATALOG_PATH = f"gpus/desktop/nvidia/{TEST_ID}.yaml"
GAMES_PATH = "games.yaml"
# The registry run_checks writes unless a case brings its own games.yaml.
TEST_GAMES = {
    "games": [
        {"id": "test_game", "name": "Test Game", "type": "game", "year": 2024},
        {"id": "test_synthetic", "name": "Test Synthetic", "type": "synthetic", "year": 2024},
    ]
}


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def find_summary(summaries, resolution, os_name="windows"):
    return next(
        summary
        for summary in summaries
        if summary["game_id"] == "helldivers_2"
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
        "game_id": "test_game",
        # Matches the 20261003 in every test file name below.
        "date": "2026-10-03",
        "result": [{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 100, "p1_low": 80}],
        "system": {"os": "windows"},
        "proof": {"method": "presentmon"},
    }
    run.update(overrides)
    return run


def community_run(**overrides):
    """An anonymous community run: no submitted_by, and no username in the file name."""
    return result_run(**overrides)


COMMUNITY_PATH = f"community/{TEST_ID}/result_20261003_test.yaml"


def dump(value):
    return value if isinstance(value, str) else yaml.safe_dump(value, sort_keys=False)


def run_checks(files):
    """Write {relative path: data or text} into a temp data dir and run every check.
    A games.yaml with test_game and test_synthetic is added unless files has one."""
    with tempfile.TemporaryDirectory() as temp:
        data_dir = Path(temp)
        for relative, content in {GAMES_PATH: TEST_GAMES, **files}.items():
            path = data_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(dump(content), encoding="utf-8")
        catalog, issues = checks.load_catalog(data_dir)
        games, game_issues = checks.load_games(data_dir)
        _, result_issues = checks.load_results(catalog, data_dir, games)
        return checks.Issues([*issues, *game_issues, *result_issues])


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
        "community-submitter": {COMMUNITY_PATH: community_run(submitted_by="not a username")},
        "community-filename": {f"{folder}/result_test.yaml": community_run()},
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
        "result-system-memory (text size)": community_run(system={"os": "windows", "memory_gb": "32 GB"}),
        "result-system-memory (bool size)": community_run(system={"os": "windows", "memory_gb": True}),
        "result-system-memory (zero size)": community_run(system={"os": "windows", "memory_gb": 0}),
        "result-system-memory (huge size)": community_run(system={"os": "windows", "memory_gb": checks.MAX_MEMORY_GB + 1}),
        "result-system-memory (old memory key)": community_run(system={"os": "windows", "memory": "32 GB DDR5"}),
        "result-system-memory (old ram key)": community_run(system={"os": "windows", "ram": 32}),
        "result-system-memory (zero channels)": community_run(system={"os": "windows", "memory_channels": 0}),
        "result-system-memory (word channels)": community_run(system={"os": "windows", "memory_channels": "dual"}),
        "result-system-memory (fraction channels)": community_run(system={"os": "windows", "memory_channels": 2.5}),
        "result-system-memory (too many channels)": community_run(system={"os": "windows", "memory_channels": 64}),
        "result-system-memory (number type)": community_run(system={"os": "windows", "memory_type": 6400}),
    }
    for label, run in os_cases.items():
        cases[label] = {COMMUNITY_PATH: run}
    no_date = {key: value for key, value in community_run().items() if key != "date"}
    timed = lambda time: community_run(result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 100, "p1_low": 80, "time": time}])
    date_cases = {
        "result-date (missing)": no_date,
        "result-date (unquoted)": dump(no_date) + "date: 2026-10-03\n",
        "result-date (format)": community_run(date="10/03/2026"),
        "result-date (not a day)": community_run(date="2026-02-30"),
        "result-date (future)": community_run(date="2999-01-01"),
        "result-date-filename": community_run(date="2026-10-04"),
        "result-time (unquoted)": dump(community_run()).replace("p1_low: 80\n", "p1_low: 80\n  time: 14:30\n"),
        "result-time (out of range)": timed("25:00"),
        "result-time (one-digit hour)": timed("9:05"),
    }
    for label, run in date_cases.items():
        cases[label] = {COMMUNITY_PATH: run}
    for rule, files in cases.items():
        expect_rule(rule.split(" (")[0], {**catalog, **files})
    expect_rule("result-system-field", {**catalog, COMMUNITY_PATH: community_run(system={"os": "linux", "kernal": "6.8"})}, level="warning")
    expect_rule("result-system-memory", {**catalog, COMMUNITY_PATH: community_run(system={"os": "windows", "memory_type": "DDR5 6400"})}, level="warning")
    # The memory fields are optional: leaving them out, or filling them in right, reports nothing at all.
    memory = {"memory_gb": 2048, "memory_type": "LPDDR5X-7500", "memory_channels": 12}
    for system in ({"os": "windows"}, {"os": "windows", **memory}, {"os": "windows", "memory_gb": 15.5, "memory_type": ""}):
        issues = run_checks({**catalog, COMMUNITY_PATH: community_run(system=system)})
        assert not [issue for issue in issues if issue.rule in ("result-system-memory", "result-system-field")], system
    issues = run_checks({**catalog, COMMUNITY_PATH: community_run(system={"os": "windows", "memory": "64 GB"})})
    assert any("memory_gb: 64" in issue.message for issue in issues.errors), [issue.format() for issue in issues]
    # A quoted local time, with or without seconds, passes; so does a file name with no date to compare.
    for time in ("09:10", "23:59:59"):
        issues = run_checks({**catalog, COMMUNITY_PATH: timed(time)})
        assert not issues.errors, (time, [issue.format() for issue in issues.errors])
    issues = run_checks({**catalog, f"official/{TEST_ID}/result_launch_day.yaml": result_run()})
    assert not issues.errors, [issue.format() for issue in issues.errors]
    # A full Linux run passes; a Linux community run is never outlier-checked against Windows numbers.
    linux = {
        "os": "linux", "distro": "Bazzite", "kernel": "6.9.12", "mesa": "24.1.5", "runtime": "proton",
        "proton": "GE-Proton9-20", "gamemode": True, "resizable_bar": True,
    }
    slow_linux = community_run(system=linux, result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 10, "p1_low": 8}])
    issues = run_checks({**catalog, f"official/{TEST_ID}/result_20261003_test.yaml": result_run(), COMMUNITY_PATH: slow_linux})
    assert not issues.errors, [issue.format() for issue in issues.errors]
    assert "result-no-baseline" in {issue.rule for issue in issues.warnings}


def check_game_rules():
    """data/games.yaml: four required fields, typed store IDs, no duplicates; results must use its IDs."""
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    game = {"id": "new_game", "name": "New Game", "type": "game", "year": 2024}

    def registry(*items):
        return {GAMES_PATH: {"games": list(items)}}

    def without(key):
        return {name: value for name, value in game.items() if name != key}

    cases = {
        "game-registry (missing file)": None,
        "game-registry (not a list)": "games: Cyberpunk\n",
        "game-field (no type)": registry(without("type")),
        "game-field (bad type)": registry({**game, "type": "benchmark"}),
        "game-field (no year)": registry(without("year")),
        "game-field (year range)": registry({**game, "year": 1970}),
        "game-field (quoted year)": registry({**game, "year": "2024"}),
        "game-field (steam_appid text)": registry({**game, "steam_appid": "1091500"}),
        "game-field (igdb_id negative)": registry({**game, "igdb_id": -1}),
        "game-field (url)": registry({**game, "url": "http://example.com"}),
        "game-field (unknown)": registry({**game, "platform": "pc"}),
        "game-id-format": registry({**game, "id": "New-Game"}),
        "game-duplicate (id)": registry(game, {**game, "name": "Other"}),
        "game-duplicate (name)": registry(game, {**game, "id": "new_game_2", "name": "new game"}),
    }
    for label, games in cases.items():
        rule = label.split(" ")[0]
        with tempfile.TemporaryDirectory() as temp:
            if games is not None:
                content = games[GAMES_PATH] if isinstance(games, dict) else games
                (Path(temp) / GAMES_PATH).write_text(dump(content), encoding="utf-8")
            _, issues = checks.load_games(Path(temp))
        assert rule in {issue.rule for issue in issues.errors}, (label, [issue.format() for issue in issues])
        assert all(issue.doc() == checks.RESULTS_DOC for issue in issues), label

    # Store IDs, url, and notes are optional; when set and valid they pass and reach the API.
    full = {**game, "steam_appid": 1091500, "igdb_id": 1877, "url": "https://example.com/new-game", "notes": "The original release."}
    with tempfile.TemporaryDirectory() as temp:
        (Path(temp) / GAMES_PATH).write_text(dump(registry(full)[GAMES_PATH]), encoding="utf-8")
        games, issues = checks.load_games(Path(temp))
    assert not issues and games == [full], (games, [issue.format() for issue in issues])

    # A result for a game that isn't registered fails with a stub to paste in...
    issues = run_checks({**catalog, COMMUNITY_PATH: community_run(game_id="new_game")})
    (unknown,) = [issue for issue in issues.errors if issue.rule == "result-unknown-game"]
    assert "data/games.yaml" in unknown.message and "- id: new_game" in unknown.message and "year: YYYY" in unknown.message
    # ...and passes once the same pull request adds the game to the registry.
    issues = run_checks({**catalog, **registry(game), COMMUNITY_PATH: community_run(game_id="new_game")})
    assert not issues.errors, [issue.format() for issue in issues.errors]

    # The old free-text game key is replaced, and the message names the right ID.
    run = community_run(game="test game")
    del run["game_id"]
    issues = run_checks({**catalog, COMMUNITY_PATH: run})
    (renamed,) = [issue for issue in issues.errors if issue.rule == "result-game-id"]
    assert "game_id: test_game" in renamed.message, renamed.message
    run = community_run()
    del run["game_id"]
    expect_rule("result-game-id", {**catalog, COMMUNITY_PATH: run})


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


def check_average_only_runs():
    """A run with no 1% low (3DMark, some in-game benchmarks) passes and aggregates."""
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    avg_only = [{"resolution": "1440p", "graphics_preset": "Default", "avg_fps": 86.03, "score": 8603}]
    nomad = community_run(game_id="test_synthetic", result=avg_only, proof={"method": "synthetic_benchmark", "summary_source": "https://www.3dmark.com/sn/1"})
    issues = run_checks({**catalog, COMMUNITY_PATH: nomad})
    assert not issues.errors, [issue.format() for issue in issues.errors]
    assert "result-no-p1-low" not in {issue.rule for issue in issues}, "synthetic benchmarks never report a 1% low"
    # Tools that may report only an average get a warning, never an error.
    for method in ("amd_adrenalin", "other"):
        issues = run_checks({**catalog, COMMUNITY_PATH: community_run(result=avg_only, proof={"method": method})})
        assert not issues.errors and "result-no-p1-low" in {issue.rule for issue in issues.warnings}, method
    # A built-in benchmark often has no 1% low (or its frame log wasn't kept):
    # one info note per file, never a warning.
    issues = run_checks({**catalog, COMMUNITY_PATH: community_run(result=avg_only * 2, proof={"method": "in_game_benchmark"})})
    assert not issues.errors and "result-no-p1-low" not in {issue.rule for issue in issues.warnings}, [issue.format() for issue in issues]
    assert [issue.rule for issue in issues.infos] == ["result-no-p1-low"], [issue.format() for issue in issues]
    assert "2 of 2 run(s)" in issues.infos[0].message
    # Frame-time tools always report a 1% low, so it is required with them.
    for method in checks.P1_LOW_METHODS:
        expect_rule("result-p1-low-required", {**catalog, COMMUNITY_PATH: community_run(result=avg_only, proof={"method": method})})
    assert set(checks.PROOF_METHODS) == {*checks.P1_LOW_METHODS, *checks.AVERAGE_ONLY_METHODS}
    expect_rule("result-proof-method", {**catalog, COMMUNITY_PATH: community_run(proof={"method": "screenshot"})})
    # proof.method is required, and every listed capture tool is accepted.
    no_method = {key: value for key, value in community_run().items() if key != "proof"}
    expect_rule("result-proof-method", {**catalog, COMMUNITY_PATH: no_method})
    expect_rule("result-proof-method", {**catalog, COMMUNITY_PATH: community_run(proof={"raw_log": "raw/a.csv"})})
    for method in checks.PROOF_METHODS:
        issues = run_checks({**catalog, COMMUNITY_PATH: community_run(proof={"method": method})})
        assert not issues.errors, (method, [issue.format() for issue in issues.errors])
    expect_rule("result-field", {**catalog, COMMUNITY_PATH: community_run(result=[{**avg_only[0], "score": "high"}])})

    # Averages still include every run; the 1% low only counts the runs that have one.
    gpu = minimal_entry()
    with_low = result_run()
    without_low = result_run(result=[{"resolution": "1080p", "graphics_preset": "High", "avg_fps": 110}])
    without_low["result"][0]["avg_fps"] = 110
    records = [
        build.build_record(run, run["result"][0], 0, "official", Path(f"official/{TEST_ID}/result_{name}.yaml"), {TEST_ID: gpu})
        for name, run in (("a", with_low), ("b", without_low))
    ]
    assert records[1]["p1_low"] is None
    (summary,) = build.aggregate_game_records(records, "official-summary")
    assert summary["avg_fps"] == 105.0 and summary["p1_low"] == 80.0 and summary["p1_low_range"] == [80.0, 80.0]
    (only_avg,) = build.aggregate_game_records(records[1:], "official-summary")
    assert only_avg["p1_low"] is None and only_avg["p1_low_range"] is None and only_avg["avg_fps"] == 110.0


def check_outlier_limit():
    """A community average more than 25% from the official average is an error."""
    assert checks.OUTLIER_RATIO == 0.25
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    official = {f"official/{TEST_ID}/result_20261003_test.yaml": result_run()}  # 100 FPS

    def run_at(avg_fps):
        entry = {"resolution": "1080p", "graphics_preset": "High", "avg_fps": avg_fps, "p1_low": avg_fps * 0.8}
        return run_checks({**catalog, **official, COMMUNITY_PATH: community_run(result=[entry])})

    for avg_fps in (80, 120):
        assert "community-outlier" not in {issue.rule for issue in run_at(avg_fps).errors}, f"{avg_fps} FPS is within 25%"
    for avg_fps in (70, 130):
        assert "community-outlier" in {issue.rule for issue in run_at(avg_fps).errors}, f"{avg_fps} FPS is more than 25% off"


def check_anonymous_submissions():
    """submitted_by is optional; a valid one may still be given, with or without it in the file name."""
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    folder = f"community/{TEST_ID}"
    for name, run in (
        ("result_20261003_test.yaml", community_run()),
        ("result_20261003_test_2.yaml", community_run()),
        ("result_20261003_test.yaml", community_run(submitted_by="tester")),
        ("result_20261003_test_tester.yaml", community_run(submitted_by="tester")),
    ):
        issues = run_checks({**catalog, f"{folder}/{name}": run})
        assert not issues.errors, (name, [issue.format() for issue in issues.errors])

    # A driver is never asked for; a run with no evidence at all still gets a warning.
    issues = run_checks({**catalog, COMMUNITY_PATH: community_run()})
    warnings = {issue.rule for issue in issues.warnings if issue.rule.startswith(("result-", "community-"))}
    assert warnings == {"result-no-baseline", "result-no-proof"}, [issue.format() for issue in issues]
    found = community_run(credit={"source_url": "https://example.com/review"})
    issues = run_checks({**catalog, COMMUNITY_PATH: found})
    assert "result-no-proof" not in {issue.rule for issue in issues.warnings}, "a found-at link counts as evidence"

    gpu = minimal_entry()
    record = build.build_record(community_run(), community_run()["result"][0], 0, "community", Path(COMMUNITY_PATH), {TEST_ID: gpu})
    assert record["submitted_by"] == "" and record["proof_level"] == "none" and record["proof_reference"] == ""
    record = build.build_record(found, found["result"][0], 0, "community", Path(COMMUNITY_PATH), {TEST_ID: gpu})
    assert record["proof_level"] == "summary-only" and record["proof_reference"] == "https://example.com/review"


def check_upscaling():
    """Upscaling is off by default; it's allowed only when the preset turns it on, and never averages with native."""
    catalog = {TEST_CATALOG_PATH: minimal_entry()}

    def entry(**fields):
        return {"resolution": "1080p", "graphics_preset": "High", "avg_fps": 100, "p1_low": 80, **fields}

    for item in (entry(), entry(upscaling="off"), entry(upscaling="Native"), entry(upscaling=False),
                 entry(upscaling="DLSS Quality", preset_upscaling=True)):
        issues = run_checks({**catalog, COMMUNITY_PATH: community_run(result=[item])})
        assert not issues.errors, (item, [issue.format() for issue in issues.errors])
    for item in (entry(upscaling="DLSS Quality"), entry(upscaling="FSR", preset_upscaling="yes")):
        expect_rule("result-upscaling", {**catalog, COMMUNITY_PATH: community_run(result=[item])})
    # A top-level upscaling applies to every entry.
    expect_rule("result-upscaling", {**catalog, COMMUNITY_PATH: community_run(upscaling="XeSS Quality")})

    gpu = minimal_entry()
    native = community_run(result=[entry(upscaling="off")])
    upscaled = community_run(result=[entry(upscaling="DLSS Quality", preset_upscaling=True, avg_fps=140, p1_low=100)])
    records = [
        build.build_record(run, run["result"][0], 0, "community", Path(COMMUNITY_PATH), {TEST_ID: gpu})
        for run in (native, upscaled)
    ]
    assert [record["upscaling"] for record in records] == ["", "DLSS Quality"]
    summaries = build.aggregate_game_records(records, "community-summary")
    assert sorted(summary["avg_fps"] for summary in summaries) == [100, 140], "upscaled runs never average with native"

    # An upscaled community run is not outlier-checked against a native official run.
    official = {f"official/{TEST_ID}/result_20261003_test.yaml": result_run()}
    issues = run_checks({**catalog, **official, COMMUNITY_PATH: upscaled})
    assert "community-outlier" not in {issue.rule for issue in issues.errors}


def check_third_party_credit():
    """A found result says where it came from; permission is optional."""
    catalog = {TEST_CATALOG_PATH: minimal_entry()}
    folder = f"community/{TEST_ID}"
    screenshot = {f"{folder}/raw/permission_example_creator.png": "placeholder image"}

    def credit(**permission):
        return {
            "name": "Example Creator",
            "url": "https://example.com/example-creator",
            "source_url": "https://example.com/example-creator/gpu-review",
            "permission": permission,
        }

    def found(**fields):
        return {"source_url": "https://example.com/example-creator/gpu-review", **fields}

    passing = (
        found(),
        found(name="Example Creator"),
        found(name="Example Creator", url="https://example.com/example-creator"),
        credit(url="https://example.com/example-creator/permission"),
        credit(screenshot="raw/permission_example_creator.png"),
        credit(note="Example note describing how permission was given"),
        # Unpublished numbers, such as a friend's run, give permission instead of a source.
        {"name": "Example Friend", "permission": {"note": "Example note describing how permission was given"}},
    )
    for block in passing:
        issues = run_checks({**catalog, **screenshot, COMMUNITY_PATH: community_run(credit=block)})
        assert not issues.errors, (block, [issue.format() for issue in issues.errors])

    cases = {
        "community-credit (not a section)": community_run(credit="Example Creator"),
        "community-credit (no source or permission)": community_run(credit={"name": "Example Creator"}),
        "community-credit (empty name)": community_run(credit=found(name="")),
        "community-credit (http source)": community_run(credit={"source_url": "http://example.com/review"}),
        "community-credit (http url)": community_run(credit=found(url="http://example.com")),
        "community-permission (not a section)": community_run(credit=found(permission="yes")),
        "community-permission (empty)": community_run(credit=credit()),
        "community-permission (http url)": community_run(credit=credit(url="http://example.com/permission")),
        "community-permission (missing file)": community_run(credit=credit(screenshot="raw/missing.png")),
        "community-permission (outside folder)": community_run(credit=credit(screenshot="../other_gpu_8gb_fe/raw/permission.png")),
    }
    for label, run in cases.items():
        expect_rule(label.split(" (")[0], {**catalog, **screenshot, COMMUNITY_PATH: run})
    # Official runs are maintainer-verified: a credit only needs who ran it.
    official_path = f"official/{TEST_ID}/result_20261003_test.yaml"
    issues = run_checks({**catalog, official_path: result_run(credit={"name": "Example Friend"})})
    assert not issues.errors, [issue.format() for issue in issues.errors]
    expect_rule("community-credit", {**catalog, official_path: result_run(credit={"url": "https://example.com/friend"})})
    official = result_run()
    record = build.build_record(official, official["result"][0], 0, "official", Path(official_path), {TEST_ID: minimal_entry()})
    assert record["proof_level"] == "maintainer-verified", record["proof_level"]

    # The build credits the source on the run and lists each one once on the summary.
    gpu = minimal_entry()
    credited = community_run(credit=credit(note="ok"))
    unnamed = community_run(credit=found(), submitted_by="finder")
    own = result_run(submitted_by="someone")
    anonymous = community_run()
    records = [
        build.build_record(run, run["result"][0], 0, "community", Path(f"community/{TEST_ID}/result_{name}.yaml"), {TEST_ID: gpu})
        for name, run in (("a", credited), ("b", unnamed), ("c", own), ("d", anonymous))
    ]
    assert records[0]["credit_name"] == "Example Creator" and records[0]["credit_url"] == "https://example.com/example-creator"
    assert records[1]["credit_name"] == "" and records[1]["credit_source_url"] == "https://example.com/example-creator/gpu-review"
    assert records[2]["credit_name"] == "" and "permission" not in records[0]
    (summary,) = build.aggregate_game_records(records, "community-summary")
    assert summary["credits"] == [
        {"name": "", "url": "", "source_url": "https://example.com/example-creator/gpu-review"},
        {"name": "Example Creator", "url": "https://example.com/example-creator", "source_url": "https://example.com/example-creator/gpu-review"},
    ], summary["credits"]
    assert summary["contributors"] == ["finder", "someone"]
    assert [run.get("credit_name") for run in summary["implementations"]] == ["Example Creator", None, None, None]
    assert [run.get("credit_source_url") for run in summary["implementations"]][1] == "https://example.com/example-creator/gpu-review"


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


def cyberpunk_summary(**overrides):
    """A Cyberpunk 2077 benchmark summary.json "Data" block, RTX 4090 on a named preset."""
    data = {
        "gameVersion": "2.31", "gpuName": "NVIDIA GeForce RTX 4090", "gpuMemory": 24210,
        "gpuDriverVersion": "Nvidia v 61714 [r617_07]", "cpuName": "Test CPU", "systemMemory": 32768,
        "osName": "Windows 11 Pro", "osVersion": "10.0.26300", "presetName": "RayTracingUltra",
        "renderWidth": 2560, "renderHeight": 1440, "windowMode": 2, "verticalSync": False, "fpsClamp": -1,
        "averageFps": 120.456, "minFps": 100.0, "maxFps": 140.0, "time": 64.2, "frameNumber": 7700,
        "frameGenerationType": 0, "DLAAEnabled": False, "DLSSEnabled": True, "DLSSQuality": 0,
        "DLSSFrameGenEnabled": False, "DLSSMultiFrameGenEnabled": True, "FSR2Enabled": False, "FSR2Quality": 1,
        "FSR3Enabled": False, "FSR3FrameGenEnabled": False, "FSR4Enabled": False, "XeSSEnabled": False,
        "XeSSFrameGenEnabled": False, "FSREnabled": False, "DRSEnabled": False,
    }
    data.update(overrides)
    return {"RootType": "worldBenchmarkSummary", "Data": data}


def check_import_cyberpunk():
    """import_cyberpunk.py puts a day's runs in one checked file and skips runs it already imported."""
    import shutil

    import import_cyberpunk

    native = {"DLSSEnabled": False}
    runs = {
        "benchmark_2026-10-13_18-44-57": cyberpunk_summary(),
        "benchmark_2026-10-13_19-00-00": cyberpunk_summary(presetName="Custom", **native),
        "benchmark_2026-10-13_19-10-00": cyberpunk_summary(presetName="Custom", DLSSEnabled=False, FSR2Enabled=True),
        "benchmark_2026-10-13_19-20-00": cyberpunk_summary(frameGenerationType=1),
        "benchmark_2026-10-13_19-30-00": cyberpunk_summary(gpuName="NVIDIA GeForce RTX 4080", gpuMemory=16000),
        "benchmark_2026-10-13_19-40-00": cyberpunk_summary(verticalSync=True),
    }
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        data_dir = temp / "data"
        shutil.copytree(FIXTURES_DIR / "gpus", data_dir / "gpus")
        shutil.copy(FIXTURES_DIR / "games.yaml", data_dir / "games.yaml")
        results = temp / "benchmarkResults"

        def add_runs(new_runs):
            for name, summary in new_runs.items():
                (results / name).mkdir(parents=True)
                (results / name / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

        add_runs(runs)
        args = ["--gpu-id", "rtx_4090_24gb_fe", "--input", str(results), "--source", "official",
                "--custom-preset", "High", "--os", "windows", "--data-dir", str(data_dir)]

        assert import_cyberpunk.main([*args, "--dry-run"]) == 0
        assert not (data_dir / "official").exists(), "a dry run writes nothing"
        assert import_cyberpunk.main(args) == 0
        out = data_dir / "official" / "rtx_4090_24gb_fe"
        day_file = out / "result_20261013_cyberpunk_2077.yaml"
        assert sorted(path.name for path in out.iterdir()) == [day_file.name]
        text = day_file.read_text(encoding="utf-8")
        assert "version: '2.31'" in text and "graphics_preset: 'Ray Tracing: Ultra'" in text, text
        day_run = yaml.safe_load(text)
        assert [entry["benchmark_run"] for entry in day_run["result"]] == [
            "benchmark_2026-10-13_18-44-57", "benchmark_2026-10-13_19-00-00",
        ], "the skipped runs are left out"
        entry, custom = day_run["result"]
        assert entry["resolution"] == "1440p" and entry["avg_fps"] == 120.46
        assert entry["upscaling"] == "DLSS Auto" and entry["preset_upscaling"] is True
        assert "p1_low" not in entry and day_run["frame_generation"] is False, "no frames.csv, no p1_low"
        assert day_run["system"]["driver"] == "617.14" and day_run["system"]["memory_gb"] == 32
        assert day_run["proof"]["method"] == "in_game_benchmark"
        assert custom["graphics_preset"] == "High" and "upscaling" not in custom, custom
        assert entry["display_mode"] == "Fullscreen" and "display_mode" not in day_run["system"]
        assert day_run["date"] == "2026-10-13" and list(day_run)[:4] == ["gpu_id", "benchmark_type", "game_id", "date"]
        assert entry["time"] == "18:44:57" and custom["time"] == "19:00:00", "time comes from the run folder"

        catalog, issues = checks.load_catalog(data_dir)
        _, result_issues = checks.load_results(catalog, data_dir)
        assert not [*issues.errors, *result_issues.errors], [issue.format() for issue in result_issues.errors]

        assert import_cyberpunk.main(args) == 0
        assert yaml.safe_load(day_file.read_text(encoding="utf-8")) == day_run, "a second import changes nothing"

        # A file imported before date and time existed gets them back on the next import.
        undated = {key: value for key, value in day_run.items() if key != "date"}
        undated["result"] = [{key: value for key, value in item.items() if key != "time"} for item in day_run["result"]]
        import_cyberpunk.write_run(day_file, undated)
        assert import_cyberpunk.main(args) == 0
        assert yaml.safe_load(day_file.read_text(encoding="utf-8")) == day_run, "date and time are backfilled"

        # A file imported before the game registry says game: and is upgraded to game_id in place.
        named = {("game" if key == "game_id" else key): ("Cyberpunk 2077" if key == "game_id" else value) for key, value in day_run.items()}
        import_cyberpunk.write_run(day_file, named)
        assert import_cyberpunk.main(args) == 0
        assert yaml.safe_load(day_file.read_text(encoding="utf-8")) == day_run, "game becomes game_id"
        assert sorted(path.name for path in out.iterdir()) == [day_file.name], "an upgraded file keeps its runs"

        # A file imported when memory was text ('32 GB') gets memory_gb in the same place.
        texty = {**day_run, "system": {("memory" if key == "memory_gb" else key): ("32 GB" if key == "memory_gb" else value)
                                       for key, value in day_run["system"].items()}}
        import_cyberpunk.write_run(day_file, texty)
        assert import_cyberpunk.main(args) == 0
        assert yaml.safe_load(day_file.read_text(encoding="utf-8")) == day_run, "memory becomes memory_gb"
        assert list(day_run["system"]).index("memory_gb") == list(texty["system"]).index("memory")

        # The RAM type and channels come from the options; summary.json only has the size.
        system = import_cyberpunk.build_system(cyberpunk_summary()["Data"], "windows", "DDR5-6000", 2)
        assert (system["memory_gb"], system["memory_type"], system["memory_channels"]) == (32, "DDR5-6000", 2), system
        assert import_cyberpunk.main([*args, "--memory-channels", "0"]) == 1

        # Left out, the RAM type and channels default to DDR5-6000 dual channel, with a warning on screen.
        assert (day_run["system"]["memory_type"], day_run["system"]["memory_channels"]) == ("DDR5-6000", 2), day_run["system"]
        for options, warned in (([], True), (["--memory-type", "DDR5-6000", "--memory-channels", "2"], False)):
            shown = io.StringIO()
            with contextlib.redirect_stdout(shown):
                assert import_cyberpunk.main([*args, "--dry-run", *options]) == 0
            assert ("WARNING: --memory-type was not given" in shown.getvalue()) is warned, shown.getvalue()
            assert ("fix memory_type and memory_channels" in shown.getvalue()) is warned, shown.getvalue()

        # Later the same day: a new run joins the day's file, and a run after a
        # driver update gets its own file because system applies to the whole file.
        add_runs({
            "benchmark_2026-10-13_20-00-00": cyberpunk_summary(renderWidth=3840, renderHeight=2160, windowMode=1),
            "benchmark_2026-10-13_21-00-00": cyberpunk_summary(gpuDriverVersion="Nvidia v 61800 [r618_00]"),
            "benchmark_2026-10-14_09-00-00": cyberpunk_summary(),
        })
        assert import_cyberpunk.main(args) == 0
        assert sorted(path.name for path in out.iterdir()) == [
            day_file.name, "result_20261013_cyberpunk_2077_2.yaml", "result_20261014_cyberpunk_2077.yaml",
        ]
        day_runs = [entry["benchmark_run"] for entry in yaml.safe_load(day_file.read_text(encoding="utf-8"))["result"]]
        assert day_runs[-1] == "benchmark_2026-10-13_20-00-00" and len(day_runs) == 3, day_runs
        assert yaml.safe_load(day_file.read_text(encoding="utf-8"))["result"][-1]["display_mode"] == "Borderless windowed", \
            "a different display mode stays in the same file"
        updated = yaml.safe_load((out / "result_20261013_cyberpunk_2077_2.yaml").read_text(encoding="utf-8"))
        assert updated["system"]["driver"] == "618.00" and len(updated["result"]) == 1
        assert import_cyberpunk.main([*args[:1], "no_such_gpu", *args[2:]]) == 1
        registry = (data_dir / "games.yaml").read_text(encoding="utf-8")
        (data_dir / "games.yaml").write_text("games:\n  - id: other_game\n    name: Other\n    type: game\n    year: 2020\n", encoding="utf-8")
        assert import_cyberpunk.main(args) == 1, "the importer needs cyberpunk_2077 in data/games.yaml"
        (data_dir / "games.yaml").write_text(registry, encoding="utf-8")

        # frames.csv gives avg_fps and p1_low: earlier runs get them on the next
        # import, new runs when imported, and a frames.csv that doesn't match
        # summary.json (here a different frame count) is ignored.
        def add_frames(name, times):
            lines = ["Frame index, Frame time (ms), DLSS Frame Generation (ms), CPU memory (MB)"]
            lines += [f"{index}, {ms}, {ms}" for index, ms in enumerate(times)]
            (results / name / "frames.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

        frames = [8.2] * 7600 + [15.0] * 100  # 7700 frames, the summary's frameNumber
        add_frames("benchmark_2026-10-13_18-44-57", frames)
        add_frames("benchmark_2026-10-13_19-00-00", frames[:7000])
        add_runs({"benchmark_2026-10-14_10-00-00": cyberpunk_summary()})
        add_frames("benchmark_2026-10-14_10-00-00", frames)
        assert import_cyberpunk.main([*args, "--dry-run"]) == 0
        assert "p1_low" not in day_file.read_text(encoding="utf-8"), "a dry run writes nothing"
        assert import_cyberpunk.main(args) == 0
        first, custom = yaml.safe_load(day_file.read_text(encoding="utf-8"))["result"][:2]
        assert first["avg_fps"] == 120.65 and first["p1_low"] == 66.67, first
        assert list(first).index("p1_low") == list(first).index("avg_fps") + 1
        assert "p1_low" not in custom and custom["avg_fps"] == 120.46, custom
        latest = yaml.safe_load((out / "result_20261014_cyberpunk_2077.yaml").read_text(encoding="utf-8"))["result"]
        assert latest[-1]["benchmark_run"] == "benchmark_2026-10-14_10-00-00" and latest[-1]["p1_low"] == 66.67, latest


ISSUE_FIXTURE = ROOT / "tests" / "fixtures" / "issues" / "valid.md"


def run_issue(body, data_dir, out_dir):
    """Feed one issue body to issue_to_result.py; return (exit code, comment)."""
    import issue_to_result

    body_file = out_dir / "body.md"
    out_dir.mkdir(parents=True, exist_ok=True)
    body_file.write_text(body, encoding="utf-8")
    args = ["--body-file", str(body_file), "--issue", "42", "--author", "octo-cat",
            "--data-dir", str(data_dir), "--out-dir", str(out_dir)]
    status = issue_to_result.main(args)
    return status, (out_dir / "comment.md").read_text(encoding="utf-8")


def check_issue_to_result():
    """A benchmark issue becomes one checked community file; a bad issue gets a reply and no file."""
    import shutil

    valid = ISSUE_FIXTURE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        data_dir = temp / "data"
        shutil.copytree(FIXTURES_DIR, data_dir)
        folder = data_dir / "community" / "rtx_4090_24gb_fe"

        status, comment = run_issue(valid, data_dir, temp / "ok")
        assert status == 0, comment
        path = folder / "result_20261003_cyberpunk_2077.yaml"
        run = yaml.safe_load(path.read_text(encoding="utf-8"))
        # The product and game names resolve to their IDs; the preset reuses the existing spelling.
        assert run["gpu_id"] == "rtx_4090_24gb_fe" and run["game_id"] == "cyberpunk_2077" and "game" not in run, run
        assert [entry["graphics_preset"] for entry in run["result"]] == ["Ultra", "Ultra"], run
        assert run["result"][1]["resolution"] == "1440p" and run["result"][1]["avg_fps"] == 180, run
        assert run["submitted_by"] == "octo-cat" and run["proof"]["method"] == "presentmon", run
        assert run["date"] == "2026-10-03" and "credit" not in run, run
        memory = {key: run["system"].get(key) for key in ("memory_gb", "memory_type", "memory_channels")}
        assert memory == {"memory_gb": 32, "memory_type": "DDR5-6000", "memory_channels": 2}, run["system"]
        assert "Closes #42" in (temp / "ok" / "pr_body.md").read_text(encoding="utf-8")
        catalog, _ = checks.load_catalog(data_dir)
        _, issues = checks.load_results(catalog, data_dir)
        assert not [issue for issue in issues.errors if path.name in issue.path], [issue.format() for issue in issues]

        # A second issue for the same day and game gets the next free name.
        assert run_issue(valid, data_dir, temp / "again")[0] == 0
        assert (folder / "result_20261003_cyberpunk_2077_2.yaml").exists()

        # The game's ID works too.
        by_id = valid.replace("### Game\n\ncyberpunk 2077", "### Game\n\ncyberpunk_2077")
        assert by_id != valid and run_issue(by_id, data_dir, temp / "by_id")[0] == 0
        assert (folder / "result_20261003_cyberpunk_2077_3.yaml").exists()

        found = valid.replace("I ran it myself", "Someone else: I found it in a video, review, or post")
        status, comment = run_issue(found, data_dir, temp / "found")
        assert status == 1 and "Source link" in comment, comment
        found = found.replace("### Source link\n\n_No response_", "### Source link\n\nhttps://example.com/review")
        assert run_issue(found, data_dir, temp / "found2")[0] == 0

        before = sorted(folder.iterdir())
        games_before = (data_dir / "games.yaml").read_text(encoding="utf-8")
        failures = {
            "not in the catalog": valid.replace("GeForce RTX 4090 Founders Edition", "rtx 4090 founders"),
            "is not a number": valid.replace("175.2, 140.1", "fast, 140"),
            "community-outlier": valid.replace("175.2, 140.1", "400, 300"),
            "result-p1-low-required": valid.replace("175.2, 140.1", "175.2"),
            "CC BY 4.0": valid.replace("- [X] I release", "- [ ] I release"),
            "YYYY-MM-DD": valid.replace("2026-10-03", "10/03/2026"),
            "Memory (GB)**": valid.replace("### Memory (GB)\n\n32 GB", "### Memory (GB)\n\n32 GB DDR5"),
            "Memory channels**": valid.replace("### Memory channels\n\ndual", "### Memory channels\n\ntriple"),
            "its own pull request": valid.replace("### Game\n\ncyberpunk 2077", "### Game\n\nSome Unlisted Game"),
            "Did you mean `cyberpunk_2077`?": valid.replace("### Game\n\ncyberpunk 2077", "### Game\n\ncyberpunk 2078"),
        }
        for expected, body in failures.items():
            status, comment = run_issue(body, data_dir, temp / expected)
            assert status == 1 and expected in comment, (expected, comment)
            assert not (temp / expected / "pr_body.md").exists(), expected
        assert sorted(folder.iterdir()) == before, "a failed issue leaves no file behind"
        assert (data_dir / "games.yaml").read_text(encoding="utf-8") == games_before, "the bot never adds a game"

        # Untrusted text can't break out of the reply's code spans.
        status, comment = run_issue(valid.replace("GeForce RTX 4090 Founders Edition", "x` @someone `y"), data_dir, temp / "md")
        assert status == 1 and "`x' @someone 'y`" in comment, comment


def check_issue_form_matches_script():
    """The issue form's labels and options are the ones issue_to_result.py reads."""
    import issue_to_result as script

    form = yaml.safe_load((ROOT / ".github" / "ISSUE_TEMPLATE" / "benchmark.yml").read_text(encoding="utf-8"))
    assert form["labels"] == ["benchmark"], form["labels"]
    fields = {item["id"]: item for item in form["body"] if item["type"] != "markdown"}
    assert {item["attributes"]["label"]: key for key, item in fields.items()} == script.FIELDS
    options = {key: item["attributes"].get("options") for key, item in fields.items()}
    assert options["method"] == list(script.CAPTURE_TOOLS), options["method"]
    assert sorted(script.CAPTURE_TOOLS.values()) == sorted(checks.PROOF_METHODS)
    assert options["who"] == list(script.WHO_RAN_IT) and options["os"] == list(script.OSES)
    assert options["graphics_api"] == list(script.GRAPHICS_APIS)
    assert [option["label"] for option in options["credit"]] == [script.CREDIT_ME]
    labels = [option["label"] for option in options["confirmations"]]
    assert labels[0].startswith(script.FRAME_GENERATION_OFF) and labels[1].startswith(script.LICENSE_AGREEMENT), labels


def check_bot_safety():
    """CODEOWNERS lists the maintainers, and bot PRs can never deploy, approve, or merge."""
    owners = [
        line.split()
        for line in (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert any(rule[0] == "*" and len(rule) > 1 for rule in owners), "CODEOWNERS needs a '*' rule with owners"
    for rule in owners:
        for owner in rule[1:]:
            assert owner.startswith("@") and checks.GITHUB_USER_PATTERN.match(owner[1:]), f"bad code owner '{owner}'"
            assert "bot" not in owner.lower(), f"never make a bot a code owner: {owner}"

    workflows = ROOT / ".github" / "workflows"
    preview = (workflows / "preview.yml").read_text(encoding="utf-8")
    assert "!startsWith(github.head_ref, 'benchmark/')" in preview, "preview.yml must skip benchmark/ branches"
    bot = (workflows / "benchmark-issue.yml").read_text(encoding="utf-8")
    for text in (preview, bot):
        assert not re.search(r"^\s*pull_request_target:", text, re.MULTILINE), "never trigger on pull_request_target"
    for banned in ("CLOUDFLARE", "secrets.GITHUB_TOKEN", "gh pr review", "gh pr merge", "createReview", "pulls.merge"):
        assert banned not in bot, f"benchmark-issue.yml must not use '{banned}'"
    # The issue body only ever reaches the shell through an env var.
    assert re.search(r"ISSUE_BODY: \$\{\{ github\.event\.issue\.body \}\}", bot)
    assert bot.count("github.event.issue.body") == 1, "use the issue body only through ISSUE_BODY"


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
        assert build.main(data_dir, output_dir) == 1
        assert not output_dir.exists(), "build must not write output when checks fail"


def check_minimal_entry_builds():
    gpu = minimal_entry()
    run = result_run()
    games = {game["id"]: game for game in TEST_GAMES["games"]}
    record = build.build_record(run, run["result"][0], 0, "official", Path(f"official/{TEST_ID}/result_x.yaml"), {TEST_ID: gpu}, games)
    assert record["tdp_w"] is None and record["vram_gb"] == 8 and record["gpu_vendor"] == "nvidia"
    assert (record["game_id"], record["game"], record["game_type"], record["game_year"]) == ("test_game", "Test Game", "game", 2024)


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
    """Each catalog template passes the checks alongside the fixture reference files."""
    # The catalog templates show cards that aren't published, so their bases
    # come from the fixture catalog snapshot rather than data/.
    references = {
        path.relative_to(FIXTURES_DIR).as_posix(): path.read_text(encoding="utf-8")
        for path in (FIXTURES_DIR / "gpus" / "reference").rglob("*.yaml")
    }
    for template in sorted((ROOT / "templates").glob("catalog_*.yaml")):
        text = template.read_text(encoding="utf-8")
        entry = yaml.safe_load(text)
        vendor = entry["identity"]["gpu_vendor"]
        folder = "reference" if template.stem == "catalog_reference" else entry["classification"]["form_factor"]
        issues = run_checks({**references, f"gpus/{folder}/{vendor}/{entry['id']}.yaml": text})
        assert not issues.errors, (template.name, [issue.format() for issue in issues.errors])

    # Each community template passes the result checks as written, anonymously.
    catalog = {
        path.relative_to(ROOT / "data").as_posix(): path.read_text(encoding="utf-8")
        for path in (ROOT / "data" / "gpus").rglob("*.yaml")
    }
    catalog[GAMES_PATH] = (ROOT / "data" / "games.yaml").read_text(encoding="utf-8")
    for template in sorted((ROOT / "templates").glob("community_*.yaml")):
        text = template.read_text(encoding="utf-8")
        run = yaml.safe_load(text)
        # Save it under the template's own date, as a submitter would.
        day = run["date"].replace("-", "")
        issues = run_checks({**catalog, f"community/{run['gpu_id']}/result_{day}_template.yaml": text})
        assert not issues.errors, (template.name, [issue.format() for issue in issues.errors])


def check_rules_are_documented():
    """Every rule name in checks.py must be a heading in the matching doc."""
    source = (ROOT / "scripts" / "checks.py").read_text(encoding="utf-8")
    rules = set(re.findall(r'issues\.(?:error|warning)\(\s*[\w\[\]]+,\s*"([a-z-]+)"', source))
    assert len(rules) > 20, rules
    for rule in rules:
        doc = checks.RESULTS_DOC if rule.startswith(checks.RESULTS_DOC_PREFIXES) else checks.CATALOG_DOC
        text = (ROOT / doc).read_text(encoding="utf-8")
        assert f"#### `{rule}`" in text, f"rule '{rule}' needs a '#### `{rule}`' heading in {doc}"


def check_real_data():
    """data/ is what deploys: it passes every check and never holds synthetic runs."""
    catalog, issues = checks.load_catalog()
    games, game_issues = checks.load_games()
    runs, result_issues = checks.load_results(catalog, games=games)
    issues = checks.Issues([*issues, *game_issues, *result_issues])
    assert not issues.errors, [issue.format() for issue in issues.errors]
    synthetic = [checks.relative_path(path) for items in runs.values() for path, run in items if run.get("synthetic")]
    assert not synthetic, f"synthetic runs belong in tests/fixtures/data, not data/: {synthetic}"


def check_catalog_specs(api_dir):
    master = load_json(api_dir / "gpus.json")
    assert master["metadata"]["schema_version"] == build.SCHEMA_VERSION == "0.17"
    group_by = master["metadata"]["comparison_policy"]["group_by"]
    assert {"os", "upscaling", "game_id"} <= set(group_by) and "game" not in group_by
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

    arc_a770 = load_json(api_dir / "community" / "arc_a770_16gb_le" / "summary.json")
    assert arc_a770["records"]
    assert all(record["vram_gb"] == 16 and record["tdp_w"] == 225 for record in arc_a770["records"])
    assert all(record["gpu_vendor"] == "intel" for record in arc_a770["records"])

    dashboard = load_json(api_dir / "dashboard.json")
    deck_records = [record for record in dashboard["records"] if record["gpu_id"] == "steam_deck_oled_16gb"]
    assert deck_records, "expected dashboard records for steam_deck_oled_16gb"
    assert all(record["vram_gb"] is None and record["tdp_w"] == 15 for record in deck_records)
    assert all(record["os"] == "linux" and record["distro"] == "SteamOS" for record in deck_records)
    assert all(record["os"] in checks.RESULT_OSES for record in dashboard["records"])
    xtx_alan_wake = [
        record for record in dashboard["records"]
        if record["gpu_id"] == "rx_7900_xtx_24gb_reference" and record["game_id"] == "alan_wake_2"
    ]
    assert sorted(record["os"] for record in xtx_alan_wake) == ["linux", "windows"], "one summary per OS"


def main():
    check_valid_fixtures()
    check_catalog_rules()
    check_result_rules()
    check_game_rules()
    check_os_grouping()
    check_average_only_runs()
    check_outlier_limit()
    check_anonymous_submissions()
    check_upscaling()
    check_third_party_credit()
    check_parse_mangohud()
    check_import_cyberpunk()
    check_issue_to_result()
    check_issue_form_matches_script()
    check_bot_safety()
    check_reports_every_error_and_build_stops()
    check_minimal_entry_builds()
    check_base_merge()
    check_rules_are_documented()
    check_templates_are_valid()
    check_real_data()
    with tempfile.TemporaryDirectory() as temp:
        check_fixture_build(Path(temp))
    with tempfile.TemporaryDirectory() as temp:
        check_site_seo(Path(temp))
    check_pick_rules()
    check_blog_tokens()
    check_blog_posts()
    check_release_version()
    print("Catalog rules, result rules, aggregation, submitter, and catalog spec checks passed")


def check_fixture_build(api_dir):
    """Build the synthetic fixtures and check the payload numbers they're known to produce."""
    stale = api_dir / "official" / "removed_gpu_8gb_fe" / "summary.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}", encoding="utf-8")
    assert build.main(FIXTURES_DIR, api_dir) == 0, "the fixtures must pass every check"
    assert not stale.parent.exists(), "a GPU removed from the catalog loses its old summary folder"
    assert load_json(api_dir / "dashboard.json")["metadata"]["synthetic_data"] is True
    picks = load_json(api_dir / "dashboard.json")["picks"]
    assert [pick["slot"] for pick in picks] == ["nvidia", "intel"], "picks come out in amd, nvidia, intel order"
    assert picks[0]["name"] == "GeForce RTX 4090 Founders Edition" and picks[0]["vram_gb"] == 24, picks[0]
    assert picks[1]["gpu_id"] is None and picks[1]["links"][0]["retailer_name"] == "Newegg", picks[1]
    arc_a770 = load_json(api_dir / "community" / "arc_a770_16gb_le" / "summary.json")
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
    # Every run carries its file's date; time is "" when the run didn't record one.
    for record in arc_a770["records"]:
        named = re.match(r"result_(\d{4})(\d{2})(\d{2})", Path(record["source_file"]).name)
        assert record["date"] == "-".join(named.groups()) and record["time"] == "", record

    linux_1080p = find_summary(arc_a770["game_summaries"], "1080p", "linux")
    assert linux_1080p["run_count"] == 1 and linux_1080p["avg_fps"] == 63.0, "Linux runs never average with Windows"
    assert linux_1080p["distro"] == "Fedora"

    summary_1440p = find_summary(arc_a770["game_summaries"], "1440p")
    assert summary_1440p["run_count"] == 1
    assert summary_1440p["avg_fps"] == 60.0
    assert summary_1440p["p1_low"] == 42.3

    dashboard = load_json(api_dir / "dashboard.json")
    assert len(dashboard["records"]) == 30
    # System RAM: numbers stay numbers, and a run without them gets null.
    flagship = load_json(api_dir / "official" / "rtx_4090_24gb_fe" / "summary.json")
    with_memory = [record for record in flagship["records"] if record["memory_gb"] is not None]
    assert [(record["memory_gb"], record["memory_type"], record["memory_channels"]) for record in with_memory] == [
        (64, "DDR5-6000", 2)
    ], with_memory
    assert all(record["memory_channels"] is None and record["memory_type"] == "" for record in flagship["records"]
               if record["memory_gb"] is None)
    implementations = [item for summary in flagship["game_summaries"] for item in summary["implementations"]]
    assert {"memory_gb": 64, "memory_type": "DDR5-6000", "memory_channels": 2}.items() <= next(
        item for item in implementations if "memory_gb" in item).items()
    check_game_payload(api_dir)
    check_catalog_specs(api_dir)


def check_game_payload(api_dir):
    """Names come from games.yaml; the dashboard lists only games with summaries."""
    dashboard = load_json(api_dir / "dashboard.json")
    assert [game["id"] for game in dashboard["games"]] == ["alan_wake_2", "baldurs_gate_3", "cyberpunk_2077", "helldivers_2"]
    assert dashboard["games"][2] == {"id": "cyberpunk_2077", "name": "Cyberpunk 2077", "type": "game", "year": 2020}
    registry = load_json(api_dir / "games.json")
    assert registry["count"] == 6 and {game["type"] for game in registry["games"]} == set(checks.GAME_TYPES)
    assert next(game for game in registry["games"] if game["id"] == "cyberpunk_2077")["steam_appid"] == 1091500
    names = {game["id"]: game["name"] for game in registry["games"]}
    for record in dashboard["records"]:
        assert record["game"] == names[record["game_id"]] and record["game_type"] == "game", record


def check_site_seo(site_dir):
    """Every host must name the same canonical origin, and the plain pages must carry every summary."""
    origin = build.SITE_URL
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="{origin}">' in index, "index.html canonical must equal build.SITE_URL"
    assert f'<meta property="og:url" content="{origin}">' in index, "og:url must equal the canonical"
    robots = (ROOT / "site" / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {origin}sitemap.xml" in robots
    assert not re.search(r"^\s*Disallow:\s*\S", robots, re.MULTILINE), "robots.txt must not block crawlers"

    # Build the fixtures with pages on, into a temp site folder.
    assert build.main(FIXTURES_DIR, site_dir / "api" / "v1", site_dir) == 0
    for name in build.SITE_PAGES:
        assert (site_dir / name).is_file(), f"build must write site/{name}"
    sitemap = (site_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert f"<loc>{origin}</loc>" in sitemap and f"<loc>{origin}benchmarks/</loc>" in sitemap
    page = (site_dir / "benchmarks" / "index.html").read_text(encoding="utf-8")
    full = (site_dir / "llms-full.txt").read_text(encoding="utf-8")
    assert "<script" not in page, "benchmarks/index.html must work without JavaScript"
    assert f'<link rel="canonical" href="{origin}benchmarks/">' in page
    records = load_json(site_dir / "api" / "v1" / "dashboard.json")["records"]
    for record in records:
        row = "| " + " | ".join(build.summary_row(record)) + " |"
        assert row in full, f"llms-full.txt is missing {record['id']}"
        cells = "".join(f"<td>{build.html.escape(cell)}</td>" for cell in build.summary_row(record))
        assert cells in page, f"benchmarks/index.html is missing {record['id']}"
    assert f"<loc>{origin}blog/</loc>" in sitemap, "the sitemap must list the blog"
    check_licenses(site_dir)


def check_licenses(site_dir):
    """Code is MIT, data is CC BY 4.0, and every place that states the data license agrees."""
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"), "LICENSE must be the MIT text"
    data_license = (ROOT / "data" / "LICENSE").read_text(encoding="utf-8")
    assert data_license.startswith("Open GPU Benchmarks Data License\n"), "data/LICENSE must start with the project header"
    assert "Creative Commons Attribution 4.0 International Public License" in data_license, "data/LICENSE must hold the CC BY 4.0 legal code"
    url = build.DATA_LICENSE["url"]
    assert build.DATA_LICENSE["id"] == build.API_LICENSE["name"] == "CC-BY-4.0" and build.API_LICENSE["url"] == url
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    json_ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', index, re.S).group(1))
    dataset = next(node for node in json_ld["@graph"] if node["@type"] == "Dataset")
    assert dataset["license"]["url"] == url, "the Dataset JSON-LD must name the CC BY 4.0 license"
    creator = dataset["creator"]
    assert creator["@type"] in {"Organization", "Person"} and creator["name"], "the Dataset JSON-LD needs a typed creator"
    assert creator["url"] == build.SITE_URL, "the Dataset creator must link the canonical origin"
    assert f'"usageInfo": "{build.LICENSE_PAGE}"' in index and build.DATA_ATTRIBUTION["text"] in index
    assert 'href="license/"' in index, "the dashboard must link the license page"
    license_page = (ROOT / "site" / "license" / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="{build.LICENSE_PAGE}">' in license_page
    assert url in license_page and build.DATA_ATTRIBUTION["url"] in license_page
    api_dir = site_dir / "api" / "v1"
    api_files = sorted(api_dir.rglob("*.json"))
    assert api_files, "the build wrote no API files"
    for path in api_files:
        payload = load_json(path)
        relative = path.relative_to(api_dir).as_posix()
        assert list(payload)[:2] == ["_license", "_source"], f"{relative} must lead with _license and _source"
        assert payload["_license"] == build.API_LICENSE, relative
        assert payload["_source"]["url"] == f"{build.SITE_URL}api/v1/{relative}", relative
        assert payload["_source"]["generated_at"] == payload["metadata"]["generated_at"], relative
    assert load_json(api_dir / "dashboard.json")["metadata"]["license"] == build.DATA_LICENSE
    for page in ("llms.txt", "llms-full.txt", "benchmarks/index.html"):
        text = (site_dir / page).read_text(encoding="utf-8")
        assert url in text and build.DATA_ATTRIBUTION["url"] in text, f"{page} must state the license and credit link"
    assert f"<loc>{build.LICENSE_PAGE}</loc>" in (site_dir / "sitemap.xml").read_text(encoding="utf-8")


def check_pick_rules():
    """data/picks.yaml: one card per slot, catalog IDs checked, store links validated."""
    catalog = checks.load_catalog(FIXTURES_DIR)[0]
    cases = {
        "slot: amd\n    name: \"Card\"\n    note: \"Why.\"\n    links:\n      - retailer: ebay\n        url: https://www.example.com/x\n": "pick-link",
        "slot: amd\n    name: \"Card\"\n    note: \"Why.\"\n    links:\n      - retailer: amazon\n        url: http://www.example.com/x\n": "pick-link",
        "slot: amd\n    name: \"Card\"\n    note: \"Why.\"\n": "pick-link",
        "slot: arm\n    name: \"Card\"\n    note: \"Why.\"\n": "pick-slot",
        "slot: amd\n    gpu_id: rtx_4090_24gb_fe\n    note: \"Why.\"\n    links:\n      - retailer: amazon\n        url: https://www.example.com/x\n": "pick-gpu-id",
        "slot: amd\n    gpu_id: no_such_gpu_8gb\n    note: \"Why.\"\n    links:\n      - retailer: amazon\n        url: https://www.example.com/x\n": "pick-gpu-id",
        "slot: amd\n    name: \"Card\"\n    links:\n      - retailer: amazon\n        url: https://www.example.com/x\n": "pick-field",
        "slot: amd\n    name: \"Card\"\n    note: \"Why.\"\n    price: 999\n    links:\n      - retailer: amazon\n        url: https://www.example.com/x\n": "pick-field",
    }
    for body, rule in cases.items():
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "picks.yaml").write_text(f"picks:\n  - {body}", encoding="utf-8")
            _, issues = checks.load_picks(catalog, Path(temp))
        assert rule in {issue.rule for issue in issues.errors}, (rule, body, [issue.format() for issue in issues])
    with tempfile.TemporaryDirectory() as temp:
        twice = "  - slot: amd\n    name: \"A\"\n    note: \"Why.\"\n    links:\n      - retailer: amazon\n        url: https://www.example.com/a\n"
        (Path(temp) / "picks.yaml").write_text("picks:\n" + twice + twice, encoding="utf-8")
        picks, issues = checks.load_picks(catalog, Path(temp))
        assert "pick-slot" in {issue.rule for issue in issues.errors} and len(picks) == 1
        (Path(temp) / "picks.yaml").write_text("picks:\n", encoding="utf-8")
        assert checks.load_picks(catalog, Path(temp)) == ([], []), "an empty picks file is valid"
    assert checks.load_picks(catalog, Path("does-not-exist"))[0] == [], "picks.yaml is optional"
    picks, issues = checks.load_picks(checks.load_catalog()[0])
    assert not issues.errors, [issue.format() for issue in issues.errors]


def css_tokens(text, selector):
    """The custom properties in the one-line `<selector> { ... }` block."""
    match = re.search(re.escape(selector) + r" \{([^}]*)\}", text)
    assert match, f"no {selector} block"
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", match.group(1)))


def check_blog_tokens():
    """The blog copies the dashboard's color tokens; they must not drift."""
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    blog = (ROOT / "blog" / "src" / "styles" / "tokens.css").read_text(encoding="utf-8")
    for selector in (":root", ':root[data-theme="light"]'):
        assert css_tokens(index, selector) == css_tokens(blog, selector), (
            f"blog/src/styles/tokens.css {selector} differs from site/index.html; copy the block again"
        )


def check_blog_posts():
    """Drafts never reach the sitemap or llms.txt; published posts do."""
    with tempfile.TemporaryDirectory() as temp:
        content = Path(temp)
        posts = {
            "live-post": 'title: "Live"\ndescription: "Shown."\ndate: "2026-10-01"\ntype: guide\n',
            "draft-post": 'title: "Draft"\ndescription: "Hidden."\ndate: "2026-10-02"\ntype: post\ndraft: true\n',
            "newer-post": 'title: "Newer"\ndescription: "Shown."\ndate: "2026-10-03"\nupdated: "2026-10-05"\ntype: review\n',
        }
        for slug, front in posts.items():
            (content / slug).mkdir()
            (content / slug / "index.md").write_text(f"---\n{front}---\n\nBody.\n", encoding="utf-8")
        found = build.blog_posts(content)
    assert [post["slug"] for post in found] == ["newer-post", "live-post"], found
    metadata = {"generated_at": "2026-10-14T00:00:00+00:00"}
    sitemap = build.sitemap_xml(metadata, found)
    origin = build.SITE_URL
    assert f"<loc>{origin}blog/newer-post/</loc><lastmod>2026-10-05</lastmod>" in sitemap
    assert f"<loc>{origin}blog/live-post/</loc>" in sitemap and "draft-post" not in sitemap
    # The real content folder parses too (every draft is skipped).
    build.blog_posts()


def check_release_version():
    """RELEASE_VERSION is MAJOR.MINOR.DATA.POST and matches the newest CHANGELOG release."""
    version = build.RELEASE_VERSION
    assert re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version), f"RELEASE_VERSION {version} must have four parts"
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## (\d[\d.]*) - \d{4}-\d{2}-\d{2}$", changelog, re.MULTILINE)
    assert released and released[0] == version, (
        f"newest CHANGELOG release is {released[:1]}, but RELEASE_VERSION is {version}"
    )


if __name__ == "__main__":
    main()
