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
- [ ] **Overlay avg FPS and 1% low in one bar.** Test rendering the two
  metrics as a single overlaid bar so the chart stays compact as the GPU
  list grows.
