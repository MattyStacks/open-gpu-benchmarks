"""Build GPU-rooted API data and crawlable summary pages for the dashboard.

    python scripts/build.py                                  # data/ -> site/api/v1 + site pages
    python scripts/build.py --data-dir tests/fixtures/data   # preview the synthetic fixtures
"""
import argparse
import html
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install -r requirements.txt")
    sys.exit(1)

import checks
from checks import DATA_DIR, ROOT, relative_path, spec


SITE_DIR = ROOT / "site"
OUTPUT_DIR = SITE_DIR / "api" / "v1"
SCHEMA_VERSION = "0.20"
# MAJOR.MINOR.DATA.POST: MAJOR = breaking data contract or API, MINOR = any
# code change, DATA = newly published runs or catalog GPUs, POST = a new or
# updated blog post.
# A bump resets the parts to its right; all four parts are always written.
RELEASE_VERSION = "1.13.0.0"
# The canonical origin. Every host (Cloudflare, GitHub Pages, pages.dev) points
# search engines here; index.html and robots.txt repeat it, and test_build.py
# checks they agree.
SITE_URL = "https://opengpubenchmarks.com/"
# Plain pages for crawlers and AI tools that don't run the dashboard's JavaScript.
# benchmarks/index.html, not benchmarks.html: Cloudflare Pages 308-redirects
# "*.html" to the bare path, and a canonical URL must not redirect.
SITE_PAGES = ("benchmarks/index.html", "llms.txt", "llms-full.txt", "sitemap.xml")
# Blog posts: content/posts/<slug>/index.md(x). Astro (blog/) renders them into
# site/blog/; this build only lists them in the sitemap and llms.txt.
CONTENT_DIR = ROOT / "content" / "posts"
# Benchmark data (data/ and everything built from it) is CC BY 4.0 with reasonable
# attribution, AI training included (site/license/index.html); the code is MIT.
DATA_LICENSE = {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}
LICENSE_PAGE = f"{SITE_URL}license/"
# The credit line reusers are asked to show; index.html and license/ repeat it.
DATA_ATTRIBUTION = {"text": "Data from Open GPU Benchmarks", "url": "https://opengpubenchmarks.com"}
# Put first in every API file, so a copied response still says where it came from.
API_LICENSE = {
    "name": DATA_LICENSE["id"],
    "url": DATA_LICENSE["url"],
    "attribution": "Open GPU Benchmarks",
    "attribution_url": DATA_ATTRIBUTION["url"],
    "ai_training_permitted": True,
    "terms": LICENSE_PAGE,
}


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


def os_details(system):
    """Copy the optional OS detail fields: text as str or "", bools as bool or None."""
    details = {}
    for key, (_, kind) in checks.OS_FIELDS.items():
        value = system.get(key)
        if kind == "bool":
            details[key] = value if isinstance(value, bool) else None
        else:
            details[key] = "" if value is None else str(value)
    return details


def testbench_fields(run, testbenches_by_id):
    """Official desktop runs carry their bench, resolved through counts_as; everything else gets ""."""
    source_id = str(run.get("testbench_id") or "")
    bench_id = checks.resolve_testbench_id(testbenches_by_id, source_id) if source_id else ""
    bench = testbenches_by_id.get(bench_id, {})
    return {
        # testbench_id groups runs; testbench_source_id is the bench the file names.
        "testbench_id": bench_id,
        "testbench_source_id": source_id,
        "testbench_name": bench.get("name", ""),
        # The memory generation ("DDR5") and the dashboard's label for it ("DDR5 Bench").
        "testbench_memory": checks.testbench_memory(bench) if bench else "",
        "testbench_label": checks.testbench_label(bench) if bench else "",
    }


def build_record(run, result, result_index, source, source_path, gpu_by_id, games_by_id=None, testbenches_by_id=None):
    """Expand one checked result entry into a flat run record."""
    gpu = gpu_by_id[run["gpu_id"]]
    game = (games_by_id or {}).get(run.get("game_id"), {})
    benchmark_type = run.get("benchmark_type", "game")
    system = run.get("system") or {}
    proof = run.get("proof") or {}
    credit = run.get("credit") or {}
    raw_log = proof.get("raw_log")
    proof_reference = checks.proof_reference(run)
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
        # game_id groups runs; the name, type, and year come from data/games.yaml.
        "game_id": str(run.get("game_id", "")),
        "game": game.get("name", ""),
        "game_type": game.get("type", ""),
        "game_year": game.get("year"),
        "game_version": str(run.get("version", "")),
        # The day the file was run (a found result's publish date), and the run's
        # optional local time. Neither groups runs; they're for filtering by age.
        "date": str(run.get("date", "")),
        "time": str(result.get("time", "")),
        "resolution": result.get("resolution", ""),
        "graphics_preset": result.get("graphics_preset", ""),
        # "" when upscaling was off, the default; a grouping key, so it never averages with native runs.
        "upscaling": checks.upscaling(run, result),
        "frame_generation": bool(result.get("frame_generation", run.get("frame_generation", False))),
        "driver": str(system.get("driver", run.get("driver", ""))),
        "implementation_name": implementation_name or "",
        "gpu_power_w": float(gpu_power_w) if gpu_power_w is not None else None,
        "overclocked": bool(run.get("overclocked", False)),
        "cpu": str(system.get("cpu", "")),
        **testbench_fields(run, testbenches_by_id or {}),
        # System RAM, for API users; not a grouping key. Numbers are null when missing.
        "memory_gb": system.get("memory_gb") if checks.is_number(system.get("memory_gb")) else None,
        "memory_type": str(system.get("memory_type") or ""),
        "memory_channels": system.get("memory_channels") if checks.is_number(system.get("memory_channels")) else None,
        "power_mode": str(system.get("power_mode", system.get("tdp_mode", ""))),
        # A result item may carry its own display_mode when it changed between runs.
        "display_mode": str(result.get("display_mode", system.get("display_mode", ""))),
        "os": str(system.get("os", "")),
        **os_details(system),
        "capture_method": str(proof.get("method", "")),
        # Official runs are verified by the maintainer even without linked evidence;
        # "none" marks an unverified community run: no raw log, summary source, or found-at link.
        "proof_level": "raw-log" if raw_log else "summary-only" if proof_reference
        else "maintainer-verified" if source == "official" else "none",
        "proof_reference": proof_reference,
        "source_file": relative_path(source_path),
        # Empty for anonymous runs: community results don't need a username.
        "submitted_by": str(run.get("submitted_by", "")),
        # Results someone else measured credit that source first, by name or
        # by where they were found. Any permission proof stays in Git.
        "credit_name": str(credit.get("name", "")),
        "credit_url": str(credit.get("url", "")),
        "credit_source_url": str(credit.get("source_url", "")),
        "synthetic": bool(run.get("synthetic", False)),
    }
    if benchmark_type == "game":
        record["avg_fps"] = round(float(result["avg_fps"]), 2)
        record["p1_low"] = round(float(result["p1_low"]), 2) if result.get("p1_low") is not None else None
    return record


def source_records(runs, source, gpu_by_id, games_by_id, testbenches_by_id=None):
    return [
        build_record(run, result, result_index, source, path, gpu_by_id, games_by_id, testbenches_by_id)
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
                record["game_id"],
                record["resolution"],
                record["graphics_preset"],
                record["upscaling"],
                record["form_factor"],
                record["gpu_power_w"],
                record["os"],
                record["testbench_id"],
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
                    "upscaling",
                    "gpu_power_w",
                    "overclocked",
                    "cpu",
                    "testbench_source_id",
                    "memory_gb",
                    "memory_type",
                    "memory_channels",
                    "power_mode",
                    "display_mode",
                    "driver",
                    "os",
                    *checks.OS_FIELDS,
                    "capture_method",
                    "credit_name",
                    "credit_source_url",
                    "submitted_by",
                )
                if run[key] not in ("", None)
            }
            for run in runs
        ]
        # Runs without a 1% low (3DMark, many in-game benchmarks) only count toward the average.
        lows = [run["p1_low"] for run in runs if run["p1_low"] is not None]
        summaries.append(
            {
                **first,
                "id": f"{id_prefix}-{first['id']}",
                "run_count": len(runs),
                "avg_fps": round(sum(run["avg_fps"] for run in runs) / len(runs), 2),
                "p1_low": round(sum(lows) / len(lows), 2) if lows else None,
                "avg_fps_range": [
                    min(run["avg_fps"] for run in runs),
                    max(run["avg_fps"] for run in runs),
                ],
                "p1_low_range": [min(lows), max(lows)] if lows else None,
                "implementations": implementations,
                "contributors": sorted(
                    {run["submitted_by"] for run in runs if run["submitted_by"]},
                    key=str.lower,
                ),
                "credits": [
                    {"name": name, "url": url, "source_url": source_url}
                    for name, url, source_url in sorted(
                        {
                            (run["credit_name"], run["credit_url"], run["credit_source_url"])
                            for run in runs
                            if run["credit_name"] or run["credit_source_url"]
                        },
                        key=lambda credit: (credit[0].lower(), credit[2]),
                    )
                ],
            }
        )
    return summaries


def remove_stale_gpu_folders(output_dir, gpu_ids):
    """Delete per-GPU summaries left by an earlier build for GPUs no longer in the catalog."""
    for source in checks.RESULT_SOURCES:
        source_dir = output_dir / source
        if not source_dir.is_dir():
            continue
        for folder in source_dir.iterdir():
            if folder.is_dir() and folder.name not in gpu_ids:
                shutil.rmtree(folder)


def write_json(output_dir, path, payload):
    """Write one API file, led by its license and its own canonical URL."""
    destination = output_dir / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = {"url": f"{SITE_URL}api/v1/{Path(path).as_posix()}", "generated_at": payload["metadata"]["generated_at"]}
    with destination.open("w", encoding="utf-8") as output:
        json.dump({"_license": API_LICENSE, "_source": source, **payload}, output, indent=2)
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


SUMMARY_COLUMNS = ("GPU", "Benchmark", "Resolution", "Preset", "Upscaling", "OS", "Source", "Test bench", "Avg FPS", "1% low", "Runs")
FORM_FACTOR_ORDER = ("Desktop", "Laptop", "Handheld", "Igpu")
FORM_FACTOR_LABELS = {"Igpu": "Integrated"}


def fps(value):
    return "n/a" if value is None else f"{value:g}"


def testbench_cell(record):
    """The dashboard's Platform wording: "DDR5 Bench: <bench>" on official desktop rows."""
    if record["testbench_id"]:
        return f"{record['testbench_label']}: {record['testbench_name']}"
    return "Community" if record["form_factor"] == "Desktop" and record["source"] == "community" else ""


def summary_row(record):
    return (
        record["gpu_name"],
        record["game"],
        record["resolution"],
        record["graphics_preset"],
        record["upscaling"] or "Native",
        record["os"].title(),
        record["source"].title(),
        testbench_cell(record),
        fps(record["avg_fps"]),
        fps(record["p1_low"]),
        str(record["run_count"]),
    )


def testbench_order(record):
    """Newest memory first; runs without a bench last."""
    return checks.testbench_rank({"memory_type": record["testbench_memory"]}) if record["testbench_id"] else 1


def records_by_form_factor(records):
    """Group summaries by form factor, each sorted by game, resolution, then fastest first."""
    grouped = defaultdict(list)
    for record in records:
        grouped[record["form_factor"]].append(record)
    order = {name: index for index, name in enumerate(FORM_FACTOR_ORDER)}
    return [
        (
            FORM_FACTOR_LABELS.get(factor, factor),
            sorted(rows, key=lambda r: (r["game"], r["resolution"], r["graphics_preset"], r["os"], testbench_order(r), -r["avg_fps"])),
        )
        for factor, rows in sorted(grouped.items(), key=lambda item: order.get(item[0], len(order)))
    ]


def method_lines(metadata):
    policy = metadata["comparison_policy"]
    return [
        "Each row averages every run that matches on GPU, form factor, GPU power, game or benchmark (by its ID), "
        "resolution, graphics preset, upscaling, OS, and (for official desktop runs) test bench.",
        "Official desktop GPUs are tested on more than one system, one per memory generation (DDR5, DDR4, and DDR3 "
        "benches). The same GPU on two benches is two rows, never one average.",
        "Windows and Linux runs are never averaged together, and desktop and laptop GPUs never share a row.",
        "Frame generation is off in every comparable run. Upscaling is off unless the graphics preset turns it on.",
        "Official runs are verified by the maintainer. Community runs are reviewed in pull requests, and a "
        f"community average more than {policy['community_outlier_threshold']:.0%} away from the matching "
        "official average is rejected.",
        "1% low is n/a when the capture tool doesn't report one (3DMark and many in-game benchmarks).",
    ]


def write_text(site_dir, name, text):
    (site_dir / name).parent.mkdir(parents=True, exist_ok=True)
    (site_dir / name).write_text(text, encoding="utf-8", newline="\n")


def benchmarks_html(records, metadata):
    page_url = f"{SITE_URL}benchmarks/"
    description = "Every Open GPU Benchmarks summary as plain tables: average FPS and 1% lows by GPU, game or benchmark, resolution, preset, and OS."
    sections = []
    for factor, rows in records_by_form_factor(records):
        head = "".join(f"<th>{column}</th>" for column in SUMMARY_COLUMNS)
        body = "\n".join(
            "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in summary_row(record)) + "</tr>"
            for record in rows
        )
        sections.append(
            f'<h2 id="{factor.lower()}">{factor} GPUs</h2>\n'
            f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>"
        )
    tables = "\n".join(sections) or "<p>No benchmark summaries are published yet.</p>"
    synthetic = (
        '<p class="warn">This build contains synthetic test data.</p>\n' if metadata["synthetic_data"] else ""
    )
    method = "\n".join(f"<li>{html.escape(line)}</li>" for line in method_lines(metadata))
    generated = metadata["generated_at"][:10]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GPU Benchmark Tables | Open GPU Benchmarks</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Open GPU Benchmarks">
<meta property="og:title" content="GPU Benchmark Tables">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{page_url}">
<link rel="icon" href="../favicons/favicon.svg" type="image/svg+xml">
<style>
:root {{ color-scheme: light dark; }}
body {{ margin: 0 auto; max-width: 1200px; padding: 24px 16px 48px; font: 14px/1.5 system-ui, sans-serif; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 28px; font-size: 13px; }}
th, td {{ border: 1px solid #8884; padding: 6px 8px; text-align: left; }}
th {{ background: #8882; }}
.warn {{ font-weight: 700; color: #b45309; }}
</style>
</head>
<body>
<h1>Open GPU Benchmarks: benchmark tables</h1>
<p>{html.escape(description)} Generated {generated} (release {metadata["release_version"]}, schema {metadata["schema_version"]}).
Open the <a href="../">interactive dashboard</a>, or get the same numbers as JSON from
<a href="../api/v1/dashboard.json">api/v1/dashboard.json</a> (summaries) and
<a href="../api/v1/gpus.json">api/v1/gpus.json</a> (GPU specs and per-GPU summaries). The test benches are in
<a href="../api/v1/testbenches.json">api/v1/testbenches.json</a>.</p>
{synthetic}<h2>How the numbers are grouped</h2>
<ul>
{method}
</ul>
{tables}
<p>Source data is reviewable YAML in the <a href="https://github.com/MattyStacks/open-gpu-benchmarks">GitHub repository</a>.
The data is licensed under <a href="{DATA_LICENSE["url"]}">CC BY 4.0</a>: use it for anything, including AI training,
with a link back to <a href="{DATA_ATTRIBUTION["url"]}">opengpubenchmarks.com</a>. See the <a href="../license/">license page</a> for what counts as reasonable attribution.</p>
</body>
</html>
"""


def markdown_table(rows):
    lines = ["| " + " | ".join(SUMMARY_COLUMNS) + " |", "|" + " --- |" * len(SUMMARY_COLUMNS)]
    lines += ["| " + " | ".join(cell.replace("|", "\\|") for cell in summary_row(record)) + " |" for record in rows]
    return "\n".join(lines)


def blog_posts(content_dir=CONTENT_DIR):
    """Published (non-draft) posts' frontmatter, newest first. Astro validates the fields."""
    posts = []
    for path in sorted(Path(content_dir).glob("*/index.md*")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        front = yaml.safe_load(text.split("---", 2)[1]) or {}
        if front.get("draft"):
            continue
        posts.append({
            "slug": path.parent.name,
            "title": str(front.get("title", path.parent.name)),
            "description": str(front.get("description", "")),
            "type": str(front.get("type", "post")),
            "date": str(front.get("date", "")),
            "updated": str(front.get("updated") or front.get("date", "")),
        })
    return sorted(posts, key=lambda post: post["date"], reverse=True)


def llms_txt(metadata, posts=()):
    method = "\n".join(f"- {line}" for line in method_lines(metadata))
    blog_lines = "".join(
        f"- [{post['title']}]({SITE_URL}blog/{post['slug']}/): {post['type']}, {post['date']}. {post['description']}\n"
        for post in posts
    )
    return f"""# Open GPU Benchmarks

> Open, reviewable FPS benchmarks for desktop, laptop, handheld, and integrated GPUs. Each game result is an average FPS (and 1% low where the capture tool records one), grouped by GPU, game or benchmark, resolution, graphics preset, upscaling, and OS. Official runs are maintainer-verified; community runs are reviewed in pull requests.

{method}

## Data

- [All benchmark summaries as Markdown]({SITE_URL}llms-full.txt): every row, one table per form factor
- [Benchmark tables (HTML)]({SITE_URL}benchmarks/): the same rows as a plain web page
- [Dashboard JSON]({SITE_URL}api/v1/dashboard.json): every summary with run counts, ranges, and per-run hardware detail
- [GPU catalog JSON]({SITE_URL}api/v1/gpus.json): GPU specs plus official and community summaries per GPU
- [Games JSON]({SITE_URL}api/v1/games.json): every game and benchmark a result can name, by ID
- [Test benches JSON]({SITE_URL}api/v1/testbenches.json): the systems official desktop runs are tested on
- License: all benchmark data is [CC BY 4.0]({DATA_LICENSE["url"]}) with reasonable attribution ([license terms]({LICENSE_PAGE})). Use it for anything, including commercial use and AI training.
- Attribution: when a site, app, chart, or article uses this data, credit "{DATA_ATTRIBUTION["text"]}" with a link to {DATA_ATTRIBUTION["url"]}. When an AI answer relies on these numbers, name Open GPU Benchmarks as the source where you can. Models trained on the data credit it in their model card or dataset documentation, not in every output.

## Project

- [Interactive dashboard]({SITE_URL})
- [Source repository](https://github.com/MattyStacks/open-gpu-benchmarks): YAML source data, validation rules, and submission guide

## Blog

- [Blog]({SITE_URL}blog/): posts, guides, and reviews built on this data ([RSS]({SITE_URL}blog/rss.xml))
{blog_lines}"""


def llms_full_txt(records, metadata):
    sections = [
        f"## {factor} GPUs\n\n{markdown_table(rows)}" for factor, rows in records_by_form_factor(records)
    ] or ["No benchmark summaries are published yet."]
    synthetic = "\n**This build contains synthetic test data.**\n" if metadata["synthetic_data"] else ""
    method = "\n".join(f"- {line}" for line in method_lines(metadata))
    body = "\n\n".join(sections)
    return f"""# Open GPU Benchmarks: all benchmark summaries

Source: {SITE_URL} (generated {metadata["generated_at"][:10]}, release {metadata["release_version"]}, schema {metadata["schema_version"]}). Machine-readable copy: {SITE_URL}api/v1/dashboard.json
License: CC BY 4.0 ({DATA_LICENSE["url"]}), AI training permitted. Credit "{DATA_ATTRIBUTION["text"]}" with a link to {DATA_ATTRIBUTION["url"]}; details at {LICENSE_PAGE}
{synthetic}
{method}

{body}
"""


def sitemap_xml(metadata, posts=()):
    lastmod = metadata["generated_at"][:10]
    pages = [(path, lastmod) for path in ("", "benchmarks/", "license/", "llms.txt", "llms-full.txt", "blog/")]
    pages += [(f"blog/{post['slug']}/", post["updated"]) for post in posts]
    urls = "".join(f"  <url><loc>{SITE_URL}{path}</loc><lastmod>{date}</lastmod></url>\n" for path, date in pages)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n"
    )


def write_site_pages(site_dir, records, metadata):
    """Write the plain summary pages, built from the same records as dashboard.json."""
    posts = blog_posts()
    write_text(site_dir, "benchmarks/index.html", benchmarks_html(records, metadata))
    write_text(site_dir, "llms.txt", llms_txt(metadata, posts))
    write_text(site_dir, "llms-full.txt", llms_full_txt(records, metadata))
    write_text(site_dir, "sitemap.xml", sitemap_xml(metadata, posts))


def main(data_dir=DATA_DIR, output_dir=OUTPUT_DIR, site_dir=None):
    """Build the API into output_dir; also write the summary pages when site_dir is set."""
    gpus, catalog_issues = checks.load_catalog(data_dir)
    games, game_issues = checks.load_games(data_dir)
    testbenches, testbench_issues = checks.load_testbenches(data_dir)
    runs, result_issues = checks.load_results(gpus, data_dir, games, testbenches)
    picks, pick_issues = checks.load_picks(gpus, data_dir)
    issues = checks.Issues([*catalog_issues, *game_issues, *testbench_issues, *result_issues, *pick_issues])
    if checks.report(issues, "Checks (run validate.py for warnings)", show_warnings=False):
        print("Build stopped: fix the errors above; nothing was written to site/api.")
        return 1
    reviews_source = load_yaml(data_dir / "reviews.yaml")
    gpu_by_id = {gpu["id"]: gpu for gpu in gpus}
    games_by_id = {game["id"]: game for game in games}
    testbenches_by_id = {bench["id"]: bench for bench in testbenches}
    official = source_records(runs, "official", gpu_by_id, games_by_id, testbenches_by_id)
    community_raw = source_records(runs, "community", gpu_by_id, games_by_id, testbenches_by_id)
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
        "license": DATA_LICENSE,
        "comparison_policy": {
            "group_by": [
                "gpu_id",
                "form_factor",
                "gpu_power_w",
                "game_id",
                "resolution",
                "graphics_preset",
                "upscaling",
                "os",
                "testbench_id",
            ],
            "game_version_is_not_a_grouping_key": True,
            "testbench_applies_to": "official desktop runs only; counts_as is resolved first",
            "os_detail_is_not_a_grouping_key": True,
            "frame_generation": "off",
            "upscaling": "off unless the graphics preset turns it on",
            "community_outlier_threshold": checks.OUTLIER_RATIO,
        },
    }

    remove_stale_gpu_folders(output_dir, {gpu["id"] for gpu in gpus})
    official_by_gpu = {}
    community_by_gpu = {}
    for gpu in gpus:
        official_by_gpu[gpu["id"]] = gpu_summary("official", gpu, official, metadata)
        community_by_gpu[gpu["id"]] = gpu_summary("community", gpu, community_raw, metadata)
        write_json(
            output_dir,
            Path("official") / gpu["id"] / "summary.json",
            official_by_gpu[gpu["id"]],
        )
        write_json(
            output_dir,
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
    # The games that have summaries, for the dashboard's picker; games.json has them all.
    used = {record["game_id"] for record in dashboard_records}
    dashboard_games = sorted(
        ({key: game.get(key) for key in ("id", "name", "type", "year")} for game in games if game["id"] in used),
        key=lambda game: game["name"].lower(),
    )
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

    write_json(output_dir, "gpus.json", {"metadata": metadata, "gpus": master_gpus})
    write_json(output_dir, "games.json", {"metadata": metadata, "games": games, "count": len(games)})
    write_json(
        output_dir,
        "testbenches.json",
        {"metadata": metadata, "testbenches": testbenches, "count": len(testbenches)},
    )
    write_json(output_dir, "official.json", {"metadata": metadata, "records": official, "count": len(official)})
    write_json(
        output_dir,
        "community.json",
        {
            "metadata": metadata,
            "records": community_summaries,
            "count": len(community_summaries),
            "raw_count": len(community_raw),
        },
    )
    write_json(
        output_dir,
        "dashboard.json",
        {
            "metadata": metadata,
            "games": dashboard_games,
            "resolutions": resolutions,
            "graphics_presets": graphics_presets,
            "testbenches": testbenches,
            "records": dashboard_records,
            "reviews": reviews_source.get("reviews", []),
            "picks": picks,
        },
    )

    if site_dir is not None:
        write_site_pages(site_dir, dashboard_records, metadata)

    print(
        f"GPUs: {len(gpus)} | Games: {len(games)} | Official runs: {len(official)} | "
        f"Community runs: {len(community_raw)} | Dashboard summaries: "
        f"{len(dashboard_records)} | Output: {output_dir}"
    )
    return 0


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="source tree to build (default: data)")
    args = parser.parse_args(argv)
    return main(args.data_dir.resolve(), OUTPUT_DIR, SITE_DIR)


if __name__ == "__main__":
    sys.exit(cli())
