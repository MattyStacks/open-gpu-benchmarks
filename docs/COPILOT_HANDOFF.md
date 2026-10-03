# Open GPU Benchmarks - Project Handoff

## Project identity

- Repository: `MattyStacks/open-gpu-benchmarks`
- Default branch: `main`
- Public site: <https://mattystacks.github.io/open-gpu-benchmarks/>
- Public dashboard API: <https://mattystacks.github.io/open-gpu-benchmarks/api/v1/dashboard.json>
- GPU master API: <https://mattystacks.github.io/open-gpu-benchmarks/api/v1/gpus.json>
- Current development version: `v0.3.0`

## Current data contract

The static dashboard is built from a GPU-rooted source tree. `data/gpus.yaml`
is authoritative: every official and community result must be in the folder
named by its exact catalog ID and must carry the same `gpu_id`.

```text
data/gpus.yaml
data/official/<gpu_id>/result_YYYYMMDD_<benchmark>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<contributor>.yaml
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

## Data rules

- The source schema uses `graphics_preset`; do not add a `settings` fallback.
- Desktop and laptop GPU records never share a summary group.
- Frame generation must be disabled for comparable game runs.
- Keep exact machine metadata with each run while charts display grouped
  summaries.
- Treat raw capture evidence as preferred and preserve its reference when
  correcting or removing a record.

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
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

[`scripts/parse.py`](../scripts/parse.py) writes converted CSV output directly
to `data/community/<gpu_id>/result_YYYYMMDD_*.yaml`.

## Current synthetic fixtures

The repository has 11 catalog GPU entries, 15 official result runs, 10
community result runs, and 24 combined dashboard summaries. The Arc A770
fixtures exercise a multi-profile source file and matching-run aggregation.
Every fixture is marked `synthetic: true`.

## Version and deployment

The project deploys `site/` using
[.github/workflows/build.yml](../.github/workflows/build.yml). Generated
`site/api/` files are ignored and recreated in CI.

For a versioned dashboard payload change:

1. Update `RELEASE_VERSION` and `SCHEMA_VERSION` in
   [`scripts/build.py`](../scripts/build.py).
2. Update current-version references, fixture counts, and feature summary in
   [README.md](../README.md) and this document.
3. Run the build, validation, compile checks, and `git diff --check`.
4. Do not commit `site/api/` unless repository policy changes.
5. Create a Git tag only when explicitly requested after review.
