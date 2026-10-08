# TODO

The backlog: deferred work that's out of scope for current PRs. Pick items up
only when asked.

**Every PR keeps this file current.** Remove items you finished, move them to
[Recently completed](#recently-completed), and add anything you deferred,
found broken, or were asked to do later. This applies to people and to every
AI agent. The same rule is in `CLAUDE.md`, `AGENTS.md`, and
`.github/copilot-instructions.md`.

## Catalog plan (next steps, one PR each)

Details are in "Planned next steps" in
[COPILOT_HANDOFF.md](COPILOT_HANDOFF.md#planned-next-steps).

- [ ] **Step 3: `sources` on catalog entries.**
  - Add a block list of `{url, title, accessed, covers}` to reference and
    product files.
  - A missing `sources` list is a warning at first.
- [ ] **Step 4: Linux vs Windows.**
  - `system.os` becomes a required grouping key.
  - Add the optional OS detail fields: distro, kernel, Mesa, Proton, and
    others.
  - Dashboard: Windows and Linux chips and an OS badge on each bar. Point to
    the JSON data for per-distro charts.
- [ ] **Require `sources`** once every catalog entry has them.
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
- [ ] **Overlay avg FPS and 1% low in one bar.** Test rendering the two
  metrics as a single overlaid bar so the chart stays compact as the GPU list
  grows.

## Tooling and bugs

- [ ] **Fix MangoHud parsing in `parse.py`.** The frame-time reader skips the
  header with `readline()` and then builds a second `DictReader`, which treats
  the first data row as the header. MangoHud captures parse to 0 FPS.
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
  - `AGENTS.md`.
