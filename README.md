# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive
graph. The site is a static dashboard built from reviewable YAML, live at
<https://opengpubenchmarks.com> (Cloudflare Pages, canonical) and mirrored on
[GitHub Pages](https://mattystacks.github.io/open-gpu-benchmarks/).

Current version: `v1.0.0`: the first published results (Cyberpunk 2077 on the GeForce RTX 5080 Founders Edition) and a Cyberpunk 2077 benchmark importer. See [CHANGELOG.md](CHANGELOG.md) for what changed in each version, and
[docs/TODO.md](docs/TODO.md) for planned follow-ups.

## GPU-rooted data flow

`data/gpus/` is the authoritative hardware catalog, one file per product at
`data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. The ID names the exact
product, including its memory size: `rtx_5060_ti_8gb_msi_ventus_2x_oc`,
`rtx_5080_16gb_fe`, `steam_deck_oled_16gb`. Different memory sizes and board
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
data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml
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

Published data: 1 catalog GPU (the GeForce RTX 5080 Founders Edition), 33
official runs, no community runs, and 29 dashboard summaries, all Cyberpunk
2077 built-in benchmark runs on Windows.

`data/` holds only real data, because it's what the site deploys. The synthetic
test data lives in [`tests/fixtures/data/`](tests/fixtures/data/), a
self-contained copy of the same layout with its own catalog snapshot.
`test_build.py` builds it into a temporary folder, never into `site/api/`, and
fails if a `synthetic: true` run ever appears in `data/`. The fixtures hold
11 catalog GPUs, 19 official runs, 12 community runs, and 30 dashboard
summaries. They include a
multi-profile file and two matching Arc A770 LE results that aggregate into one
1080p summary. Six Linux runs (RX 7900 XTX, RTX 4090, ROG Ally on Bazzite, and
Arc A770 LE) pair with a Windows run of the same profile, and the Steam Deck runs
are Linux (SteamOS). The three laptop entries use the temporary `_generic` ID for an
unknown laptop model. All fixture runs are marked
`synthetic: true`. Every community fixture is `submitted_by: MattyStacks`
except the Steam Deck Cyberpunk 2077 run, which is anonymous.

API schema `0.5` adds `submitted_by` to every generated run record and a
`contributors` list (unique GitHub usernames) to every grouped summary.
Schema `0.6` nests the catalog hardware specs. Schema `0.7` switches to
product-level IDs and renames the vendor field to `gpu_vendor` (in
`identity.gpu_vendor` and on every run record). Schema `0.8` adds `base`,
`identity.board_partner`, `skus`, and `platform` to catalog entries, which
are always returned already merged with their reference. Schema `0.9` adds
`sources`. Schema `0.10` adds `os` (a grouping key) and the OS detail fields
(`os_detail`, `distro`, `kernel`, `mesa`, `proton`, ...) to every run record
and `implementations` entry. Schema `0.11` makes `p1_low` optional (it is `null`
on runs and summaries without one) and adds `capture_method`. Schema `0.12`
makes `submitted_by` optional (empty for anonymous runs), adds `upscaling` as a
grouping key (empty when off), adds `none` ("Unverified", community only) and
`maintainer-verified` (official runs with no linked evidence) to `proof_level`,
and
adds `source_url` to each summary `credits` entry and `credit_source_url` to
`implementations`. The
dashboard's **Get the data as JSON** panel lists each endpoint with Open and
Copy URL actions; copied URLs are built from the page's own location, so they
stay correct on GitHub Pages or a custom domain.

## Community contributions

Copy [templates/community_submission.yaml](templates/community_submission.yaml)
to the folder matching its `gpu_id`, for example:

```text
data/community/rtx_5080_16gb_fe/result_20261003_cyberpunk.yaml
```

Submissions are anonymous by default. A run needs only the product, game,
resolution, preset, average FPS, `system.os`, and `proof.method`; your
username (`submitted_by`), machine details, and evidence are optional. For a
second file with the same date and game, add a number, such as
`result_20261003_cyberpunk_2.yaml`. The result doesn't have to be yours: to add
one from a video or review, start from
[templates/community_found_result.yaml](templates/community_found_result.yaml)
and link where you found it in `credit.source_url`. Upscaling is off unless the
graphics preset turns it on (`preset_upscaling: true`).

Pull requests run three separate checks so it's clear which part failed:
**Catalog entries** (`validate.py catalog`), **Benchmark results**
(`validate.py results`), and **Build and tests**. The result check covers
official and community `result_*.yaml` and `result_*.yml` files. It enforces
the game benchmark contract, requires frame generation and upscaling to be
off, checks catalog/folder identity, the file name, and any `submitted_by` or
`credit`, and compares
matching game runs with official baselines. Every problem is reported at once
with a rule name that links to its explanation. See
[docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) and
[data/gpus/README.md](data/gpus/README.md) for the complete rules.

## Local development

You need Python 3.11+. Dependencies live in
[requirements.txt](requirements.txt); install them into a project virtual
environment (`.venv`, already gitignored) rather than your global Python:

```powershell
python -m venv .venv                     # once, creates the .venv folder
.venv\Scripts\Activate.ps1               # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

With the environment active (your prompt starts with `(.venv)`):

```powershell
python scripts/validate.py            # or: validate.py catalog / validate.py results
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\import_cyberpunk.py scripts\test_build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000>. Press `Ctrl+C` to stop the server when you're
done.

To preview the dashboard with the full synthetic test data, build the fixtures
instead (`validate.py` takes the same flag). Run `python scripts/build.py`
again afterwards to go back to the real data:

```powershell
python scripts/build.py --data-dir tests/fixtures/data
```

To leave the virtual environment, run `deactivate` (same on every OS) or close
the terminal. In a new terminal, only re-run the activate line; the install
step is needed again only when `requirements.txt` changes. To remove the
environment completely, delete the `.venv` folder. If PowerShell refuses to
run `Activate.ps1`, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Use `scripts/parse.py` to convert PresentMon or MangoHud CSV data directly
into `data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml` (it adds `_2`,
`_3`, ... instead of overwriting; `--submitted-by` is optional). It
rejects IDs that aren't in the catalog and takes the form factor from the
catalog entry:

```powershell
python scripts/parse.py capture.csv --gpu-id rtx_5080_16gb_fe --game "Cyberpunk 2077" --os windows
```

`--os` is `windows` or `linux` (with an optional `--os-detail`). Without it, a
MangoHud capture defaults to `linux` and a PresentMon capture to `windows`. The
OS is written under `system:`.

Ran Cyberpunk 2077's built-in benchmark? `scripts/import_cyberpunk.py` reads
the `summary.json` of every run in the game's `benchmarkResults` folder and
writes one result file per run, named after the run. Run it again later and it
adds only the new runs. See
[docs/CYBERPUNK_BENCHMARK.md](docs/CYBERPUNK_BENCHMARK.md):

```powershell
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe
```

## Site and deployment

`site/index.html` fetches the generated dashboard and GPU catalog JSON with
relative paths, so
the site works under any host or custom domain. Site icons live in
`site/favicons/`; the SVG favicon follows the dashboard's light/dark toggle. Links to the GitHub repository,
contributing guide, and issues are absolute and appear in the header and
footer. The workflow in
[.github/workflows/build.yml](.github/workflows/build.yml) validates the data,
rebuilds `site/api/`, and deploys the site to both GitHub Pages and Cloudflare
Pages whenever `main` changes. [preview.yml](.github/workflows/preview.yml)
deploys a Cloudflare preview for the repository owner's own pull requests only.
Do not commit generated API files unless repository policy changes.

For search engines and AI tools, every host declares
`https://opengpubenchmarks.com/` as canonical (`build.SITE_URL`), so the
mirrors count as copies of it. `build.py` also writes JavaScript-free copies of
every summary (`benchmarks/index.html`, `llms.txt`, `llms-full.txt`) and
`sitemap.xml` next to `site/api/`. They are gitignored like the API.
`site/robots.txt` allows all crawlers, AI crawlers included. Those absolute
URLs are the only exception to relative links.

For the architecture and maintenance checklist, see
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md). Contributor setup and PR
requirements are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT Code, CC0 Data
