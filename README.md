# Open GPU Benchmarks

Open GPU Benchmarks compares desktop, laptop, handheld, and integrated GPUs in
one interactive chart. Every number comes from a small YAML file in this repository
that anyone can review. The site is a static dashboard built from those files,
with no backend and no database. The data is free to reuse under CC BY 4.0.

**[Dashboard](https://opengpubenchmarks.com)** ·
**[Blog](https://opengpubenchmarks.com/blog/)** ·
**[Submit a result](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml)** ·
**[JSON API](#use-the-data)** ·
**[Changelog](CHANGELOG.md)**

The site lives at <https://opengpubenchmarks.com>, with a mirror on
[GitHub Pages](https://mattystacks.github.io/open-gpu-benchmarks/). The blog
has posts, guides, and reviews built on the same data.

## How it works

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml         hardware catalog, one file per product
data/games.yaml                                        the games and benchmarks results can use
data/testbenches.yaml                                  the maintainer's test systems
data/official/<gpu_id>/result_YYYYMMDD_<game_id>.yaml  maintainer runs
data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml community runs
                    ↓
python scripts/build.py      checks every file, then groups the runs into summaries
                    ↓
site/api/v1/**.json          the JSON API the dashboard reads
```

Every change goes through a pull request, and the checks run on all of them, so a bad file
never reaches the site. The dashboard follows a few rules so its comparisons are fair:

- **One bar per product.** A product is an exact card, laptop GPU, handheld, or
  iGPU, memory size included. Different memory sizes and board partners are
  different products, and their results are never averaged together.
- **Like with like.** Desktop and laptop GPUs never share a summary. Windows and
  Linux runs are charted separately, and so are the maintainer's DDR5, DDR4,
  and DDR3 test systems.
- **Native or upscaled, clearly labelled.** Every bar names its upscaler or
  says `Native`. Frame generation is never allowed.
- **Official and community runs.** The maintainer verifies official runs.
  Community runs show what evidence backs them, or "Unverified" if there's none, and
  a run far from the official average is rejected.
- **Specs with sources.** Each product's specs come from its maker's spec
  page, and the dashboard links to the pages they came from.

The data rules and the API fields are in
[docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) and
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md).

## Use the data

Every file is plain JSON, served from the site. On the dashboard, the
**Get the data as JSON** panel lists them all.

| Endpoint | What's in it |
| -------- | ------------ |
| [`api/v1/dashboard.json`](https://opengpubenchmarks.com/api/v1/dashboard.json) | The grouped summaries the dashboard charts |
| [`api/v1/gpus.json`](https://opengpubenchmarks.com/api/v1/gpus.json) | Every catalog GPU with its specs, statistics, and links to its summaries |
| `api/v1/official/<gpu_id>/summary.json`, `api/v1/community/<gpu_id>/summary.json` | One product's runs, summaries, evidence, and exact machine details |
| `api/v1/official.json`, `api/v1/community.json` | Every run record |
| [`api/v1/games.json`](https://opengpubenchmarks.com/api/v1/games.json), [`api/v1/testbenches.json`](https://opengpubenchmarks.com/api/v1/testbenches.json) | The game registry and the test systems |
| [`benchmarks/`](https://opengpubenchmarks.com/benchmarks/), [`llms.txt`](https://opengpubenchmarks.com/llms.txt), [`llms-full.txt`](https://opengpubenchmarks.com/llms-full.txt) | The same summaries as plain HTML and text |

Every run keeps details the charts don't group by, such as the Linux distro,
kernel, and Proton version. Download the run files to compare those yourself.

You can use the data for anything, commercial or not, including AI training.
Credit "Data from Open GPU Benchmarks" with a link to
<https://opengpubenchmarks.com>. The [license page](https://opengpubenchmarks.com/license/)
has the details.

## Contribute

**Submit a result.** The easiest way is a
[Benchmark result issue](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml).
Fill in the form, or attach a result file. A bot writes the file, runs the
checks, and opens a pull request for a maintainer to approve. Results are
anonymous by default, and they don't have to be yours: a number from a video
or review counts too, with a link to where you found it.

**Other ways to help:**

| To...                                                     | Read |
| --------------------------------------------------------- | ---- |
| Submit by pull request (bulk uploads, raw captures, importers) | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Look up a submission rule or a failed check               | [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) |
| Ask for a GPU, or add a card, laptop, or handheld         | [Add a GPU issue](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=gpu_request.yml), [data/gpus/README.md](data/gpus/README.md) |
| Import Cyberpunk 2077 benchmark runs                      | [docs/CYBERPUNK_BENCHMARK.md](docs/CYBERPUNK_BENCHMARK.md) |
| Write a blog post, guide, or review                       | [content/README.md](content/README.md) |
| Work on the code or the dashboard                         | [CONTRIBUTING.md](CONTRIBUTING.md#working-on-the-code) |
| See what's planned                                        | [docs/TODO.md](docs/TODO.md) |

Before you open a pull request, run `python scripts/preflight.py`. It runs
every check that CI runs, and each failure says how to fix it. Setup is in
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

- **Code** is under the [MIT license](LICENSE).
- **Benchmark data** (everything in `data/`, and the API and pages built from
  it) is under [CC BY 4.0](data/LICENSE). Submitting a result means agreeing
  to this; see
  [Your results become public data](docs/COMMUNITY_SUBMISSIONS.md#your-results-become-public-data).
  Data published before the switch was CC0, and copies made then keep those terms.
- **Blog posts** in `content/` stay the author's copyright, all rights reserved.
- GPU and company names are trademarks of their owners.
