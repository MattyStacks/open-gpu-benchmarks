# TODO

The backlog: deferred work that's out of scope for current PRs. Pick items up
only when asked.

**Every PR keeps this file current.** Remove items you finished, move them to
[Recently completed](#recently-completed), and add anything you deferred,
found broken, or were asked to do later. This applies to people and to every
AI agent. The same rule is in `CLAUDE.md`, `AGENTS.md`, and
`.github/copilot-instructions.md`.

## Catalog follow-ups

The four-step catalog plan is complete. These items finish it off.

- [ ] **Re-validate the RTX 5080 sources by hand.** `rtx_5080_16gb` and
  `rtx_5080_16gb_fe` cite NVIDIA's product page and Wikipedia (2026-10-14),
  because TechPowerUp blocks scripts with a bot check. The clocks are written
  from NVIDIA's rounded 2.30/2.62 GHz as 2300/2620 MHz, and `mem_mhz` and
  `features.fsr` are left out. Check them against TechPowerUp or NVIDIA's
  Blackwell whitepaper (Appendix B) and add a TechPowerUp source.
- [ ] **Require `sources`.** After the re-validation above, turn the
  `sources-missing` warning into an error.
- [ ] **Make `_generic` laptop IDs an error.** Since v1.0.0 the published
  catalog has no `_generic` IDs (only the test fixtures do), so `id-generic`
  could become an error for `data/` once the fixtures stop needing it.
- [ ] **Re-add the pre-1.0 catalog products when they get real runs.** v1.0.0
  reset `data/gpus/` to the RTX 5080 FE. The old entries (RTX 4090/4080
  Super/4070 Super FE, RX 7900 XTX, Arc A770 LE, the laptops, and the
  handhelds) are still in `tests/fixtures/data/gpus/` and in git history.

## 3DMark and capture tools

Follow-ups to average-only results and `proof.method` (PR #13).

- [ ] **Add the first Steel Nomad run.** Add the maintainer's Steel
  Nomad run on the RTX 5080 FE (8603 score, 86.03 FPS) as community data with its 3DMark result
  URL as `proof.summary_source`. Also add an official Steel Nomad baseline per
  catalog GPU, since without one the run only gets `result-no-baseline`.
- [ ] **Confirm 3DMark fixed settings.** Check the fixed render resolution and
  preset for Steel Nomad, Steel Nomad Light, and the other benchmarks people
  will submit, and list them in `docs/COMMUNITY_SUBMISSIONS.md`. The Steel
  Nomad template now says `4K` (Light is the 1440p test); confirm it against
  3DMark's technical guide. Consider a check that rejects a `synthetic`
  `game_id` run at the wrong resolution, perhaps with a fixed `resolution` in
  its `data/games.yaml` entry.
- [ ] **Add Steel Nomad Light to `data/games.yaml`** when the first Light run
  arrives (`3dmark_steel_nomad_light`, `type: synthetic`, 1440p).
- [ ] **Fill in store IDs for the registered games.** `helldivers_2` and
  `3dmark_steel_nomad` have no `steam_appid` or `url` yet. Add them after
  checking each store page; never guess.
- [ ] **Parsers for more capture tools (separate PR).** `parse.py` reads only
  PresentMon and MangoHud CSVs. Add CapFrameX, NVIDIA FrameView, MSI
  Afterburner/RTSS, and AMD Adrenalin exports, writing the matching
  `proof.method`. Needs real sample exports from each tool to test against;
  don't guess the formats.
- [ ] **Multi-GPU machines.** 3DMark and PresentMon captures can come from a
  machine with an iGPU or a second card. Consider a `system.gpu` field to
  record the GPU name the tool reported, and a check against the catalog
  entry.
- [ ] **Tune the outlier limit.** `OUTLIER_RATIO` is 25% from the official
  average (`scripts/checks.py`). Revisit it with real data: a retail card's
  run-to-run spread on one benchmark is far smaller than 25%, so 3DMark runs
  could use a tighter limit than games. Also decide whether the gap should be
  measured against the best known score for the hardware.

## Data and submissions

- [ ] **Use the run `date`** (API schema 0.14) now that every run has one.
  Ideas: a historical chart of a product's results over time (driver and game
  updates), a "since" filter or download option for the JSON, and a rule or
  dashboard toggle to hide or retire runs older than a cutoff. Decide whether
  any of this changes grouping before building it; today `date` never groups
  runs.

- [ ] **Cyberpunk importer follow-ups** (`scripts/import_cyberpunk.py`).
  - Confirm the upscaler quality indices that weren't checked against
    `UserSettings.json`: DLSS and FSR 2.1 indices other than DLSS 0 (Auto)
    and FSR 2.1 1 (Quality) follow the menu order, and FSR 3, FSR 4, XeSS,
    and FSR 1.0 are written as `(mode N)`. A label change splits dashboard
    groups, so update existing files in the same PR.
  - Confirm `windowMode` 0 (Windowed) and 1 (Borderless windowed); only 2
    (Fullscreen) was checked against `UserSettings.json`.
  - The 1440p native High run on the RTX 5080 FE was recorded twice on
    2026-10-13 (`20-16-59` and `20-19-09`); decide whether to keep both.
  - Make `--gpu-id` remembered or inferred when the catalog has one match.
- [ ] **Importers for other games' built-in benchmarks**, using the same
  one-file-per-run naming so re-runs skip imported runs.

- [ ] **Benchmark issue follow-ups** (`benchmark-issue.yml`,
  `scripts/issue_to_result.py`). The issue form is now the primary way to
  submit.
  - File a test issue end to end. The one-time setup in
    `docs/COPILOT_HANDOFF.md` ("Benchmark issues and the bot App") is done
    (2026-10-15): the App is installed, `BENCHMARK_BOT_APP_ID` and
    `BENCHMARK_BOT_PRIVATE_KEY` are set, and "Base Rules" requires a
    code-owner approval with a Repository admin bypass for pull requests only.
  - Parse or scrape what people attach, into the same run dict
    `build_run()` returns:
    - a PresentMon, CapFrameX, or MangoHud CSV attached to the issue, through
      `parse.py`, kept under `raw/`;
    - a Cyberpunk `summary.json`, through `import_cyberpunk.py`;
    - a screenshot;
    - a review URL.
  - Fields the form doesn't take yet: Linux-only `system` fields (distro,
    kernel, Mesa, Proton, ...), per-run `time`, `gpu_power_w` for laptops,
    `device_name`, and `permission` credits for unpublished numbers.
  - A static web form on the dashboard that prefills the issue.
  - Maybe later: let the bot add a game that isn't in `data/games.yaml`.
    For now the form only accepts listed games, and a new game needs its own
    pull request, so the registry doesn't fill up with one-off entries.
  - Spam: watch whether the 10-open-PR queue cap is enough. Options are a
    per-author limit, or holding first-time submitters until a maintainer
    adds a label.
  - An "Official benchmark review" or "Report a bad result" form could reuse
    the same bot (see the items below).
- [ ] **Flesh out official benchmarks and cross-check them against community
  data.** Official runs must stay close to community runs for the same
  product, game, resolution, preset, and OS. Today only the reverse exists:
  `community-outlier` checks each community entry against the official
  average.
  - Add a check in `scripts/checks.py` (run by `build.py` and `validate.py`)
    that compares each official summary (avg FPS and 1% low) with the
    community summary for the same group key. Flag when the difference
    exceeds a configurable percentage (start around 10 to 15 percent) and
    require a minimum community sample count, such as 3 runs, so thin data
    doesn't trigger it.
  - Severity: a warning locally and in the PR check, with a clear message
    naming the official file, the community median, and the percent gap.
    Decide whether large gaps (for example over 25 percent) become errors.
  - The message must tell the user the next step: re-check the submission or
    open a GitHub issue asking the maintainer to review the official
    benchmark. Add an issue template for "Official benchmark review".
  - Outliers: support pulling an official run out of summaries (for example
    an `excluded: true` plus `excluded_reason` field) while keeping the file
    and its raw evidence.
  - Add a ``#### `rule-name` `` heading for each new rule, tests in
    `scripts/test_build.py`, and document what "official" means (who may add
    them, required raw evidence, test-bench spec).
  - Also grow the set of official runs per game and GPU.
- [ ] **Custom graphics presets.** Let people submit runs with their own
  settings instead of only the standard presets.
  - Decide the data shape: for example `graphics_preset: custom` plus a
    block-style `custom_settings` map (texture quality, shadows, RT, upscaler
    and its mode, and so on) and an optional `custom_preset_name`.
  - Update the preset validation in `scripts/checks.py` so `custom` is
    accepted only with settings, and unknown fields stay rejected.
  - Decide grouping: custom runs must not be averaged with standard presets.
    Group by a hash or normalized form of the settings, or keep them
    ungrouped and show them as individual runs.
  - Keep `frame_generation: false` required. Update `templates/`, the
    dashboard preset filter and labels, and bump `SCHEMA_VERSION` if the API
    payload changes.
  - Docs: `docs/COMMUNITY_SUBMISSIONS.md`, `docs/COPILOT_HANDOFF.md`,
    `.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`.

- [ ] **Scrub raw captures for personal data.** Raw PresentMon and MangoHud
  logs can contain a PC name, Windows username, or file paths. The docs now
  warn about it; consider having `parse.py` or a check flag user-folder paths
  in files under `raw/`.
- [ ] **Show upscaling in chart labels.** Upscaling is now a grouping key, but
  only the run details show it. A preset-upscaled bar and a native bar of the
  same preset look alike in the chart and table.
- [ ] **Report a bad result.** Add an issue template for flagging a wrong
  community or official result, and an `excluded: true` plus
  `excluded_reason` field that drops a run from summaries but keeps the file
  (see the official cross-check item above).

## Dashboard

- [ ] **Search in the Benchmark picker.** The picker is a plain `<select>`
  built from `dashboard.json` `games`, grouped by type. That list will get
  long as `data/games.yaml` grows. Replace it with a searchable combobox
  that matches on name and ID (later perhaps year or edition), keeps the
  type groups, and stays usable with a keyboard and on phones.

- [ ] **Show the internal render resolution of upscaled results**, for example
  "4K, renders at 1440p" for FSR 2.1 Quality, next to the upscaling pill. It
  needs confirmed scale factors per upscaler and mode, and Auto modes pick a
  mode from the output resolution, so they can't be shown without the game's
  rule.

- [ ] **Roll-up view by GPU model.** Group products that share a `base`
  reference, for example every RTX 5060 Ti 16 GB board, and compare boards
  of the same GPU side by side.
- [ ] **Linux vs Windows comparison view.** Show the percentage difference per
  product and game wherever both OSes have results.
- [ ] **Fix the chart legend.** The "Official" and "Community" swatches
  above the chart don't match the bars, which are colored by GPU vendor.
  Either color by source, or show a vendor legend.
- [ ] **Phone-width layout scrolls sideways.** At 390 px the header buttons
  and toolbar are wider than the screen, so the whole page scrolls
  horizontally.
- [ ] **Remove the six-GPU selection limit.** Let users pin more than six GPUs
  to the top of the chart and table (the limit and its "up to six" text are in
  `site/index.html`).
- [ ] **Rename "Benchmark summaries".** The table is now a per-card spec and
  results table, so give the section a more meaningful heading.
- [ ] **Make the table search more noticeable.** Widen the search input so it
  stands out as the table grows.
- [ ] **Per-GPU or per-vendor icons** in the table and chart labels.

## Content and outreach

- [ ] **Pick affiliate programs.** Amazon Associates, Newegg, and Best Buy are
  likely. Once approved, set the Amazon `id` in
  `blog/src/data/retailers.ts`, and check each program's required disclosure
  wording against `DisclosureBanner.astro`.
- [ ] **Fill in the featured GPU picks.** `data/picks.yaml` is empty, so all
  three dashboard cards say "coming soon". Add an AMD, an NVIDIA, and an Intel
  favorite with affiliate links once the programs are approved.
- [ ] **Fill the API's `reviews` from blog review posts.** The dashboard no
  longer shows `reviews`, but `dashboard.json` still carries it from
  `data/reviews.yaml` (empty). Have `build.py` list non-draft `type: review`
  posts there, then retire `reviews.yaml`. Also show a product's reviews in
  its expanded table row.
- [ ] **Planned content**, in order:
  - methodology guides (how results are verified, why frame generation is
    off, Windows vs Linux, average FPS vs 1% low)
  - capture how-tos (PresentMon, the Cyberpunk 2077 importer, submitting a
    found result)
  - the RTX 5080 FE review
  - data roundups once more cards have runs
- [ ] **Blog follow-ups.**
  - A per-post 1200x630 social image (a generated card when there's no
    `hero`).
  - Interactive charts, opt-in, keeping the static HTML bars as the
    no-JS fallback.
  - Related posts by tag or `gpu_ids`.
  - Link a GPU's posts from its dashboard row.
- [ ] **YouTube.** Plan episodes that point back to the dashboard and the
  posts. Video sources can be credited with the `credit` block (see
  `docs/COMMUNITY_SUBMISSIONS.md`).

## Hosting and SEO

- [ ] **Finish the Cloudflare setup (manual).** See "Cloudflare Pages" in
  `docs/COPILOT_HANDOFF.md`: Direct Upload project, custom domains, www and
  pages.dev redirects, API token secrets, AI-bot blocking off, and Search
  Console plus the sitemap.
- [ ] **A 1200x630 social share image** for `og:image` (it uses the 512 px
  icon now), and `twitter:card` `summary_large_image`.
- [ ] **Per-GPU crawlable pages** (`/gpu/<id>/`) once real runs exist, so
  searches like "RTX 4090 Cyberpunk 1440p FPS" land on a specific page. Add
  them to the sitemap. The license page then can ask reusers to link the GPU's
  own page instead of the dashboard or `/benchmarks/`.
- [ ] **Have a lawyer read the license page.** The CC BY 4.0 switch, its AI
  clarifications, the CC0-history note, and the blog copyright lines were
  written without legal review.
- [ ] **Check who blog copyright lines name.** A post's copyright holder is its
  `author`, or `DEFAULT_AUTHOR` ("Matt") without one. The first post sets
  `author: Open GPU Benchmarks`, so its line reads "© 2026 Open GPU
  Benchmarks". Change it if the copyright should name a person.
- [ ] **Optional fixture-data preview.** PR previews build the real `data/`,
  which has no runs yet. A second preview built with
  `--data-dir tests/fixtures/data` would help with functional testing.

## Tooling and bugs

- [ ] **Warn when a file name's game part doesn't match `game_id`.** Files are
  named `result_YYYYMMDD_<game_id>.yaml`, but older community fixtures use
  short names such as `_cyberpunk`, so this isn't checked yet.

- [ ] **Clear stale build output.** `build.py` never deletes old files under
  `site/api/v1/`. After an ID rename, a local preview still serves the old
  per-product `summary.json` files. CI is unaffected because it starts from a
  clean checkout. Fix: clear `OUTPUT_DIR` at the start of a successful build.
- [ ] **Read more of the MangoHud log header in `parse.py`.** It already
  copies `kernel` and `driver`. The header block also has `os`, `cpu`, `gpu`,
  and `ram`; map `cpu` to `system.cpu`, `ram` to `system.memory_gb` (a number), and a
  SteamOS/distro `os` value to `system.distro`.
- [ ] **Changelog check in CI.** Fail or warn on a PR that changes `scripts/`,
  `site/`, `templates/`, or catalog rules without touching `CHANGELOG.md`.
- [ ] **Branch protection** (manual repo setting): mark the four PR checks
  (Catalog entries, Benchmark results, Build and tests, Blog) as required on
  `main`. Checked 2026-10-13: `main` has no protection or rulesets.

## Recently completed

- **v1.5.0.0 (2026-10-16, branch `fix/dataset-jsonld`): Dataset JSON-LD**
  - Added `creator` and a `CreativeWork` `license` to the dashboard's Dataset
    JSON-LD after Google Search flagged them as missing.
  - Follow-up: after deploy, run the Rich Results Test on the homepage and
    click "Validate fix" in Search Console.
- **v1.4.0.0 (2026-10-15, branch `docs/readme-cleanup`): README overview**
  - README cut to a short overview with an endpoint table, a "where the
    rules live" table, grouped local setup, and a repository layout. Catalog
    notes moved to `data/gpus/README.md`; schema history and fixture details
    stay in `docs/COPILOT_HANDOFF.md` only.

- **v1.3.0.0 (2026-10-15, branch `feat/cc-by-license`): CC BY 4.0 data license**
  - Data license CC0 → CC BY 4.0 with reasonable attribution (AI training
    explicitly permitted), the `/license/` page, `_license` and `_source` in
    every API file (schema 0.16), plain-English terms on the dashboard, the
    issue form, and the docs, and copyright lines on blog posts.

- **v1.3.0.0 (2026-10-15, branch `feat/benchmark-issue-form`): benchmark issue form**
  - "Benchmark result" issue form, `benchmark-issue.yml`, and
    `scripts/issue_to_result.py`: an issue becomes a checked community file
    and a bot pull request from a GitHub App, with no Cloudflare preview. The
    form's Game field takes a `game_id` or registry name; only listed games.
  - `.github/CODEOWNERS` as the maintainer list.
- **v1.2.0.0 (2026-10-15, branch `feat/game-registry`): game registry**
  - `data/games.yaml` with `id`, `name`, `type`, `year`, and optional
    `steam_appid`, `igdb_id`, `url`, `notes`; results use `game_id`
    (schema 0.15). This unblocks the benchmark issue form PR (#25).

- **v1.1.0.0 (2026-10-14, branch `feature/blog`)**
  - `/blog/` (Astro) with posts, guides, reviews, tags, RSS, `<BenchChart>`,
    `<Callout>`, `<AffiliateLink>` and its disclosure banner, and the AI-use
    footer. The first post, "Why I'm Starting Open GPU Benchmarks".
  - `MAJOR.MINOR.DATA.POST` versioning and the **Blog** PR check.
  - Featured GPU picks panel (`data/picks.yaml`, schema 0.13) replacing the
    empty reviews panel.
  - `LICENSE` (MIT, code) and `data/LICENSE` (CC0, data), the license in the
    JSON-LD and API metadata, plain-English submission terms, and a pull
    request template.

- **v1.0.0 (2026-10-14, branch `release/1.0.0`)**
  - Catalog reset to the GeForce RTX 5080 Founders Edition, with its first
    33 official Cyberpunk 2077 runs (29 summaries).
  - `scripts/import_cyberpunk.py` and `docs/CYBERPUNK_BENCHMARK.md`.

- **Unreleased (branch `feature/cloudflare-pages`, 2026-10-13)**
  - Cloudflare Pages deploy and the opengpubenchmarks.com canonical domain,
    owner-only PR previews, SEO meta and JSON-LD, robots.txt allowing AI
    crawlers, and generated `benchmarks/index.html`, `llms.txt`, `llms-full.txt`,
    and `sitemap.xml`.
- **Unreleased (branch `chore/test-fixtures`, 2026-10-13)**
  - Synthetic runs moved to `tests/fixtures/data/` (with a catalog snapshot);
    `data/` holds only real data. `--data-dir` on `build.py` and
    `validate.py`, fixture builds in a temp folder, a no-synthetic-in-`data/`
    test, and a "No benchmarks published yet" dashboard state.
- **Unreleased (branch `feature/anonymous-submissions`, 2026-10-13)**
  - Anonymous community submissions: optional `submitted_by`, username-free
    file names, and only five required fields.
  - Found results with a `credit.source_url` and no permission needed, plus
    a template.
  - Upscaling off by default (`preset_upscaling: true` to allow it), now a
    grouping key; `proof_level: none` ("Unverified"); schema 0.12.
- **Unreleased (branch `chore/python-venv`, 2026-10-13)**
  - Python setup: `requirements.txt`, CI installs from it, and `.venv`
    create/activate/deactivate documented; agents stop servers and
    `deactivate` before finishing.
- **Unreleased (merged in PR #13, 2026-10-13)**
  - Average-FPS-only results (`p1_low` optional) and 3DMark Steel Nomad runs,
    with a template.
  - A required `proof.method` with ten capture tools; frame-time tools must
    include `p1_low`.
  - Permission-based third-party submissions: the `credit` block with proof of
    permission, its checks, API fields, and "Name (via @user)" on the
    dashboard.
  - Community outlier limit set to 25%.
- **v0.6.0 (2026-10-08)**
  - Catalog plan step 4: Linux vs Windows. `system.os` is required and
    a grouping key, plus OS detail fields, the `result-os`,
    `result-os-field`, and `result-system-field` checks, dashboard OS chips,
    badges, and striped Linux bars, schema 0.10, and six paired synthetic Linux
    runs.
  - Fixed MangoHud (and detailed PresentMon) parsing to 0 FPS in `parse.py`.
  - Avg FPS and 1% low overlaid in one bar per GPU.
  - Catalog plan step 3: `sources` on every catalog entry, `source-invalid`
    and `sources-missing` checks, and source links in the dashboard.
  - `AGENTS.md`.
- **v0.5.0 (2026-10-08)**
  - Catalog plan step 1: per-product catalog files, product-level IDs, shared
    checks in `scripts/checks.py`, and three PR checks.
  - Catalog plan step 2: reference files with `base`, `platform`,
    `board_partner`, and `skus`.
  - Per-card dashboard spec table.
  - Site favicon.
