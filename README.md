# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive
graph. The site is a static GitHub Pages dashboard built from reviewable YAML.

Current version: `v0.6.0`: Linux vs Windows results charted side by side, cited catalog sources, and one overlaid avg/1% low bar per GPU. See [CHANGELOG.md](CHANGELOG.md) for what changed in each version, and
[docs/TODO.md](docs/TODO.md) for planned follow-ups.

## GPU-rooted data flow

`data/gpus/` is the authoritative hardware catalog, one file per product at
`data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. The ID names the exact
product, including its memory size: `rtx_5060_ti_8gb_msi_ventus_2x_oc`,
`rtx_4090_24gb_fe`, `steam_deck_oled_16gb`. Different memory sizes and board
makers are different IDs, so their results are never averaged together.

Every source folder uses one of these IDs exactly, so each card, laptop GPU,
handheld, or iGPU owns its benchmark results and any future card-specific
metrics. Each entry also carries hardware specs in nested sections
(`identity`, `classification`, `silicon`, `memory`, `clocks`, `power`,
`release`, `features`), shown per card in the dashboard table. Only five
fields are required; anything missing shows as `—`. Specs shared by every
product built on one GPU live once in a reference file under
`data/gpus/reference/`. Each product points at it with `base:` and only lists
what it changes or adds. Handhelds and laptops also carry a `platform`
section with their device specs, such as RAM speed and power range. Every
entry lists its `sources`: the pages its specs came from. They're shown as
links when you expand a row. ID rules, the field
reference, and the meaning of every check are in
[data/gpus/README.md](data/gpus/README.md).

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml
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
duplicate key. There are no checked-in source summaries. The build runs every
check in `scripts/checks.py` first and stops without writing anything if any
fail. It then expands every list item and derives game summaries by product
ID, form factor, known power profile, game, resolution, `graphics_preset`, and
OS. It never groups desktop and laptop GPUs together, or Windows and Linux runs.

Every game run sets `system.os` to `windows` or `linux`. The dashboard has
Windows and Linux filter chips, labels a product's bars by OS when both appear,
and stripes the Linux bars. The distro is not a grouping key: SteamOS, Bazzite,
and CachyOS runs of one profile share a Linux bar. Distro, kernel, Mesa, Proton,
and the other OS details are recorded on every run in the JSON. **To compare
distros, kernels, or Proton versions, download `community.json`,
`official.json`, or a per-product `summary.json` and chart them yourself.**

[`site/api/v1/gpus.json`](site/api/v1/gpus.json) is the master JSON contract:
each catalog GPU has `links.official_summary` and
`links.community_summary`, its nested hardware specs, plus its generated
`official` and `community`
statistics. The linked per-GPU JSON includes all source runs, grouped game
summaries, evidence references, and exact machine metadata. Generated API
files are ignored by Git and appear after running the build.

Current synthetic fixtures: 11 catalog GPUs, 19 official runs, 12 community
runs, and 30 dashboard summaries. The community fixtures include a
multi-profile file and two matching Arc A770 LE results that aggregate into one
1080p summary. Six Linux runs (RX 7900 XTX, RTX 4090, ROG Ally on Bazzite, and
Arc A770 LE) pair with a Windows run of the same profile, and the Steam Deck runs
are Linux (SteamOS). The three laptop entries use the temporary `_generic` ID for an
unknown laptop model. All fixture records are marked
`synthetic: true`, and every community fixture is `submitted_by: MattyStacks`.

API schema `0.5` adds `submitted_by` to every generated run record and a
`contributors` list (unique GitHub usernames) to every grouped summary.
Schema `0.6` nests the catalog hardware specs. Schema `0.7` switches to
product-level IDs and renames the vendor field to `gpu_vendor` (in
`identity.gpu_vendor` and on every run record). Schema `0.8` adds `base`,
`identity.board_partner`, `skus`, and `platform` to catalog entries, which
are always returned already merged with their reference. Schema `0.9` adds
`sources`. Schema `0.10` adds `os` (a grouping key) and the OS detail fields
(`os_detail`, `distro`, `kernel`, `mesa`, `proton`, ...) to every run record
and `implementations` entry. The
dashboard's **Get the data as JSON** panel lists each endpoint with Open and
Copy URL actions; copied URLs are built from the page's own location, so they
stay correct on GitHub Pages or a custom domain.

## Community contributions

Copy [templates/community_submission.yaml](templates/community_submission.yaml)
to the folder matching its `gpu_id`, for example:

```text
data/community/rtx_4090_24gb_fe/result_20261003_cyberpunk_mattystacks.yaml
```

Every community file sets `submitted_by` to the GitHub username of the person
opening the pull request, and the file name ends with that username
(compared case-insensitively; lowercase is conventional). For a second file
with the same date and game, add a number before the username, such as
`result_20261003_cyberpunk_2_mattystacks.yaml`.

Pull requests run three separate checks so it's clear which part failed:
**Catalog entries** (`validate.py catalog`), **Benchmark results**
(`validate.py results`), and **Build and tests**. The result check covers
official and community `result_*.yaml` and `result_*.yml` files. It enforces
the game benchmark contract, requires frame generation to be disabled, checks
catalog/folder identity and the `submitted_by`/file-name match, and compares
matching game runs with official baselines. Every problem is reported at once
with a rule name that links to its explanation. See
[docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) and
[data/gpus/README.md](data/gpus/README.md) for the complete rules.

## Local development

```powershell
python -m pip install pyyaml numpy
python scripts/validate.py            # or: validate.py catalog / validate.py results
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000>.

Use `scripts/parse.py` to convert PresentMon or MangoHud CSV data directly
into `data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml`
(it adds `_2`, `_3`, ... before the username instead of overwriting). It
rejects IDs that aren't in the catalog and takes the form factor from the
catalog entry:

```powershell
python scripts/parse.py capture.csv --gpu-id rtx_4090_24gb_fe --game "Cyberpunk 2077" --submitted-by MattyStacks --os windows
```

`--os` is `windows` or `linux` (with an optional `--os-detail`). Without it, a
MangoHud capture defaults to `linux` and a PresentMon capture to `windows`. The
OS is written under `system:`.

## Site and deployment

`site/index.html` fetches the generated dashboard and GPU catalog JSON with
relative paths, so
the site works under any host or custom domain. Site icons live in
`site/favicons/`; the SVG favicon follows the dashboard's light/dark toggle. Links to the GitHub repository,
contributing guide, and issues are absolute and appear in the header and
footer. The workflow in
[.github/workflows/build.yml](.github/workflows/build.yml) validates the data,
rebuilds `site/api/`, and deploys the site whenever `main` changes. Do not commit generated API
files unless repository policy changes.

For the architecture and maintenance checklist, see
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md). Contributor setup and PR
requirements are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT Code, CC0 Data
