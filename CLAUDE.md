# CLAUDE.md

Guidance for Claude Code working in this repository.

## Every change: update the changelog, the backlog, and the version

These three steps are required, not optional, for every PR an agent or a person
prepares:

1. **[CHANGELOG.md](CHANGELOG.md)** — add a line under `Unreleased` for any change to
   behavior, the data contract, the API schema, the dashboard, the checks, the
   templates, or the contributor workflow. Data-only result submissions are the
   only exception. Don't finish a task with your change missing from the
   changelog.
2. **[docs/TODO.md](docs/TODO.md)** (the backlog) — remove items you completed, and
   add anything you deferred, found broken, or were asked to do later.
3. **Bump the version** — every PR except a data-only result submission
   increments `RELEASE_VERSION` in [scripts/build.py](scripts/build.py) by the
   biggest kind of change it contains: MAJOR (breaking data contract or API),
   MINOR (any code, check, dashboard, docs-workflow, or license change), DATA
   (newly published runs), or POST (a new or updated blog post). Reset the
   parts to its right. Rename `Unreleased` in `CHANGELOG.md` to
   `## <version> - <date>`, add a fresh empty `Unreleased` above it, and update
   the current-version references and feature summary in `README.md`,
   `docs/COPILOT_HANDOFF.md`, and `CLAUDE.md`. `test_build.py` fails if
   `RELEASE_VERSION` doesn't match the newest changelog heading. Data-only
   submissions (including bot PRs from benchmark issues) are batched into a
   later DATA bump by a maintainer.

## Branching

Always create a new branch from an up-to-date `main` (`git checkout main && git pull`, then
`git checkout -b <type>/<name>`). Never stack a branch on another unmerged
feature branch, unless the user explicitly asks for it. The usual workflow:
commit everything, push, and open a PR into `main`; one topic per branch.

## Read these first

Before changing the data schema, build logic, validation, the dashboard, or the
docs, read:

1. [.github/copilot-instructions.md](.github/copilot-instructions.md) — the
   short agent rulebook (data rules, version/release housekeeping). Treat it as
   binding for Claude too, not just Copilot.
2. [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md) — architecture, the data
   contract, current fixture counts, deployment, and the maintenance checklist.
   This is the project's living state document.
3. [README.md](README.md) — public overview: what the dashboard shows, the
   JSON endpoints, where to contribute, and local dev. Keep it short; details
   belong in the documents below.
4. [CONTRIBUTING.md](CONTRIBUTING.md) and
   [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) — contributor
   setup and the full submission/review rules.
5. [data/community/README.md](data/community/README.md) — folder-level rules for
   community result files. [data/gpus/README.md](data/gpus/README.md) — catalog
   layout, ID grammar, field reference, and an explanation of every check rule.
6. [CHANGELOG.md](CHANGELOG.md) — high-level version history. Add an entry under
   `Unreleased` for every user-visible, schema, or workflow change.
7. [docs/TODO.md](docs/TODO.md) — the backlog of deferred work. Do not pull
   items from it into a session unless asked; add new deferred ideas there
   instead, and remove items when they're done.
8. [AGENTS.md](AGENTS.md) — the tool-neutral entry point for other AI agents.
   Keep it in step with this file.
9. [content/README.md](content/README.md) — before writing or editing a blog
   post, guide, or review: frontmatter, components, and the AI-cleanup rules.

The first five documents overlap on purpose. When a rule changes, it has to change
in every file that states it, or the next session gets contradictory context.

## What this project is

A static GitHub Pages dashboard that compares desktop, laptop, handheld, and
integrated GPUs from reviewable YAML. No backend, no database, no build
toolchain beyond Python.

- Repo: `MattyStacks/open-gpu-benchmarks`, default branch `main`
- Site: <https://opengpubenchmarks.com> (Cloudflare Pages, canonical); mirror
  <https://mattystacks.github.io/open-gpu-benchmarks/> (GitHub Pages)
- Current development version: `v1.10.0.0` (`RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py), with `SCHEMA_VERSION` alongside it).
  Versions are `MAJOR.MINOR.DATA.POST`, always four parts; see the
  Versioning section of [CHANGELOG.md](CHANGELOG.md)

### Layout

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml
                                   authoritative catalog, one file per product
data/gpus/reference/<gpu_vendor>/<ref_id>.yaml
                                   shared chip specs products inherit via base:
data/gpus/README.md                catalog rules, ID grammar, every check explained
LICENSE                            MIT, for the code
data/LICENSE                       CC BY 4.0 (+ reasonable-attribution header), for all benchmark data
.github/pull_request_template.md   PR checklist, including agreeing to CC BY 4.0 for results
data/reviews.yaml                  optional review links (still in the API; no longer shown)
data/games.yaml                    game registry: every game_id a result may use, with
                                   name, type, year, and optional store IDs (game-* rules)
data/testbenches.yaml              test bench registry: the systems official desktop runs
                                   name with testbench_id (testbench-* rules)
data/picks.yaml                    featured GPU picks: one dashboard card per GPU maker
                                   with affiliate store links (pick-* rules)
data/official/<gpu_id>/result_*.yaml
data/community/<gpu_id>/result_*.yaml
data/community/<gpu_id>/raw/**     optional raw capture evidence
tests/fixtures/data/               synthetic test data (same layout, never deployed)
scripts/checks.py                  every catalog and result rule, written once
scripts/build.py                   YAML source -> site/api/v1/** JSON (runs checks first; --data-dir)
scripts/validate.py                PR validator: validate.py [catalog|results] [--data-dir]
scripts/parse.py                   PresentMon/MangoHud CSV -> result YAML
scripts/import_cyberpunk.py        Cyberpunk 2077 benchmarkResults/*/summary.json + frames.csv -> result YAML
scripts/issue_to_result.py         "Benchmark result" issue body -> community result YAML + PR text
                                   (run by benchmark-issue.yml; tests use tests/fixtures/issues/)
                                   (one file per day; re-runs add only new runs)
scripts/test_build.py              build smoke test (runs in both CI workflows)
site/index.html                    the whole dashboard, single file
site/favicons/                     site icons (favicon.svg is primary, theme-aware)
site/robots.txt, site/_headers     crawler rules (AI allowed) and Cloudflare headers
site/license/index.html            the public license page (data CC BY 4.0, posts the author's)
site/benchmarks/, llms.txt,       generated JS-free summary pages + sitemap.xml
  llms-full.txt, sitemap.xml       (gitignored, written by build.py)
content/posts/<slug>/index.md(x)  blog posts, guides, and reviews (+ their images)
content/README.md                  how to write a post: frontmatter, components, AI-cleanup rules
blog/                              Astro project that renders content/ into site/blog/
                                   (gitignored output; schema in blog/src/content.config.ts)
blog/src/styles/tokens.css         verbatim copy of the dashboard's color tokens
templates/                         starting points for runs (incl. community_found_result.yaml) and catalog entries
requirements.txt                   Python dependencies (pyyaml, numpy); CI and .venv use it
.venv/                             local virtual environment (gitignored, never committed)
docs/CYBERPUNK_BENCHMARK.md        user guide for the Cyberpunk 2077 importer
CHANGELOG.md                       high-level version history (update with every change)
docs/TODO.md                       backlog: deferred work (update with every change)
AGENTS.md                          tool-neutral agent entry point (keep in step with this file)
.github/workflows/build.yml        builds site/api and deploys GitHub Pages + Cloudflare on main
.github/workflows/preview.yml      Cloudflare PR previews, owner's own PRs only (never benchmark/*)
.github/workflows/benchmark-issue.yml
                                   benchmark issue -> result file -> bot PR (GitHub App token)
.github/ISSUE_TEMPLATE/benchmark.yml
                                   the "Benchmark result" issue form (applies the benchmark label)
.github/CODEOWNERS                 maintainers; a code owner's approval is required to merge
.github/FUNDING.yml                GitHub Sponsors button (github: MattyStacks)
.github/workflows/validate.yml     four PR checks: Catalog entries, Benchmark results,
                                   Build and tests, Blog
```

Generated `site/api/` output is gitignored and recreated in CI. Do not commit it
unless repository policy changes.

### Non-obvious rules that bite

- `data/` holds only real data, because it's what deploys. Synthetic test runs
  live in `tests/fixtures/data/` (same layout, its own catalog snapshot);
  `test_build.py` builds them into a temp folder, never `site/api/`, and fails
  if a `synthetic: true` run appears in `data/`. Preview them with
  `python scripts/build.py --data-dir tests/fixtures/data`.
- Source files use `graphics_preset`. Never add a `settings` fallback.
- `result:` is always a YAML list; every resolution/preset profile needs its
  leading `-`. A duplicated `result:` key silently drops data.
- Desktop and laptop GPU records never share a summary group.
- Official desktop runs name their test bench with a top-level `testbench_id`,
  an ID from `data/testbenches.yaml` (`checks.load_testbenches()`, rules
  `testbench-*`, `result-testbench-id`, `result-unknown-testbench`,
  `result-testbench-community`, and the `result-testbench-mismatch`
  warning). A bench is labeled by the DDR type in its `memory_type`
  ("DDR5 Bench", "DDR4 Bench", "DDR3 Bench"), so a DDR6 system needs no code
  change; there is no generation field. Exactly one bench is `primary`. The
  bench is a grouping key, so one GPU on two benches is two bars; `counts_as`
  folds a bench into another with the same DDR type. Laptops, handhelds,
  iGPUs, and every community file leave it out. The community outlier
  baseline is the primary bench only. The dashboard's "Platform" chips show
  one chip per DDR type, newest first, and every chip starts on.
- Every game run names its game with `game_id`, an ID from
  `data/games.yaml` (`checks.load_games()`, rules `game-*`,
  `result-game-id`, `result-unknown-game`). The registry supplies the
  display name, `type` (`game`, `synthetic`, or `engine_demo`), and `year`,
  all required. `steam_appid`, `igdb_id`, and `url` are optional, because
  not every game is on Steam or has a page, but fill them in whenever the
  game has one, and never guess them. `game_id` is the grouping key. A
  remaster, edition, or different test (Steel Nomad vs Steel Nomad Light)
  gets its own ID; a patch goes in `version`. The old free-text `game:` key
  is an error. A result for a game that isn't registered adds its registry
  entry in the same change.
- Game runs require `system.os`: `windows` or `linux`, lowercase. The OS is a
  grouping key, so Windows and Linux runs are never averaged together; the
  distro, kernel, Mesa, and Proton are per-run detail fields, never grouping
  keys or extra chart bars. Linux-only fields on a windows run (or the
  reverse) are errors. Per-distro comparisons are DIY from the JSON.
- System RAM is numeric: `system.memory_gb` (a number of GB, never `"32 GB"`),
  plus optional `memory_type` (`DDR5-6400`: type, dash, MT/s) and
  `memory_channels` (a whole number: 1 single, 2 dual, 4 quad, 8 on servers).
  All three are optional, a missing one is never reported, and none of them
  group runs or appear on charts. The old `memory`/`ram` keys fail
  `result-system-memory`.
- `frame_generation: false` is required for comparable game runs.
- `avg_fps` is required; `p1_low` is optional (3DMark and in-game benchmarks
  report none) and is `null` in the API when missing. `proof.method` is
  required on every game run and says which tool captured it
  (`checks.PROOF_METHODS`: PresentMon, CapFrameX, FrameView, MSI Afterburner,
  AMD Adrenalin, MangoHud, OCAT, in-game benchmark, synthetic benchmark, or
  other); PresentMon is the recommended default and the method is never a
  grouping key. Frame-time tools (`checks.P1_LOW_METHODS`) must include
  `p1_low` (`result-p1-low-required`); Adrenalin and `other` only warn, and
  an `in_game_benchmark` file gets one `info` note (`checks.P1_LOW_INFO_METHODS`;
  info never fails and is a GitHub `::notice`). A 3DMark run is a normal game run with the
  graphics-test FPS as `avg_fps` and its result URL as `proof.summary_source`.
- A community average more than 25% from the matching official average fails
  `community-outlier` (`OUTLIER_RATIO` in `scripts/checks.py`).
- Catalog specs are nested (`identity`, `classification`, `silicon`,
  `memory`, `clocks`, `power`, `release`, `features`). Only five fields are
  required (`id`, `identity.name`, `identity.gpu_vendor`,
  `classification.form_factor`, `memory.capacity_gb`); quote every date and
  version number so YAML keeps it a string.
- A result folder's name must exactly equal the `gpu_id` inside its files, and
  that ID must be a catalog file name under `data/gpus/`.
- Catalog IDs are product-level with one `<N>gb` token equal to
  `memory.capacity_gb`. Different memory sizes and board partners are
  different IDs. Handheld RAM is in the ID; laptop system RAM is recorded per
  run. The catalog folder is `<form_factor>/<gpu_vendor>`, where
  `gpu_vendor` is the GPU chip maker. The field is `identity.gpu_vendor`, not
  `vendor`.
- `data/gpus/reference/` holds shared chip specs, not products. Products use
  `base: <ref_id>` and the build deep-merges them over the reference.
  Results never point at a reference ID. `platform` is for handhelds and
  laptops only, and `board_partner` is for desktop cards only.
- Catalog files list `sources` (https URLs, `covers` = sections that page
  actually backs). Never invent a source or a spec value; leave unknowns out.
  Quote source titles that contain `: `. The GPU vendor's own spec page
  (nvidia.com, amd.com, intel.com) wins every conflict; Wikipedia or
  TechPowerUp only fill fields the vendor doesn't publish. Cite the card's own vendor page as well as any overview page.
- Block-style YAML only in data and templates: no inline `[ ]` or `{ }`.
- Every rule lives once in `scripts/checks.py`. A new rule needs a
  ``#### `rule-name` `` heading in `data/gpus/README.md` or
  `docs/COMMUNITY_SUBMISSIONS.md`, and `test_build.py` enforces that.
- Exact machine metadata stays on each run; charts show grouped summaries.
- Raw capture evidence is preferred; preserve its reference when correcting or
  removing a record.
- Every result file needs a quoted `date: 'YYYY-MM-DD'` (`result-date`): the
  day it was run, or a found result's publish date. It must equal the file
  name's `YYYYMMDD` (`result-date-filename`), because one file holds one day.
  Each `result` item may add a quoted local `time` (`'HH:MM'` or
  `'HH:MM:SS'`, no time zone; `result-time`). Neither is a grouping key; the
  API puts `date` and `time` on every run record.
- Community files are anonymous by default. Only `gpu_id`, `game_id`, `date`, the
  `result` list, `system.os`, and `proof.method` are required. `submitted_by`
  is optional (a valid GitHub username when set), and the file name is
  `result_YYYYMMDD_<game_id>.yaml` (same-day repeats `_<game_id>_2`; older names
  ending in a username still pass). Runs with no evidence show as
  "Unverified" (`proof_level: none`). Official runs are maintainer-verified
  by definition (`maintainer-verified`, "Verified") and may carry a `credit`
  with just a `name` for a run entered on someone's behalf.
- A result someone else measured (a video, review, or post) adds a `credit`
  block with an https `source_url` saying where it was found; no permission
  is needed. Unpublished numbers, such as a friend's, give `permission` (at
  least one of `url`, `screenshot`, `note`) instead. `name` and `url` are
  optional. The dashboard shows "Name (via @user)", the source's site when
  there's no name, or "Anonymous". Example credits use made-up names and
  `example.com` URLs, never a real creator or channel.
- Upscaling is off by default. `upscaling` is allowed only with
  `preset_upscaling: true` (the graphics preset turned it on), otherwise
  `result-upscaling` fails. It is a grouping key, so upscaled runs never
  average with native ones.
- Cyberpunk 2077 built-in benchmark runs come in through
  `scripts/import_cyberpunk.py`. It writes one `result_YYYYMMDD_cyberpunk_2077.yaml`
  per day and setup, with one `result` item per run. Each item's
  `benchmark_run` names its run folder, and that is how re-runs skip imported
  runs. A run with a different version, driver, CPU, memory, or OS goes in a
  `_2` file, because those fields apply to the whole file. It uses the
  in-game preset names (`Ray Tracing: Ultra`) and upscaler labels
  (`DLSS Auto`, `FSR 2.1 Quality`); keep those labels stable, because
  changing one splits dashboard groups. Settings come from `summary.json`;
  `avg_fps` and `p1_low` come from the run's `frames.csv` frame times, and a
  re-import backfills `p1_low` on earlier runs that lack one. The game
  doesn't report RAM type or channels, so `--memory-type` and
  `--memory-channels` default to `DDR5-6000` and `2` with an on-screen
  warning when they're left out. Official desktop runs need
  `--testbench <id>`, which writes `testbench_id` and takes the RAM type and
  channels from the bench; a different bench on the same day goes in a `_2`
  file.
- Keep GitHub links absolute and API/data links relative to the page, so
  every host works. The one exception is the canonical origin
  `https://opengpubenchmarks.com/` (`build.SITE_URL`): the canonical link,
  `og:url`, and JSON-LD in `index.html`, `robots.txt`, and the generated
  sitemap and pages use it, and `test_build.py` checks that they agree.
- AI crawlers and search engines are welcome. robots.txt never disallows
  anything, and `build.py` writes JavaScript-free copies of every summary
  (`benchmarks/`, `llms-full.txt`) because most AI crawlers don't run JS.
- `preview.yml` deploys Cloudflare previews only for the repo owner's own
  same-repo PRs, never for `benchmark/*` branches. Keep it on `pull_request`,
  never `pull_request_target`.
- **Benchmark issues are the primary submission path.** The issue form
  (`.github/ISSUE_TEMPLATE/benchmark.yml`, label `benchmark`) feeds
  `benchmark-issue.yml`, which runs `scripts/issue_to_result.py`, commits the
  one generated file to `benchmark/issue-<N>`, and opens a pull request with a
  GitHub App token. A code owner approves it. Pull requests stay the path for
  bulk or scripted uploads (the Cyberpunk importer, raw captures). Safety
  rules, all from `docs/COPILOT_HANDOFF.md` ("Benchmark issues and the bot
  App"); `test_build.check_bot_safety()` enforces what it can:
  - `benchmark/*` and bot pull requests never get Cloudflare previews;
  - never enable "Allow GitHub Actions to create and approve pull requests";
  - never give the bot App the Workflows permission;
  - never call a review, approve, or merge API from a workflow;
  - never reference the Cloudflare secrets in `benchmark-issue.yml`;
  - never interpolate `github.event.issue.body` into a shell line (it goes
    through the `ISSUE_BODY` env var).
  - never let the bot add a game: the form accepts only a `game_id` or name
    already in `data/games.yaml`, and a new game comes in its own pull request.
- `.github/CODEOWNERS` is the maintainer list, and a code owner's approval is
  required to merge. Adding a maintainer means adding their `@username` there
  and giving them write access. Never add a bot.
- A change to the issue form's labels or options goes in
  `issue_to_result.py` (`FIELDS`, `CAPTURE_TOOLS`, `WHO_RAN_IT`, `OSES`,
  `GRAPHICS_APIS`) and `tests/fixtures/issues/valid.md` in the same commit.
  `test_build.check_issue_form_matches_script()` fails otherwise, and a new
  `checks.PROOF_METHODS` value needs a form option.
- The blog is Astro, scoped to `/blog/`. `build.py` still owns the dashboard,
  the API, the sitemap, and `llms.txt`, and it lists non-draft posts in both.
  Astro builds after `build.py`, because `<BenchChart>` and the review spec
  cards read `site/api/v1/`. Its rules live in
  `blog/src/content.config.ts` (frontmatter) and `blog/src/lib/posts.ts`
  (reserved slugs, affiliate disclosure), not in `scripts/checks.py`.
- `BLOG_BASE` sets the blog's path: `/blog` (the default, Cloudflare) or
  `/open-gpu-benchmarks/blog` (the GitHub Pages mirror, a second build in
  `build.yml`). Blog code builds links from `import.meta.env.BASE_URL` and
  `siteRoot()`, never a hard-coded `/blog/`. Canonical, `og:url`, and RSS
  links always use `https://opengpubenchmarks.com/blog/`. In Git Bash, set
  `MSYS_NO_PATHCONV=1` or Git Bash rewrites `BLOG_BASE` into a Windows path.
- The blog never restyles the dashboard. `blog/src/styles/tokens.css` is a
  verbatim copy of the `:root` blocks in `site/index.html`, and
  `test_build.py` fails if they differ, so a color change goes in both.
- The author writes the content. AI may clean up wording and insert
  affiliate links, and the post says so in `ai_assistance` (for example
  "Grammar and flow cleanup"). A post AI wrote sets `ai_generated: true`,
  which the page marks; see `content/README.md`. Never type benchmark
  numbers into a post; use `<BenchChart>`. Store links go only
  through `<AffiliateLink>` with `affiliate: true`, which adds the disclosure
  banner. The affiliate programs aren't chosen yet, so
  `blog/src/data/retailers.ts` has no IDs.
- Licenses:
  - **Code** is MIT (`LICENSE`).
  - **Benchmark data** is CC BY 4.0 with reasonable attribution
    (`data/LICENSE`, explained on `site/license/index.html`). That's
    everything in `data/` and everything built from it. AI training is
    explicitly permitted; sites credit "Data from Open GPU Benchmarks" with a
    link, charts and videos may use a text credit, and AI models credit it
    in their model card, not in every output. Data published before the
    switch was CC0, and copies made then keep those terms.
  - **Blog writing** in `content/` stays the author's copyright, all rights
    reserved, under neither license. A post with `ai_generated: true` claims
    no copyright in its text. `PostLayout.astro` prints the line on every post.
  - Submitting a result releases it under CC BY 4.0. The plain-English terms
    live once in `docs/COMMUNITY_SUBMISSIONS.md` ("Your results become public
    data"). The same five points are repeated in full on the dashboard's
    submission panel, on `license/`, and in the issue form. CONTRIBUTING,
    `data/community/README.md`, the community templates, and
    `.github/pull_request_template.md` give a short version plus a link.
    Change them together.
  - `build.DATA_LICENSE`, `build.DATA_ATTRIBUTION`, and `build.API_LICENSE`
    feed the `_license` block that leads every API file (next to `_source`),
    `metadata.license`, `llms.txt`, and `benchmarks/`. The `index.html`
    JSON-LD (`creator`, `license`, `usageInfo`, `creditText`) and `license/` repeat them.
    `test_build.check_licenses()` checks they agree.
  - Never add data under other terms.
- The dashboard's **Featured GPU picks** come from `data/picks.yaml`:
  - Slots are `amd`, `nvidia`, and `intel`, one card each. Empty slots show
    "coming soon".
  - A pick needs a `note` and a `name`, or a catalog `gpu_id` whose vendor
    matches the slot. It also needs `links` (`amazon`/`newegg`/`bestbuy` +
    https URL).
  - Never add prices.
  - `checks.load_picks()` holds the rules, and `checks.PICK_RETAILERS` must
    match `blog/src/data/retailers.ts`.
  - Example picks use made-up names and `example.com` URLs.
- Versions are `MAJOR.MINOR.DATA.POST` with four parts. MINOR is any code
  change, DATA is new published runs, and POST is a new or updated post.
  `test_build.py` checks that `RELEASE_VERSION` matches the newest
  `## x.y.z.w - date` heading in `CHANGELOG.md`.

## Checks to run before finishing

Run the checks inside the project's virtual environment, never the global
Python. Create it once with `python -m venv .venv`; after that, only activate it.

```powershell
.venv\Scripts\Activate.ps1               # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts/checks.py scripts/build.py scripts/validate.py scripts/parse.py scripts/import_cyberpunk.py scripts/issue_to_result.py scripts/test_build.py
npm --prefix blog ci                     # Node 22.12+; once, or after the lockfile changes
npm --prefix blog run build              # after build.py; writes site/blog/
git diff --check
```

Preview the site with `python -m http.server 8000 --directory site` and open
<http://localhost:8000> (the blog is at `/blog/`). `npm --prefix blog run dev`
serves the blog with live reload at <http://localhost:4321/blog/>, drafts
included. Stop every server when you're done with it, and run
`deactivate` at the end of the session (see "Wrapping up a session").

Create a Git tag only when explicitly asked, after the commit is reviewed.

## Wrapping up a session

Context for the next session lives in the instruction files, not in this
conversation. Before you report a task complete, clean up and update whatever
is now stale:

- **Clean up your environment** → stop every server or background process you
  started (for example the `python -m http.server 8000 --directory site`
  preview), then run `deactivate` to leave the `.venv` virtual environment.

- **Data contract, schema, or build-output change** → update
  [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md),
  [README.md](README.md), and
  [.github/copilot-instructions.md](.github/copilot-instructions.md) if a rule
  changed. Bump `SCHEMA_VERSION` when the generated API payload changes.
- **Any behavior, schema, dashboard, or workflow change** → add a line under
  `Unreleased` in [CHANGELOG.md](CHANGELOG.md). Always; see the top of this
  file.
- **Work finished, deferred, or discovered** → update the backlog in
  [docs/TODO.md](docs/TODO.md).
- **Agent instructions changed** → keep `CLAUDE.md`,
  `.github/copilot-instructions.md`, and `AGENTS.md` consistent.
- **Version bump (every PR but data-only submissions; see the top of this
  file)** → pick the part from the biggest change in the PR (MAJOR breaking,
  MINOR code, DATA runs, POST posts), reset the parts to its right, rename `Unreleased` in `CHANGELOG.md` to the new four-part
  version and date, and update `RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py) plus the version references and feature
  summary in `README.md` and `docs/COPILOT_HANDOFF.md`.
- **Blog post published** → a POST bump (see above), with a changelog line
  "New post: `<title>`".
- **Fixtures or published runs added/removed** → refresh the counts (catalog
  GPUs, official runs, community runs, dashboard summaries). Published `data/`
  counts are quoted in `README.md` and `docs/COPILOT_HANDOFF.md`; the
  `tests/fixtures/data/` counts live only in `docs/COPILOT_HANDOFF.md` and the
  fixture numbers asserted in `scripts/test_build.py`. These counts go wrong
  easily.
- **Submission or validation rules changed** → update `CONTRIBUTING.md`,
  `docs/COMMUNITY_SUBMISSIONS.md`, `data/community/README.md`,
  `data/gpus/README.md`, and the data rules in
  `.github/copilot-instructions.md`.
- **New command, script, or workflow step** → add it to the check lists in
  `README.md`, `CONTRIBUTING.md`, `docs/COPILOT_HANDOFF.md`, and
  `.github/copilot-instructions.md`.
- **Anything a future session would have to rediscover by reading code** → put
  it in `docs/COPILOT_HANDOFF.md`, and add the rule here or in
  `.github/copilot-instructions.md` if it constrains future work.

Keep this file current too: if the layout, the checks, or the list of
instruction files changes, edit `CLAUDE.md` in the same commit.
