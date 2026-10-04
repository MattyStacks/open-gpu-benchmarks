# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive
graph. The site is a static GitHub Pages dashboard built from reviewable YAML.

Current version: `v0.4.0`. See [CHANGELOG.md](CHANGELOG.md) for what changed in each version, and
[docs/TODO.md](docs/TODO.md) for planned follow-ups.

## GPU-rooted data flow

`data/gpus.yaml` is the authoritative hardware catalog. Every source folder
uses one of its IDs exactly, so each card, laptop GPU, handheld, or iGPU owns
its benchmark results and any future card-specific metrics.

```text
data/gpus.yaml
data/official/<gpu_id>/result_YYYYMMDD_<benchmark>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
data/community/<gpu_id>/raw/**                         optional raw evidence
                    ↓
python scripts/build.py
                    ↓
site/api/v1/gpus.json                                  GPU-rooted master API
site/api/v1/official/<gpu_id>/summary.json             generated GPU summary
site/api/v1/community/<gpu_id>/summary.json            generated GPU summary
site/api/v1/dashboard.json                             game-FPS dashboard data
```

Each result file describes one benchmark capture and contains a non-empty
`result` YAML list. Each dashed list item is one resolution/preset result; the
dash is required so YAML retains multiple profiles rather than overwriting a
duplicate key. There are no checked-in source summaries. The build validates
and expands every list item, then derives game summaries by GPU ID, form
factor, known power profile, game, resolution, and `graphics_preset`. It never
groups desktop and laptop GPUs together.

[`site/api/v1/gpus.json`](site/api/v1/gpus.json) is the master JSON contract:
each catalog GPU has `links.official_summary` and
`links.community_summary`, plus its generated `official` and `community`
statistics. The linked per-GPU JSON includes all source runs, grouped game
summaries, evidence references, and exact machine metadata. Generated API
files are ignored by Git and appear after running the build.

Current synthetic fixtures: 11 catalog GPUs, 15 official runs, 10 community
runs, and 24 dashboard summaries. The community fixtures include a
multi-profile file and two matching Arc A770 results that aggregate into one
1080p summary. All fixture records are marked
`synthetic: true`, and every community fixture is `submitted_by: MattyStacks`.

API schema `0.5` adds `submitted_by` to every generated run record and a
`contributors` list (unique GitHub usernames) to every grouped summary. The
dashboard's **Get the data as JSON** panel lists each endpoint with Open and
Copy URL actions; copied URLs are built from the page's own location, so they
stay correct on GitHub Pages or a custom domain.

## Community contributions

Copy [templates/community_submission.yaml](templates/community_submission.yaml)
to the folder matching its `gpu_id`, for example:

```text
data/community/rtx_4090/result_20261003_cyberpunk_mattystacks.yaml
```

Every community file sets `submitted_by` to the GitHub username of the person
opening the pull request, and the file name ends with that username
(compared case-insensitively; lowercase is conventional). For a second file
with the same date and game, add a number before the username, such as
`result_20261003_cyberpunk_2_mattystacks.yaml`.

The pull-request validator checks all community `result_*.yaml` and
`result_*.yml` files in GPU folders. It enforces the game benchmark contract,
requires frame generation to be disabled, checks catalog/folder identity and
the `submitted_by`/file-name match, and
compares matching game runs with official baselines. See
[docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) for the
complete rules.

## Local development

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python scripts/test_build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000>.

Use `scripts/parse.py` to convert PresentMon or MangoHud CSV data directly
into `data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml`
(it adds `_2`, `_3`, ... before the username instead of overwriting):

```powershell
python scripts/parse.py capture.csv --gpu-id rtx_4090 --game "Cyberpunk 2077" --submitted-by MattyStacks
```

## Site and deployment

`site/index.html` fetches the generated dashboard JSON with relative paths, so
the site works under any host or custom domain. Links to the GitHub repository,
contributing guide, and issues are absolute and appear in the header and
footer. The workflow in
[.github/workflows/build.yml](.github/workflows/build.yml) rebuilds `site/api/`
and deploys the site whenever `main` changes. Do not commit generated API
files unless repository policy changes.

For the architecture and maintenance checklist, see
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md). Contributor setup and PR
requirements are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT Code, CC0 Data
