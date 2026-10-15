# Changelog

High-level, user-facing changes by version, newest first. Details live in git
history and pull requests. Follows [Keep a Changelog](https://keepachangelog.com/)
headings (Added, Changed, Removed, Fixed).

**Every PR updates this file.** Contributors and AI agents (Claude, Copilot,
or any other) add a line under `Unreleased` in every PR that changes behavior,
the data contract, the API schema, the dashboard, the checks, or the
contributor workflow. Data-only result submissions can skip it. When the
version is bumped, rename `Unreleased` to the new version and date, then start
a fresh empty `Unreleased` section.

## Versioning

From 1.1.0.0, versions are `MAJOR.MINOR.DATA.POST`, always written with four
parts (tags are `vMAJOR.MINOR.DATA.POST`):

- **MAJOR**: a breaking change to the data contract or the API.
- **MINOR**: any code change (features and fixes alike).
- **DATA**: newly published benchmark runs.
- **POST**: a new or materially updated blog post, guide, or review.

Bumping one part resets the parts to its right (1.1.2.3 then 1.2.0.0). There is
one bump per release, not per pull request: the biggest kind of change under
`Unreleased` picks the part. Community data PRs don't add their own line; a
DATA or POST release gets one short line, for example "12 new Cyberpunk 2077
runs" or "New post: <title>". Earlier releases used three parts.

## Unreleased

### Added
- Result files require a top-level `date: 'YYYY-MM-DD'` that matches the file
  name's date (a found result uses its publish date), and each run may add an
  optional local `time`. New checks: `result-date`, `result-date-filename`,
  and `result-time`. API schema 0.14 puts `date` and `time` on every run
  record. The Cyberpunk importer and `parse.py` write them, and existing files
  were backfilled from their file names.

### Fixed
- Dashboard on phones: the submission example, review checklist, and API code
  blocks no longer spill past their panel; code scrolls inside its own box.

### Changed
- Dashboard header on phones is compact: one brand line with the icon buttons
  beside it and the All/Official/Community switch on a single row below.
- Blog header on phones is compact too: one line, no subtitle, smaller icons.
- Agent instructions: new branches always start from `main`.
- The site icon now shows at the top left of the dashboard and blog headers.

## 1.1.0.0 - 2026-10-14

A blog, guides, and reviews section at `/blog/`, featured GPU picks on the
dashboard, and four-part versions.

New post: "Why I'm Starting Open GPU Benchmarks".

### Added
- `/blog/`, built with Astro from Markdown and MDX posts in
  `content/posts/<slug>/`. It has post, guide, and review types, tag pages, an
  RSS feed, and optimized images. It shares the dashboard's colors and theme
  setting.
- Post components:
  - `<BenchChart>` draws a chart from the published summaries at build time,
    with no client JavaScript.
  - `<Callout>` adds a note, tip, or warning banner.
  - `<AffiliateLink>` marks a link `rel="sponsored"`. Any post with
    `affiliate: true` gets an automatic disclosure banner, and the build fails
    if an affiliate link appears without it.
  - Reviews show the catalog specs, a verdict, and pros and cons.
- Posts say how AI was used: `ai_assistance` (for example "Grammar and flow
  cleanup") goes in the footer, and `ai_generated: true` marks a post AI wrote,
  with an "AI-generated" pill. Unknown
  frontmatter fields, unquoted dates, and `gpu_ids` that aren't catalog
  products fail the build.
- The sitemap and `llms.txt` list the blog and every published post.
- A "Blog" link in the dashboard header.
- **Featured GPU picks** on the dashboard, replacing the empty "Official GPU
  and laptop reviews" panel:
  - One card each for AMD, NVIDIA, and Intel, from `data/picks.yaml`, with
    store buttons and an affiliate disclosure. There are no prices, because
    they go stale and Amazon's rules don't allow typed-in prices.
  - A pick can name a catalog `gpu_id`, which adds VRAM, power, and a "See
    benchmarks" button, or be any card by `name`.
  - Empty slots show "coming soon".
  - New `pick-slot`, `pick-field`, `pick-gpu-id`, and `pick-link` checks
    (run by `validate.py catalog` and `build.py`).
  - API schema 0.13 adds `picks` to `dashboard.json` (and
    `metadata.license`, below). `reviews` stays in the API, unchanged.
- A fourth PR check, **Blog**, that builds the blog.
- `test_build.py` checks that:
  - the blog's color tokens match `site/index.html`
  - draft posts stay out of the sitemap
  - `RELEASE_VERSION` matches the newest release here

- License files:
  - `LICENSE` puts the code under MIT.
  - `data/LICENSE` puts the benchmark data under CC0 1.0 (public domain),
    as the README already stated.
  - The Dataset JSON-LD, `dashboard.json` `metadata.license`, `llms.txt`,
    and `benchmarks/` all name the CC0 license, and `test_build.py` checks
    that they agree.
- Plain-English submission terms. Submitting a result releases it under
  CC0: anyone can use it for anything without permission or credit, and it
  can't be taken back. They're in "Your results become public data" in
  `docs/COMMUNITY_SUBMISSIONS.md`, with short notices in CONTRIBUTING, the
  community folder README, the templates, and the dashboard's submission and
  footer text. A pull request template asks contributors to agree.
  - Found results submit only the numbers and a link.
  - A friend's numbers need their agreement to public release.

### Changed
- Versions are now `MAJOR.MINOR.DATA.POST` (see Versioning above).
- CI and Cloudflare previews install Node 22 and build the blog after
  `build.py`. The GitHub Pages mirror gets its own blog build under
  `/open-gpu-benchmarks/blog/`.

## 1.0.0 - 2026-10-14

The first published results: the catalog starts over with the GeForce RTX 5080
Founders Edition and 33 official Cyberpunk 2077 runs, and a script turns
Cyberpunk 2077's own benchmark results into result files.

### Changed
- The templates, the dashboard's examples, and the contributor docs use
  `rtx_5080_16gb_fe`. Cyberpunk 2077 examples use the in-game preset names
  (`Ray Tracing: Ultra`) with the preset's upscaler, matching the importer.
- `test_build.py` checks the catalog templates against the fixture reference
  files, since their example bases aren't published any more.
- `community-outlier` threshold tightened from 50% to 25% away from the
  matching official average (`checks.OUTLIER_RATIO`, also reported as
  `comparison_policy.community_outlier_threshold`).
- Contributor docs now state Python 3.11+ (was 3.10+), matching CI and
  `build.py`'s use of `datetime.UTC`.
- Agent instructions (`CLAUDE.md`, `AGENTS.md`, Copilot instructions) require
  running checks in `.venv` and, before finishing, stopping any started
  servers and running `deactivate`.
- Community submissions are anonymous by default. `submitted_by` is optional
  (still checked as a GitHub username when given), and community files are
  named `result_YYYYMMDD_<game>.yaml` with no username; older names still
  pass. Only `gpu_id`, `game`, the `result` list, `system.os`, and
  `proof.method` are required. The dashboard shows "Anonymous" for runs with
  no name, and its submission guide lists everything else as optional.
- Found results: a `credit` block now needs only `source_url`, the link where
  the result was found, so anyone can add a benchmark from a video or review
  without the creator's permission. `credit.name` is optional (the dashboard
  falls back to the source's site name), and `permission` is only needed for
  unpublished numbers with no source. New
  `templates/community_found_result.yaml`.
- Upscaling is off by default. Setting `upscaling` now requires
  `preset_upscaling: true`, meaning the graphics preset turned it on; new
  `result-upscaling` check. `upscaling` is a grouping key and part of the
  official-baseline match, so upscaled runs never average with native ones.
  The templates and contributor examples no longer use DLSS.
- Evidence: `proof_level` is `none` (shown as "Unverified") when a community
  run has no raw log, summary source, or `credit.source_url`.
  `result-no-proof` now warns only in that case, and a `credit.source_url`
  counts as evidence. Official runs are verified by the maintainer: one with
  no linked evidence is `maintainer-verified` and shows as "Verified" (it was
  "Summary only").
- Official runs may carry a `credit` block, for a run the maintainer enters on
  someone else's behalf. It needs only `name`; it was an error before.
- `parse.py`: `--submitted-by` is optional, and output file names leave out the
  username and slugify the game name.
- API schema `0.12`: optional `submitted_by`, `upscaling` in `group_by` and on
  `implementations`, `proof_level` `none` and `maintainer-verified`,
  `source_url` on summary `credits`,
  and `credit_source_url` on `implementations`.
- One synthetic fixture (Steam Deck, Cyberpunk 2077) is now anonymous.
- `templates/official_result.yaml` now includes the required `system.os` and
  `proof.method`, and CONTRIBUTING's minimal example is a valid anonymous run.
- The synthetic benchmark runs moved out of `data/` into
  `tests/fixtures/data/`, with their own catalog snapshot, so the published
  site shows only real benchmarks. The site has no runs until the first real
  ones are merged. `test_build.py` now builds the fixtures into a temporary
  folder, never `site/api/`.
- The dashboard shows "No benchmarks published yet" with a link to the
  contributing guide when there are no runs, instead of an error.

### Removed
- Every published catalog entry and reference file except the RTX 5080. The
  pre-1.0 products remain in the test fixtures.
- The `result-no-driver` warning. A driver version is still welcome but never
  asked for.

### Fixed
- `build.py` deletes per-GPU summary folders in `site/api/v1/official/` and
  `community/` for GPUs no longer in the catalog. Before, a local build kept
  serving old summaries after a catalog entry was removed.

### Added
- Upscaled and native results are told apart on the dashboard. Every chart
  label has a pill naming the upscaler (`FSR 2.1 Quality`, `DLSS Auto`) or
  `Native`, colored by the upscaler's maker: DLSS and DLAA green, FSR red, XeSS
  blue, native gray, in shades tuned for each theme. Labels add the preset when several presets are shown, and leave
  out the GPU name when every bar is the same GPU. Native/Upscaled filter
  chips sit next to the OS chips, the table has a Settings column (preset and
  upscaler), and the tooltip names both. The plain benchmark tables
  (`/benchmarks/`, `llms-full.txt`) say `Native` instead of `off`.
- GeForce RTX 5080 Founders Edition (`rtx_5080_16gb_fe`) and its reference
  file `rtx_5080_16gb`, sourced from NVIDIA and Wikipedia.
- The first official results: 33 Cyberpunk 2077 built-in benchmark runs on the
  RTX 5080 FE at 1080p, 1440p, and 4K, across every quick preset plus native
  High (29 dashboard summaries).
- `scripts/import_cyberpunk.py`: reads each run's `summary.json` from the
  game's `benchmarkResults` folder (found automatically on Windows and Steam
  Proton) and writes one `result_YYYYMMDD_cyberpunk_2077.yaml` per day and
  setup, with one `result` item per run, each naming its run folder in
  `benchmark_run`. Running it again adds only new runs, appending same-day
  runs to that day's file. Each item also records its display mode.
- `display_mode` may be set on a single `result` item as well as under
  `system:`; the item's value wins on the run record. It skips runs with frame generation,
  V-Sync, or an FPS cap, runs from a different GPU, and Custom presets with
  upscaling. Custom presets with upscaling off need a name. A user guide is in
  `docs/CYBERPUNK_BENCHMARK.md`, and `test_build.py` covers the importer.
- Cloudflare Pages hosting at <https://opengpubenchmarks.com> (the canonical
  site). `build.yml` deploys the same build to Cloudflare (Wrangler Direct
  Upload) and GitHub Pages; GitHub Pages stays live as a mirror.
- `preview.yml`: Cloudflare preview deploys with a sticky PR comment, only for
  the repository owner's own same-repo pull requests. Other PRs and forks skip
  the job.
- SEO: every host declares `https://opengpubenchmarks.com/` as canonical, plus
  Open Graph tags, a better title and description, and `WebSite`/`Dataset`
  JSON-LD.
- Crawler and AI access: `build.py` writes JavaScript-free copies of every
  dashboard summary (`site/benchmarks/index.html`, `site/llms.txt`,
  `site/llms-full.txt`) and a `site/sitemap.xml`. `site/robots.txt` allows all
  crawlers, including named AI crawlers, with `Content-Signal: search=yes,
  ai-input=yes, ai-train=yes`. `site/_headers` sets Cloudflare response headers.
  `test_build.py` checks that the canonical URLs agree and that the pages
  carry every summary.
- `--data-dir` on `build.py` and `validate.py`, for example
  `python scripts/build.py --data-dir tests/fixtures/data` to preview the
  dashboard with the synthetic fixtures.
- A test that `data/` passes every check and holds no `synthetic: true` runs.
- `requirements.txt` lists the Python dependencies (`pyyaml`, `numpy`). Local
  setup now uses a `.venv` virtual environment (create, activate, install,
  `deactivate`), documented in `README.md` and `CONTRIBUTING.md`. Both CI
  workflows install from `requirements.txt` with a pip cache.
- Average-FPS-only results: `p1_low` is now optional, so 3DMark (Steel Nomad)
  and in-game benchmark runs that report no 1% low can be submitted. Without
  one, the run and its summary carry `p1_low: null`, the dashboard shows a dash,
  and the check raises the `result-no-p1-low` warning (not raised for
  `synthetic_benchmark`). Schema `0.11`.
- Required `proof.method` records which tool captured a game run: `presentmon`
  (recommended), `capframex`, `frameview`, `msi_afterburner`, `amd_adrenalin`,
  `mangohud`, `ocat`, `in_game_benchmark`, `synthetic_benchmark`, or `other`.
  It is exposed as `capture_method` and is never a grouping key. New
  `result-proof-method` check; the existing synthetic fixtures use `other`.
  `parse.py` writes it (with a new `--method` option) in place of the old
  top-level `capture_method`.
- 1% low by capture tool: frame-time tools (PresentMon, CapFrameX, FrameView,
  MSI Afterburner, MangoHud, OCAT) must include `p1_low` (new
  `result-p1-low-required` error). For AMD Adrenalin, in-game benchmarks, and
  other, a missing 1% low is a warning that says it's fine if the tool
  didn't report one.
- Third-party submissions: a community file can credit someone else's results
  with a `credit` block (name, optional links, and proof of permission as a
  link, screenshot, or note). New `community-credit` and `community-permission`
  checks; `credit_name`, `credit_url`, `credit_source_url` on run records,
  `credits` on summaries; the dashboard shows "Name (via @user)".
- A test pins the 25% outlier limit.
- Optional `score` on a result entry (for example the 3DMark score).
- `templates/community_steel_nomad.yaml`: a 3DMark Steel Nomad submission
  template that links the 3DMark result page as `proof.summary_source`.

## 0.6.0 - 2026-10-08

Linux vs Windows and catalog sources: every run says which OS it ran on, the
two are charted side by side instead of averaged, and every catalog entry cites
the pages its specs came from.

### Added
- Linux vs Windows (catalog plan step 4): game runs require `system.os`
  (`windows` or `linux`), and the OS is a grouping key, so the two are never
  averaged together. Optional OS detail fields (`os_detail`, `os_build`,
  `resizable_bar`, `graphics_api`, Windows `game_mode`/`hags`/
  `memory_integrity`/`power_plan`, Linux `distro`/`distro_version`/`kernel`/
  `mesa`/`runtime`/`proton`/`dxvk`/`vkd3d_proton`/`launcher`/`session`/
  `gamemode`) are copied to every run record; the distro is never a grouping
  key.
- New checks: `result-os` (missing or not `windows`/`linux`),
  `result-os-field` (wrong type, a bad `runtime`, or a field that doesn't fit
  the OS), and a `result-system-field` warning for unknown `system` keys.
- Dashboard: Windows and Linux filter chips (deselecting both shows every
  run, like the form-factor chips), an OS column and badge in the
  table, OS details in the run list, and a "compare distros yourself" note in
  the JSON API panel. When both OSes are on the chart, Linux bars are striped
  and a product shown under both OSes is labelled by OS.
- Six synthetic Linux runs, each paired with a Windows run of the same
  profile (RX 7900 XTX, RTX 4090, ROG Ally on Bazzite, Arc A770 LE).
- `parse.py --os {windows,linux}` and `--os-detail`, written under `system:`.
  Without `--os`, MangoHud captures default to `linux` and PresentMon to
  `windows`. MangoHud logs also fill `system.kernel` and `system.driver`.
- Tests: OS rule cases, Windows/Linux summary separation, MangoHud parsing,
  and the community template passing the result checks.
- Catalog `sources`: every catalog file lists the pages its specs came from
  (`url`, `title`, `accessed`, `covers`). Price history items can link their
  own `source`.
- Sources for all 20 current catalog files: TechPowerUp's GPU database for the
  discrete GPUs, and the AMD, Intel, ASUS, Lenovo, and Valve spec pages for
  the rest.
- Source links in the dashboard's expanded row.
- New checks: `source-invalid` (bad URL, field, date, or section name) and a
  `sources-missing` warning.
- Templates include a `sources` example.

### Changed
- API schema `0.10`: run records, summaries, and `implementations` carry `os`
  and the OS detail fields; `comparison_policy.group_by` includes `os`.
- Community outlier checks compare only against official runs on the same OS.
- The dashboard chart shows one bar per GPU: the 1% low is drawn solid over a
  faded average bar, instead of two bars side by side. The chart grows 30 px
  per GPU from a 260 px minimum, and long labels truncate on narrow screens
  (the tooltip shows the full name, OS, and both values).
- Templates and contributor docs use `system.os: windows` plus `os_detail`
  instead of free text such as `os: Windows 11`; existing fixtures migrated
  (Steam Deck runs are `linux`, SteamOS).
- API schema `0.9`: `gpus.json` entries carry `sources`. A product's sources
  are combined with its reference's, and a URL cited by both appears once.
- The ROG Ally entry gains its 40 Wh battery. The Legion Go display now lists
  its exact resolution (2560x1600), from Lenovo's spec sheet.

### Fixed
- `parse.py` read MangoHud logs and detailed PresentMon captures as 0 FPS: it
  skipped the header line and treated the first frame as the header. MangoHud
  logs with the `os,cpu,gpu,...` header block now parse too.

## 0.5.0 - 2026-10-08

Per-product catalog: every card, laptop, and handheld is its own file and its
own benchmark group, with shared chip specs in reference files and checks that
report every problem at once.

### Added
- **Per-product GPU catalog.** One file per card, laptop, or handheld at
  `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. `data/gpus/README.md`
  documents the ID rules, a field reference, and every check.
- **Reference files** under `data/gpus/reference/<gpu_vendor>/` hold the specs
  shared by every product built on one GPU. Products inherit them with `base:`
  and list only what they change or add. Nine references were split out of the
  existing entries, including `z1_extreme`, now shared by the ROG Ally and the
  Legion Go.
- **Device specs.** A `platform` section for handhelds and laptops covers
  maker, CPU, RAM speed, OS shipped, display, power range, and battery. The
  dashboard's expanded row shows it as a "Device" grid. Desktop cards get
  `identity.board_partner`, and any product can list variants that share an
  entry under `skus`.
- **Full hardware specs per card** in nested sections (`identity`,
  `classification`, `silicon`, `memory`, `clocks`, `power`, `release`,
  `features`), backfilled for all 11 entries.
- **Dashboard spec table.**
  - Per-card columns: vendor, form, architecture, VRAM, bus, bandwidth,
    clocks, shaders, RT cores, TDP, process, release, and MSRP.
  - Every column sorts.
  - Search covers IDs, codenames, and architectures.
  - Expanding a row shows the silicon details, price history, device specs,
    and the exact runs behind the number.
- **Shared checks** in `scripts/checks.py`.
  - Both `build.py` and `validate.py` use them.
  - Each run reports every problem at once, tagged with a rule name that
    links to its explanation.
  - The build stops without writing `site/api/` when any error exists.
- **New check rules.**
  - Block-style YAML only: inline `[ ]` and `{ }` are rejected.
  - Unknown catalog fields are rejected.
  - Stray files in result folders, which the build would silently skip, are
    flagged.
  - Reference rules: `base-unknown`, `base-mismatch`, `reference-field`, and
    `field-not-allowed`.
  - `result-reference-id` rejects results that point at a reference file.
  - Range checks for the `platform` fields.
- **Validation commands.** `validate.py catalog` and `validate.py results` run
  each half on its own. Official result files are now checked too.
- **CI.** Pull requests show three separate checks: **Catalog entries**,
  **Benchmark results**, and **Build and tests**. The deploy workflow now
  validates the data before building.
- **Templates.** Catalog templates for desktop, laptop, handheld, and
  reference entries.
- **Contributor guide.** New section, "Adding a card, laptop, or handheld",
  with worked examples and a guide to reading a failed check.
- **Site favicon** (`site/favicons/`): an SVG icon that follows the dashboard's
  light/dark toggle, with ICO and Apple touch icon fallbacks.
- **`AGENTS.md`**: a tool-neutral entry point for AI agents, pointing to the
  shared rules, the changelog requirement, and the backlog.

### Changed
- **API schema.** The schema is now `0.8`. It passed through three versions in
  this release:
  - `0.6`: catalog specs are nested. Run records keep flat `vram_gb` and
    `tdp_w`; `vram_gb` is null for shared-memory handhelds instead of 0.
  - `0.7`: IDs are product-level and the vendor field is `gpu_vendor`.
  - `0.8`: `gpus.json` entries carry `base`, `board_partner`, `skus`, and
    `platform`, already merged with their reference.
- **Product-level IDs that include the memory size.** For example, `rtx_4090`
  became `rtx_4090_24gb_fe` and `legion_go` became
  `legion_go_z1_extreme_16gb`. Different memory sizes and board makers are
  never averaged together. Result folders were renamed to match. Laptops with
  an unknown model use a temporary `_generic` ID.
- **Vendor field renamed.** `identity.vendor` is now `identity.gpu_vendor`,
  and run records carry `gpu_vendor` instead of `vendor`.
- **Product names.** The vendors' own cards are now named "Founders Edition",
  "Limited Edition", and "(AMD reference)".
- **Required fields.** Only five catalog fields are required: `id`,
  `identity.name`, `identity.gpu_vendor`, `classification.form_factor`, and
  `memory.capacity_gb`. The dashboard shows `—` for anything missing.
- **`parse.py`** rejects IDs that aren't in the catalog and takes the form
  factor from the catalog entry.
- **`CONTRIBUTING.md`** is rewritten around submitting a result:
  - a 5-step flow with a diagram
  - visuals for the file name and folder
  - validated desktop, laptop, handheld, and summary-only examples
  - a table of required fields and a table of common mistakes

  `data/community/README.md` now points to it.

### Removed
- `data/gpus.yaml`, replaced by the per-product catalog.

## 0.4.0 - 2026-10-03

### Added
- Community result files require `submitted_by` (the submitter's GitHub
  username); file names end with the same username:
  `result_YYYYMMDD_<game>_<github_user>.yaml`. The validator enforces both.
- API schema `0.5`: `submitted_by` on every run record and a `contributors` list
  on every grouped summary.
- Dashboard "Get the data as JSON" panel with Open and Copy URL actions for each
  endpoint, plus `curl` and `fetch` examples.
- Dashboard header and footer links to the GitHub repository, contributing
  guide, and issues.
- `docs/TODO.md` for deferred work.
- This changelog.

### Changed
- `scripts/parse.py` requires `--submitted-by` and uses the new file name.
- Renamed all community fixtures to the new naming scheme.

### Removed
- The "Desktop vs Laptop vs Handheld" tagline from the dashboard header.

## 0.3.0

### Changed
- Restructured results by GPU: `data/official/<gpu_id>/` and
  `data/community/<gpu_id>/`, with generated per-GPU summary JSON and a
  GPU-rooted master API (`gpus.json`).
- Each result file holds a `result` list of resolution/preset profiles that are
  validated and grouped independently.

### Added
- `CLAUDE.md` agent entry point.

## 0.2.0

### Added
- Graphics preset filter and community submission guidance.
- Chart bars colored by GPU vendor.

## 0.1.0

### Added
- Initial data-driven benchmark dashboard on GitHub Pages, built from reviewable
  YAML.
