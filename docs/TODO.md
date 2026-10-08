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
- [ ] **Roll-up view by GPU model.** Group products that share a `base`
  reference, for example every RTX 5060 Ti 16 GB board, and compare boards
  of the same GPU side by side.

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
