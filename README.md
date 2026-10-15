# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive
graph. The site is a static dashboard built from reviewable YAML, live at
<https://opengpubenchmarks.com> (Cloudflare Pages, canonical) and mirrored on
[GitHub Pages](https://mattystacks.github.io/open-gpu-benchmarks/).

Posts, guides, and reviews built on the same data live at
<https://opengpubenchmarks.com/blog/>.

Current version: `v1.3.0.0`: the benchmark data is now CC BY 4.0 (use it for
anything, AI training included, with a link back; see the
[license page](https://opengpubenchmarks.com/license/)), and results can be
submitted through a GitHub issue form. v1.2.0.0 added a game registry,
[data/games.yaml](data/games.yaml), that every result names by `game_id`, plus
a required date on every result file. v1.1.0.0 added the blog, guides, and reviews section, and four-part
`MAJOR.MINOR.DATA.POST` versions. v1.0.0 brought the first
published results (Cyberpunk 2077 on the GeForce RTX 5080 Founders Edition)
and a Cyberpunk 2077 benchmark importer. See [CHANGELOG.md](CHANGELOG.md) for what changed in each version, and
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
data/official/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
data/community/<gpu_id>/raw/**                         optional raw evidence
data/games.yaml                                        game registry: game_id -> name, type, year
                    ↓
python scripts/build.py
                    ↓
site/api/v1/gpus.json                                  GPU-rooted master API
site/api/v1/official/<gpu_id>/summary.json             generated GPU summary
site/api/v1/community/<gpu_id>/summary.json            generated GPU summary
site/api/v1/dashboard.json                             game-FPS dashboard data
site/api/v1/games.json                                 the game registry as JSON
```

Each result file describes one benchmark capture and contains a non-empty
`result` YAML list. Each dashed list item is one resolution/preset result; the
dash is required so YAML retains multiple profiles rather than overwriting a
duplicate key. There are no checked-in source summaries. The build runs every
check in `scripts/checks.py` first and stops without writing anything if any
fail. It then expands every list item and derives game summaries by product
ID, form factor, known power profile, game, resolution, `graphics_preset`, and
OS. It never groups desktop and laptop GPUs together, or Windows and Linux runs.

Many graphics presets turn an upscaler on by themselves, so one GPU can show
a native and an upscaled result for the same preset. Every chart label carries
a pill naming the upscaler (`FSR 2.1 Quality`, `DLSS Auto`) or `Native`,
colored by maker (DLSS green, FSR red, XeSS blue, native gray), the
table has a Settings column, and Native/Upscaled filter chips hide either kind.

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

Published data: 1 catalog GPU (the GeForce RTX 5080 Founders Edition), 34
official runs, no community runs, and 30 dashboard summaries, all Cyberpunk
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
`implementations`. Schema `0.13` adds `picks` to `dashboard.json`: the
featured GPU cards from [data/picks.yaml](data/picks.yaml), one per GPU maker,
each with `slot`, `name`, optional `gpu_id`, `note`, `label`, `vram_gb`,
`tdp_w`, `form_factor`, and `links` (`retailer`, `retailer_name`, `url`), and
`metadata.license` (`CC0-1.0`) to every API file. Schema `0.14` adds `date`
(the result file's required `YYYY-MM-DD`) and `time` (the run's optional local
`HH:MM[:SS]`, `""` when not set) to every run record; neither groups runs.
Schema `0.15` adds the game registry: results name their game with `game_id`
from [data/games.yaml](data/games.yaml), every run record carries `game_id`,
`game` (the registry name), `game_type`, and `game_year`, summaries group by
`game_id`, `dashboard.json` `games` becomes a list of `{id, name, type, year}`
objects, and `games.json` publishes the whole registry. The
dashboard's **Get the data as JSON** panel lists each endpoint with Open and
Copy URL actions; copied URLs are built from the page's own location, so they
stay correct on GitHub Pages or a custom domain.

Schema `0.16` changes the data license to CC BY 4.0 (`metadata.license` is
`CC-BY-4.0`) and puts two blocks first in every API file: `_license` (`name`,
`url`, `attribution`, `attribution_url`, `ai_training_permitted`, `terms`) and
`_source` (the file's canonical `url` and `generated_at`), so a copied
response still says where it came from.

## Community contributions

The easiest way to add a result is a
[Benchmark result issue](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml).
Fill in the form and a bot ([`scripts/issue_to_result.py`](scripts/issue_to_result.py)
via [`benchmark-issue.yml`](.github/workflows/benchmark-issue.yml)) writes the
result file, runs the checks, and opens a pull request for a maintainer (a
[code owner](.github/CODEOWNERS)) to approve. If something needs fixing, it
replies on the issue. See
[Submit through an issue](docs/COMMUNITY_SUBMISSIONS.md#submit-through-an-issue).

For bulk or scripted uploads, open a pull request instead. Copy
[templates/community_submission.yaml](templates/community_submission.yaml)
to the folder matching its `gpu_id`, for example:

```text
data/community/rtx_5080_16gb_fe/result_20261003_cyberpunk_2077.yaml
```

The game is named by its `game_id` from [data/games.yaml](data/games.yaml). A
new game is added there in the same pull request: `id`, `name`, `type`, and
`year`, plus `steam_appid` or `url` when the game has one.

Submissions are anonymous by default. A run needs only the product, game,
resolution, preset, average FPS, `system.os`, and `proof.method`; your
username (`submitted_by`), machine details, and evidence are optional. For a
second file with the same date and game, add a number, such as
`result_20261003_cyberpunk_2077_2.yaml`. The result doesn't have to be yours: to add
one from a video or review, start from
[templates/community_found_result.yaml](templates/community_found_result.yaml)
and link where you found it in `credit.source_url`. Upscaling is off unless the
graphics preset turns it on (`preset_upscaling: true`).

Pull requests run four separate checks so it's clear which part failed:
**Catalog entries** (`validate.py catalog`), **Benchmark results**
(`validate.py results`), **Build and tests**, and **Blog** (the Astro build). The result check covers
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

On Windows (PowerShell):

```powershell
python -m venv .venv                     # once, creates the .venv folder
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS, Linux, or WSL:

```bash
python3 -m venv .venv                    # once, creates the .venv folder
source .venv/bin/activate                # run it with source, not ./ or bash
python -m pip install -r requirements.txt
```

On Ubuntu and WSL, if `python3 -m venv` says `ensurepip` is missing, run
`sudo apt install python3-venv` first. If your prompt doesn't show `(.venv)`
(some prompt themes hide it), `which python` should print a path ending in
`.venv/bin/python`.

With the environment active (your prompt starts with `(.venv)`):

```powershell
python scripts/validate.py            # or: validate.py catalog / validate.py results
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts/checks.py scripts/build.py scripts/validate.py scripts/parse.py scripts/import_cyberpunk.py scripts/issue_to_result.py scripts/test_build.py
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

### Blog

The blog (`/blog/`) is an [Astro](https://astro.build) project in `blog/`
that renders posts from `content/posts/`. It needs Node 22.12+ and builds
after `build.py`, because its charts read `site/api/v1/`:

```powershell
npm --prefix blog ci                     # once, or after blog/package-lock.json changes
npm --prefix blog run build              # writes site/blog/, served by the http.server above
npm --prefix blog run dev                # live preview at http://localhost:4321/blog/, drafts included
```

How to write a post, the frontmatter fields, charts, and the affiliate rules
are in [content/README.md](content/README.md).

To leave the virtual environment, run `deactivate` (same on every OS) or close
the terminal. In a new terminal, only re-run the activate line; the install
step is needed again only when `requirements.txt` changes. To remove the
environment completely, delete the `.venv` folder. If PowerShell refuses to
run `Activate.ps1`, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Use `scripts/parse.py` to convert PresentMon or MangoHud CSV data directly
into `data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml` (it adds `_2`,
`_3`, ... instead of overwriting; `--submitted-by` is optional). It
rejects IDs that aren't in the catalog and takes the form factor from the
catalog entry:

```powershell
python scripts/parse.py capture.csv --gpu-id rtx_5080_16gb_fe --game-id cyberpunk_2077 --os windows
```

`--os` is `windows` or `linux` (with an optional `--os-detail`). Without it, a
MangoHud capture defaults to `linux` and a PresentMon capture to `windows`. The
OS is written under `system:`.

Ran Cyberpunk 2077's built-in benchmark? `scripts/import_cyberpunk.py` reads
the `summary.json` and `frames.csv` of every run in the game's
`benchmarkResults` folder and writes one result file per day, with one
`result` item per run. The average and 1% low come from the frame times in
`frames.csv`. Run it again later and it adds only the new runs, and gives
earlier runs without a 1% low one from their `frames.csv`. See
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
deploys a Cloudflare preview for the repository owner's own pull requests only,
never for the bot's `benchmark/*` pull requests.
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

- **Code** (`scripts/`, `site/`, `blog/`, `templates/`, workflows) is under
  the [MIT license](LICENSE).
- **Benchmark data** is under [CC BY 4.0](data/LICENSE) with reasonable
  attribution. That covers everything in `data/` (the catalog, official and
  community results, raw captures) and everything generated from it (the
  dashboard data, the JSON API, `benchmarks/`, and `llms*.txt`). Use it for
  anything, commercial or not, including AI training. Sites, apps, and
  articles that use it credit "Data from Open GPU Benchmarks" with a link to
  <https://opengpubenchmarks.com>; a chart image or video can use a text
  credit, and AI models credit it in their model card, not in every answer.
  The [license page](https://opengpubenchmarks.com/license/) has the details.
  Submitting a result means agreeing to this; see
  [Your results become public data](docs/COMMUNITY_SUBMISSIONS.md#your-results-become-public-data).
  Data published before the switch was CC0, and copies made then keep those
  terms.
- **Blog posts, guides, and reviews** in `content/` stay the author's
  copyright, all rights reserved, and aren't covered by either license. A
  post marked AI-generated (`ai_generated: true`) claims no copyright in its
  text. Charts in posts are drawn from the CC BY 4.0 data.
- GPU and company names are trademarks of their owners.
