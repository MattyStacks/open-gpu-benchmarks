# TODO

Deferred work that is intentionally out of scope for current PRs. Pick items up
only when asked.

- [ ] **GPU icons / favicons.** Add small per-GPU (or per-vendor) icons to the
  dashboard table and chart labels, plus a site favicon.
- [ ] **Python virtual environment.** Add a `.venv` setup (and ignore it in
  `.gitignore`), and document `python -m venv .venv` plus activation in
  `README.md` and `CONTRIBUTING.md`. Consider a `requirements.txt` for
  `pyyaml` and `numpy`, and use it in both CI workflows.
- [ ] **Rename "Benchmark summaries".** The table is now a per-card spec and
  results table, so give the section a more meaningful heading.
- [ ] **Make the table search more noticeable.** Expand the search input so
  it stands out as the table grows.
- [ ] **Remove the six-GPU selection limit.** Let users pin more than six
  GPUs to the top of the chart and table.
- [ ] **Catalog plan step 2: reference files.** `data/gpus/reference/`, `base`
  merging, `platform` for handhelds and laptops, `identity.board_partner`,
  and `skus`. See "Planned next steps" in `docs/COPILOT_HANDOFF.md`.
- [ ] **Catalog plan step 3: `sources`** on catalog entries, as a warning first.
- [ ] **Catalog plan step 4: Linux vs Windows.** `system.os` as a required
  grouping key, optional OS detail fields, and dashboard OS chips and badges.
- [ ] **Linux vs Windows comparison view.** Show the percentage difference per
  product and game wherever both OSes have results.
- [ ] **Replace `_generic` laptop IDs.** Rename them to real laptop models.
  When none are left, turn the `id-generic` warning into an error.
- [ ] **Require `sources`** once every catalog entry has them.
- [ ] **Fix MangoHud parsing in `parse.py`.** The frame-time reader skips the
  header with `readline()` and then builds a second `DictReader`, which
  treats the first data row as the header, so MangoHud captures parse to
  0 FPS.
- [ ] **Permission-based third-party submissions.** Let a maintainer add
  benchmarks on behalf of someone else, such as a YouTube channel or another
  user who has given permission. Today `submitted_by` must be the GitHub
  user opening the PR, and the file name must end with that username. This
  needs:
  - a way to credit the original source (name, channel or profile URL, link
    to the video or post)
  - a record that permission was given
  - checks and file-name rules that allow the PR author and the credited
    source to differ
  - updated contributor docs (`CONTRIBUTING.md`,
    `docs/COMMUNITY_SUBMISSIONS.md`, `data/community/README.md`)
  - dashboard and API attribution for the credited source
- [ ] **Overlay avg FPS and 1% low in one bar.** Test rendering the two
  metrics as a single overlaid bar so the chart stays compact as the GPU
  list grows.
