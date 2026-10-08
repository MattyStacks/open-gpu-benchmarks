# Open GPU Benchmarks - Project Handoff

## Project identity

- Repository: `MattyStacks/open-gpu-benchmarks`
- Default branch: `main`
- Public site: <https://mattystacks.github.io/open-gpu-benchmarks/>
- Public dashboard API: <https://mattystacks.github.io/open-gpu-benchmarks/api/v1/dashboard.json>
- GPU master API: <https://mattystacks.github.io/open-gpu-benchmarks/api/v1/gpus.json>
- Current development version: `v0.4.0`
  - v0.4.0: community files require `submitted_by` and a `_<github_user>` file
    name suffix, API schema 0.5 (`submitted_by`, `contributors`), dashboard
    JSON API panel and GitHub links.
  - Version history lives in [CHANGELOG.md](../CHANGELOG.md); update its
    `Unreleased` section with every behavioral change.
  - Open follow-ups live in [docs/TODO.md](TODO.md).

## Current data contract

The static dashboard is built from a GPU-rooted source tree. `data/gpus.yaml`
is authoritative: every official and community result must be in the folder
named by its exact catalog ID and must carry the same `gpu_id`.

```text
data/gpus.yaml
data/official/<gpu_id>/result_YYYYMMDD_<benchmark>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
data/community/<gpu_id>/raw/**                         optional raw evidence
                 |
                 v
python scripts/build.py
                 |
                 v
site/api/v1/gpus.json
site/api/v1/official/<gpu_id>/summary.json
site/api/v1/community/<gpu_id>/summary.json
site/api/v1/dashboard.json
```

There are no source `summary.yaml` files. Each source file describes one
benchmark capture and has a non-empty `result` YAML list. Each dashed list
entry is a separate resolution/preset profile. The dash is required YAML list
syntax: duplicate `result:` keys overwrite each other. The build validates and
expands every entry before deriving source-specific per-GPU and dashboard
summaries. The per-GPU summaries retain all records and metrics, allowing
future benchmark types such as 3DMark to coexist with game FPS results.

`gpus.json` is the master API. Each catalog entry includes official/community
run and game-summary data plus links to the generated per-GPU summary JSON.
`dashboard.json` remains a game-FPS-only, chart-ready projection.

Schema `0.5` adds `submitted_by` (string, empty for official runs) to every run
record and the per-run `implementations` entries, and a sorted, de-duplicated
`contributors` list to every grouped summary. The dashboard does not display
submitters; they are API-only.

## Data rules

- The source schema uses `graphics_preset`; do not add a `settings` fallback.
- Desktop and laptop GPU records never share a summary group.
- Frame generation must be disabled for comparable game runs.
- Keep exact machine metadata with each run while charts display grouped
  summaries.
- Treat raw capture evidence as preferred and preserve its reference when
  correcting or removing a record.
- Community files require `submitted_by` (the PR author's GitHub username), and
  the file name must be `result_YYYYMMDD_<game>_<github_user>.yaml`, matched
  case-insensitively. Same-day repeats put a number before the username
  (`..._helldivers_2_mattystacks.yaml`). `validate.py` enforces this; it does
  not compare against the PR author.

`benchmark_type` defaults to `game`. Game source files need `game` and a
`result` list whose entries each carry `resolution`, `graphics_preset`,
`avg_fps`, and `p1_low`. Each entry is independently validated and expanded.
The build averages matching entries from one or several files, while different
resolution/preset profiles remain distinct. Other types retain their `result`
entries in per-GPU API data but do not enter dashboard charts.

## Build and validation

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python scripts/test_build.py
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

[`scripts/parse.py`](../scripts/parse.py) writes converted CSV output directly
to `data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml`. It
requires `--submitted-by` and adds `_2`, `_3`, ... before the username rather
than overwrite an existing file. `scripts/test_build.py` covers aggregation,
`submitted_by`/`contributors` output, and the validator's submitter checks.

## Current synthetic fixtures

The repository has 11 catalog GPU entries, 15 official result runs, 10
community result runs, and 24 combined dashboard summaries. The Arc A770
fixtures exercise a multi-profile source file and matching-run aggregation.
Every fixture is marked `synthetic: true`. All community fixtures use
`submitted_by: MattyStacks`.

## Dashboard

`site/index.html` is the whole dashboard. It loads `./api/v1/dashboard.json`
relative to the page, so it works on GitHub Pages or a future custom domain.
The header has **JSON API** (jumps to `#data-api`) and **GitHub** buttons, and
the footer links to the repository, contributing guide, and issues. GitHub
links are absolute (`https://github.com/MattyStacks/open-gpu-benchmarks`); API
links stay relative. The **Get the data as JSON** panel (`#data-api`) lists
each endpoint with Open and Copy URL actions, plus curl/fetch snippets built
from `location` at runtime, and shows the schema version.

Icons live in `site/favicons/` (committed static files, linked relatively).
`favicon.svg` is the primary icon and carries its own
`prefers-color-scheme` light/dark styles. `syncFavicon()` in `index.html`
fetches it and swaps in a `data:` URI whose media query is forced to match the
site's ◐ theme toggle, so the tab icon follows the toggle rather than the OS.
If the fetch fails, the static link still follows the OS. `favicon.ico` and
`apple-touch-icon.png` are dark-only fallbacks.

## Version and deployment

The project deploys `site/` using
[.github/workflows/build.yml](../.github/workflows/build.yml). Generated
`site/api/` files are ignored and recreated in CI.

For a versioned dashboard payload change:

1. Update `RELEASE_VERSION` and `SCHEMA_VERSION` in
   [`scripts/build.py`](../scripts/build.py).
2. Update current-version references, fixture counts, and feature summary in
   [README.md](../README.md) and this document, and move `Unreleased` in
   [CHANGELOG.md](../CHANGELOG.md) under the new version heading.
3. Run the build, validation, compile checks, and `git diff --check`.
4. Do not commit `site/api/` unless repository policy changes.
5. Create a Git tag only when explicitly requested after review.
