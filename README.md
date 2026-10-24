# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive
graph. Every number comes from a small, reviewable YAML file in this
repository, and the site is a static dashboard built from them: no backend,
no database.

**[Dashboard](https://opengpubenchmarks.com)** ·
**[Blog](https://opengpubenchmarks.com/blog/)** ·
**[Submit a result](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml)** ·
**[JSON API](#use-the-data)** ·
**[Changelog](CHANGELOG.md)**

The canonical site is <https://opengpubenchmarks.com> (Cloudflare Pages),
mirrored on [GitHub Pages](https://mattystacks.github.io/open-gpu-benchmarks/).
The blog has posts, guides, and reviews built on the same data.

Current version: `v1.8.0.0`, which adds a GitHub Sponsors button. v1.7.0.0
added 309 reference GPU specs from NVIDIA, AMD, and Intel's own spec pages, with new fields for ray tracing, encoders, API
versions, and each vendor's feature list. v1.6.0.0 records system RAM as
numbers in the API: `memory_gb`, plus optional `memory_type` (`DDR5-6400`) and
`memory_channels`. v1.5.0.0 added `creator` and a typed `license` to the Dataset structured data
for Google Search. v1.4.0.0 reorganized this
README into a short overview, and v1.3.0.0 moved the benchmark data to CC BY 4.0 and added the
benchmark issue form. See [CHANGELOG.md](CHANGELOG.md) for every release and
[docs/TODO.md](docs/TODO.md) for planned work.

## What's on the dashboard

Published so far: 1 catalog GPU (the GeForce RTX 5080 Founders Edition), 309
reference GPU specs ready for products to build on, 34
official runs, no community runs, and 30 dashboard summaries, all Cyberpunk
2077 built-in benchmark runs on Windows.

- **One bar per product.** A product is an exact card, laptop GPU, handheld, or
  iGPU, memory size included. Different memory sizes and board partners are
  different products, so their results are never averaged together.
- **Like with like.** Desktop and laptop GPUs never share a summary, and
  Windows and Linux runs are charted separately (Linux bars are striped).
- **Native or upscaled, clearly labelled.** Some presets switch an upscaler
  on, so every bar names it (`DLSS Auto`, `FSR 2.1 Quality`) or says `Native`.
  Frame generation is never allowed.
- **Official and community runs.** Official runs are maintainer-verified.
  Community runs show what evidence backs them, or "Unverified" when there's
  none, and a run far from the official average is rejected.
- **Specs and sources.** The table lists each product's hardware specs; expand
  a row for the pages they came from.

## How it works

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml         hardware catalog, one file per product
data/games.yaml                                        game registry
data/official/<gpu_id>/result_YYYYMMDD_<game_id>.yaml  maintainer runs
data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml community runs (+ optional raw/ evidence)
                    ↓
python scripts/build.py      runs every check first, writes nothing if one fails
                    ↓
site/api/v1/**.json          the JSON API the dashboard reads
site/benchmarks/, llms.txt   JavaScript-free copies for search engines and AI tools
```

Each result folder is named by a catalog ID, and each result file holds one
day's runs as a `result:` list. The build groups runs by product, game,
resolution, preset, upscaler, and OS. Generated output is gitignored and
rebuilt in CI.

- How products are named and what a catalog file holds:
  [data/gpus/README.md](data/gpus/README.md).
- The full data contract, API fields, and schema history:
  [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md).

## Use the data

Every file is plain JSON, served from the dashboard's own host. The
dashboard's **Get the data as JSON** panel lists them with Open and Copy URL
buttons.

| Endpoint | What's in it |
| -------- | ------------ |
| [`api/v1/dashboard.json`](https://opengpubenchmarks.com/api/v1/dashboard.json) | The grouped summaries, games, and picks the dashboard charts |
| [`api/v1/gpus.json`](https://opengpubenchmarks.com/api/v1/gpus.json) | The master file: every catalog GPU with its specs, statistics, and links to its summaries |
| `api/v1/official/<gpu_id>/summary.json`, `api/v1/community/<gpu_id>/summary.json` | One product's runs, grouped summaries, evidence, and exact machine details |
| `api/v1/official.json`, `api/v1/community.json` | Every run record, one file each |
| [`api/v1/games.json`](https://opengpubenchmarks.com/api/v1/games.json) | The game registry |
| [`benchmarks/`](https://opengpubenchmarks.com/benchmarks/), [`llms.txt`](https://opengpubenchmarks.com/llms.txt), [`llms-full.txt`](https://opengpubenchmarks.com/llms-full.txt) | The same summaries as plain HTML and text |

Distro, kernel, Mesa, and Proton are recorded on every Linux run but aren't
charted. To compare them, download the run files and chart them yourself.

The data is CC BY 4.0: use it for anything, AI training included, and credit
"Data from Open GPU Benchmarks" with a link. See [License](#license).

## Contribute a result

**The easiest way is a
[Benchmark result issue](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml).**
Fill in the form and a bot writes the result file, runs the checks, and opens
a pull request for a maintainer to approve. If something needs fixing, it
replies on the issue.

For bulk uploads, raw captures, or scripted imports, open a pull request:
copy [templates/community_submission.yaml](templates/community_submission.yaml)
to `data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml`, fill it in, and
run the checks below. Submissions are anonymous by default, and the result
doesn't have to be yours: a number from a video or review starts from
[templates/community_found_result.yaml](templates/community_found_result.yaml)
and links its source.

Pull requests run four checks: **Catalog entries**, **Benchmark results**,
**Build and tests**, and **Blog**. Every failure names a rule that links to its
explanation.

| To...                                         | Read |
| --------------------------------------------- | ---- |
| Submit a result step by step, with examples   | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Look up a submission rule or a failed result check | [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) |
| Name a result folder and file                 | [data/community/README.md](data/community/README.md) |
| Add a card, laptop, or handheld, or decode a catalog check | [data/gpus/README.md](data/gpus/README.md) |
| Import Cyberpunk 2077 benchmark runs          | [docs/CYBERPUNK_BENCHMARK.md](docs/CYBERPUNK_BENCHMARK.md) |
| Write a blog post, guide, or review           | [content/README.md](content/README.md) |

## Local development

### Set up

You need Python 3.11+. Install the dependencies from
[requirements.txt](requirements.txt) into a project virtual environment
(`.venv`, gitignored), not your global Python.

Windows (PowerShell):

```powershell
python -m venv .venv                     # once
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS, Linux, or WSL:

```bash
python3 -m venv .venv                    # once
source .venv/bin/activate                # use source, not ./ or bash
python -m pip install -r requirements.txt
```

- On Ubuntu and WSL, if `python3 -m venv` says `ensurepip` is missing, run
  `sudo apt install python3-venv` first.
- If PowerShell refuses to run `Activate.ps1`, run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- Your prompt starts with `(.venv)` when it's active. If your prompt theme
  hides it, `which python` should end in `.venv/bin/python`.
- In a new terminal, only re-run the activate line. Re-install only when
  `requirements.txt` changes. Run `deactivate` to leave, or delete `.venv` to
  start over.

### Check, build, and preview

```bash
python scripts/validate.py               # or: validate.py catalog / validate.py results
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts/checks.py scripts/build.py scripts/validate.py scripts/parse.py scripts/import_cyberpunk.py scripts/issue_to_result.py scripts/test_build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000>, and press `Ctrl+C` to stop the server.

The published data is small, so to see the dashboard with every feature in
use, build the synthetic test fixtures instead. Run `python scripts/build.py`
again afterwards to go back to the real data:

```bash
python scripts/build.py --data-dir tests/fixtures/data
```

### Import captures

[`scripts/parse.py`](scripts/parse.py) turns a PresentMon or MangoHud CSV into
a community result file. It never overwrites (it adds `_2`, `_3`, ...), and it
rejects IDs that aren't in the catalog. `--os` defaults to `linux` for
MangoHud and `windows` for PresentMon:

```bash
python scripts/parse.py capture.csv --gpu-id rtx_5080_16gb_fe --game-id cyberpunk_2077 --os windows
```

[`scripts/import_cyberpunk.py`](scripts/import_cyberpunk.py) reads every run in
Cyberpunk 2077's `benchmarkResults` folder and writes one file per day. Run it
again later and it adds only the new runs. See
[docs/CYBERPUNK_BENCHMARK.md](docs/CYBERPUNK_BENCHMARK.md):

```bash
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe
```

### Blog

The blog (`/blog/`) is an [Astro](https://astro.build) project in `blog/` that
renders posts from `content/posts/`. It needs Node 22.12+ and builds after
`build.py`, because its charts read `site/api/v1/`:

```bash
npm --prefix blog ci                     # once, or after blog/package-lock.json changes
npm --prefix blog run build              # writes site/blog/, served by the http.server above
npm --prefix blog run dev                # live preview at http://localhost:4321/blog/, drafts included
```

## Repository layout

```text
data/                 the published data (CC BY 4.0): catalog, games, picks, results
  gpus/               hardware catalog, one file per product, plus shared reference specs
  official/           maintainer runs, one folder per product
  community/          community runs, one folder per product
scripts/              checks, build, validation, importers (checks.py holds every rule)
site/                 the dashboard (index.html), license page, icons, crawler rules
blog/                 the Astro blog project
content/posts/        blog posts, guides, and reviews
templates/            starting points for result files and catalog entries
tests/fixtures/       synthetic test data and issue bodies (never deployed)
docs/                 contributor guides, the project handoff, and the backlog
.github/              CI workflows, the benchmark issue form, CODEOWNERS, FUNDING.yml
```

## Deployment

[build.yml](.github/workflows/build.yml) validates the data, rebuilds the
site, and deploys it to Cloudflare Pages and GitHub Pages on every push to
`main`. [preview.yml](.github/workflows/preview.yml) deploys a Cloudflare
preview for the repository owner's own pull requests only, never for the
bot's `benchmark/*` pull requests.

The site loads its data with relative paths, so it works on any host. Every
host names `https://opengpubenchmarks.com/` as canonical, and `robots.txt`
welcomes every crawler, AI crawlers included. Architecture, the bot App
setup, and the maintenance checklist are in
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md).

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
