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

- [ ] **Require `sources`.** Turn the `sources-missing` warning into an
  error once the maintainer has re-validated the current sources by hand.
- [ ] **Re-validate catalog sources by hand.** The current sources were added
  on 2026-10-08. TechPowerUp blocks scripts, so those URLs were confirmed by
  page title and their values through search results. Also find a source for
  the `z1_extreme` silicon specs (die size, transistors, shader counts), and
  for any value not yet listed in a `covers`.
- [ ] **Replace `_generic` laptop IDs** with real laptop models, then turn the
  `id-generic` warning into an error.

## Data and submissions

- [ ] **Permission-based third-party submissions.** Let a maintainer add
  benchmarks on behalf of someone else, such as a YouTube channel or another
  user who has given permission. Today `submitted_by` must be the GitHub user
  opening the PR, and the file name must end with that username. This needs:
  - a way to credit the original source: name, channel or profile URL, and a
    link to the video or post
  - a record that permission was given
  - check and file-name rules that allow the PR author and the credited source
    to differ
  - updated contributor docs: `CONTRIBUTING.md`,
    `docs/COMMUNITY_SUBMISSIONS.md`, and `data/community/README.md`
  - dashboard and API attribution for the credited source
- [ ] **Simple benchmark submission flow (no PRs).** PRs are too complex for
  most people. Build a low-friction way to get benchmarks in.
  - Goal: a contributor with a PresentMon/MangoHud capture (or typed-in
    numbers) submits without forking, branching, or writing YAML.
  - Options to evaluate: a GitHub issue form (`.github/ISSUE_TEMPLATE/*.yml`)
    with an Action that parses the issue, runs `scripts/checks.py`, and opens
    the PR on the submitter's behalf; or a static web form on the dashboard
    that generates the result YAML (using `parse.py` logic) for download or
    prefilled issue.
  - Must keep: `submitted_by` set from the issue author, correct file name
    `result_YYYYMMDD_<game>_<github_user>.yaml`, required `system.os`,
    `frame_generation: false`, and raw capture attachment preserved under
    `data/community/<gpu_id>/raw/`.
  - Feedback: post validation errors back on the issue in plain language.
  - Docs: update `CONTRIBUTING.md`, `docs/COMMUNITY_SUBMISSIONS.md`,
    `data/community/README.md`; add rules to `data/gpus/README.md` if new
    checks appear.
  - Done when: a first-time user can submit one run end to end from the
    browser and a maintainer only has to review and merge.
- [ ] **Flesh out official benchmarks and cross-check them against community
  data.** Official runs must stay close to community runs for the same
  product, game, resolution, preset, and OS.
  - Add a check in `scripts/checks.py` (run by `build.py` and `validate.py`)
    that compares each official summary (avg FPS and 1% low) with the
    community summary for the same group key. Flag when the difference
    exceeds a threshold (start with a configurable percentage, for example
    10 to 15 percent, and require a minimum community sample count, such as
    3 runs, so thin data doesn't trigger it).
  - Severity: a warning locally and in the PR check, with a clear message
    naming the official file, the community median, and the percent gap.
    Decide whether large gaps (for example over 25 percent) become errors.
  - Message must tell the user the next step: re-check the submission or
    open a GitHub issue asking the maintainer to review the official
    benchmark. Add an issue template for "Official benchmark review".
  - Outliers: support pulling an official run out of summaries (for example
    an `excluded: true` plus `excluded_reason` field) while keeping the file
    and its raw evidence.
  - Add a ``#### `rule-name` `` heading for each new rule in
    `data/gpus/README.md` or `docs/COMMUNITY_SUBMISSIONS.md`, tests in
    `scripts/test_build.py`, and document the policy for what "official"
    means (who may add them, required raw evidence, test-bench spec).
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
- [ ] **Roll-up view by GPU model.** Group products that share a `base`
  reference, for example every RTX 5060 Ti 16 GB board, and compare boards
  of the same GPU side by side.

## Content and outreach

- [ ] **Blog, reviews, and possibly a YouTube channel.** Show people the
  benchmarks and how to read them.
  - Decide the home: a `site/blog/` section on the same static site (Markdown
    or HTML rendered at build time, no new backend), with posts in a
    `content/` folder.
  - Reviews: reuse `data/reviews.yaml` to link published reviews to products,
    and show them on the dashboard and blog.
  - Define post types: GPU reviews, methodology, data roundups, and
    submission how-tos.
  - YouTube: plan episodes that point back to the dashboard, and consider
    the permission-based third-party submissions item above for crediting
    video sources.
  - Keep GitHub links absolute and site links relative so a custom domain
    works.

## Dashboard

- [ ] **Linux vs Windows comparison view.** Show the percentage difference per
  product and game wherever both OSes have results.
- [ ] **Per-GPU or per-vendor icons** in the table and chart labels. The site
  favicon shipped in v0.5.0.
- [ ] **Rename "Benchmark summaries".** The table is now a per-card spec and
  results table, so give the section a more meaningful heading.
- [ ] **Make the table search more noticeable.** Widen the search input so it
  stands out as the table grows.
- [ ] **Remove the six-GPU selection limit.** Let users pin more than six GPUs
  to the top of the chart and table.
- [ ] **Fix the chart legend.** The "Official" and "Community" swatches
  above the chart don't match the bars, which are colored by GPU vendor.
  Either color by source, or show a vendor legend.
- [ ] **Phone-width layout scrolls sideways.** At 390 px the header buttons
  and toolbar are wider than the screen, so the whole page scrolls
  horizontally. This happens on `main` too.

## Tooling and bugs

- [ ] **Read more of the MangoHud log header in `parse.py`.** It already
  copies `kernel` and `driver`. The header block also has `os`, `cpu`, `gpu`,
  and `ram`; map `cpu` to `system.cpu`, `ram` to `system.memory`, and a
  SteamOS/distro `os` value to `system.distro`.
- [ ] **Clear stale build output.** `build.py` never deletes old files under
  `site/api/v1/`. After an ID rename, a local preview still serves the old
  per-product `summary.json` files. CI is unaffected because it starts from a
  clean checkout. Fix: clear `OUTPUT_DIR` at the start of a successful build.
- [ ] **Changelog check in CI.** Fail or warn on a PR that changes `scripts/`,
  `site/`, `templates/`, or catalog rules without touching `CHANGELOG.md`.
- [ ] **Python virtual environment.**
  - Add a `.venv` setup and ignore it in `.gitignore`.
  - Document `python -m venv .venv` and activation in `README.md` and
    `CONTRIBUTING.md`.
  - Consider a `requirements.txt` for `pyyaml` and `numpy`, and use it in
    both CI workflows.
- [ ] **Branch protection** (manual repo setting): mark the three PR checks
  (Catalog entries, Benchmark results, Build and tests) as required on
  `main`.

## Recently completed

- **v0.5.0 (2026-10-08)**
  - Catalog plan step 1: per-product catalog files, product-level IDs, shared
    checks in `scripts/checks.py`, and three PR checks.
  - Catalog plan step 2: reference files with `base`, `platform`,
    `board_partner`, and `skus`.
  - Per-card dashboard spec table.
  - Site favicon.
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
