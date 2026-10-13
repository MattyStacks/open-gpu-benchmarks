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

- [ ] **Re-validate catalog sources by hand.** The current sources were added
  on 2026-10-08. TechPowerUp blocks scripts, so those URLs were confirmed by
  page title and their values through search results. Also find a source for
  the `z1_extreme` silicon specs (die size, transistors, shader counts), and
  for any value not yet listed in a `covers`.
- [ ] **Require `sources`.** After the re-validation above, turn the
  `sources-missing` warning into an error.
- [ ] **Replace `_generic` laptop IDs** (`arc_a770m_16gb_generic`,
  `rtx_4070_laptop_8gb_generic`, `rtx_4090_laptop_16gb_generic`) with real
  laptop models, then make every `_generic` laptop ID an `id-generic` error
  instead of a warning.

## 3DMark and capture tools

Follow-ups to average-only results and `proof.method` (PR #13).

- [ ] **Add the RTX 5080 and the first Steel Nomad run.** The catalog has no
  RTX 5080 entry yet. Add one (with sources), then add the maintainer's Steel
  Nomad run (8603 score, 86.03 FPS) as community data with its 3DMark result
  URL as `proof.summary_source`. Also add an official Steel Nomad baseline per
  catalog GPU, since without one the run only gets `result-no-baseline`.
- [ ] **Confirm 3DMark fixed settings.** Check the fixed render resolution and
  preset for Steel Nomad, Steel Nomad Light, and the other benchmarks people
  will submit, and list them in `docs/COMMUNITY_SUBMISSIONS.md`. The Steel
  Nomad template's `1440p` is unconfirmed. Consider a check that rejects a
  3DMark `game` with the wrong resolution.
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

- [ ] **Simple benchmark submission flow (no PRs).** PRs are too complex for
  most people. Build a low-friction way to get benchmarks in.
  - Goal: a contributor with a capture (or typed-in numbers) submits without
    forking, branching, or writing YAML.
  - Options to evaluate: a GitHub issue form (`.github/ISSUE_TEMPLATE/*.yml`)
    with an Action that parses the issue, runs `scripts/checks.py`, and opens
    the PR on the submitter's behalf; or a static web form on the dashboard
    that generates the result YAML (using `parse.py` logic) for download or
    prefilled issue.
  - Anonymity: submissions are anonymous by default, so don't copy the issue
    author into `submitted_by` unless they ask. A bot that commits issue-form
    results also keeps the submitter out of the commit history, which a PR
    can't (GitHub shows the PR author and commit email). Consider a
    "Submit a result you found" form that asks for `credit.source_url`.
  - Must keep: file name `result_YYYYMMDD_<game>.yaml`, required `system.os`
    and `proof.method`, frame generation and upscaling off (or
    `preset_upscaling: true`), an optional `credit` block for found results,
    and raw capture attachments preserved under
    `data/community/<gpu_id>/raw/`.
  - Feedback: post validation errors back on the issue in plain language.
  - Docs: update `CONTRIBUTING.md`, `docs/COMMUNITY_SUBMISSIONS.md`,
    `data/community/README.md`; add rule headings for any new checks.
  - Done when: a first-time user can submit one run end to end from the
    browser and a maintainer only has to review and merge.
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

- [ ] **Blog, reviews, and possibly a YouTube channel.** Show people the
  benchmarks and how to read them.
  - Decide the home: a `site/blog/` section on the same static site (Markdown
    or HTML rendered at build time, no new backend), with posts in a
    `content/` folder.
  - Reviews: `data/reviews.yaml` already feeds the dashboard's reviews panel
    (empty so far). Link published reviews to products, and show them on the
    blog too.
  - Define post types: GPU reviews, methodology, data roundups, and
    submission how-tos.
  - YouTube: plan episodes that point back to the dashboard. Video sources can
    be credited with the `credit` block (see
    `docs/COMMUNITY_SUBMISSIONS.md`), with permission.
  - Keep GitHub links absolute and site links relative so a custom domain
    works.

## Tooling and bugs

- [ ] **Clear stale build output.** `build.py` never deletes old files under
  `site/api/v1/`. After an ID rename, a local preview still serves the old
  per-product `summary.json` files. CI is unaffected because it starts from a
  clean checkout. Fix: clear `OUTPUT_DIR` at the start of a successful build.
- [ ] **Read more of the MangoHud log header in `parse.py`.** It already
  copies `kernel` and `driver`. The header block also has `os`, `cpu`, `gpu`,
  and `ram`; map `cpu` to `system.cpu`, `ram` to `system.memory`, and a
  SteamOS/distro `os` value to `system.distro`.
- [ ] **Changelog check in CI.** Fail or warn on a PR that changes `scripts/`,
  `site/`, `templates/`, or catalog rules without touching `CHANGELOG.md`.
- [ ] **Branch protection** (manual repo setting): mark the three PR checks
  (Catalog entries, Benchmark results, Build and tests) as required on
  `main`. Checked 2026-10-13: `main` has no protection or rulesets.

## Recently completed

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
