# Open GPU Benchmarks agent instructions

## Start here

Read [README.md](../README.md), [docs/COPILOT_HANDOFF.md](../docs/COPILOT_HANDOFF.md),
and [docs/COMMUNITY_SUBMISSIONS.md](../docs/COMMUNITY_SUBMISSIONS.md) before
changing the data schema, build logic, validation, or dashboard behavior.

## Data and schema rules

- The source schema uses `graphics_preset`; do not add a `settings` fallback.
- Desktop and laptop GPU records never share a summary group.
- Frame generation must be disabled for comparable benchmark runs.
- Keep exact machine metadata with each run while charts display grouped
  summaries.
- Treat raw capture evidence as preferred and preserve its reference when
  correcting or removing a record.
- Community result files require `submitted_by` (the submitter's GitHub
  username) and must be named `result_YYYYMMDD_<game>_<github_user>.yaml`;
  same-day repeats put a number before the username.
- Catalog specs live in nested `data/gpus.yaml` sections (`identity`,
  `classification`, `silicon`, `memory`, `clocks`, `power`, `release`,
  `features`); new GPUs must fill every required leaf and quote every date
  so YAML keeps it a string.
- Dashboard links to GitHub are absolute; API links stay relative so the site
  works on a custom domain.

## Version and release housekeeping

Record every behavioral, data-contract, dashboard, or workflow change under
`Unreleased` in [CHANGELOG.md](../CHANGELOG.md).

For a versioned dashboard change:

1. Rename `Unreleased` in `CHANGELOG.md` to the new version and date, then add
   a fresh empty `Unreleased` section.
2. Update `RELEASE_VERSION` in `scripts/build.py`.
3. Increment `SCHEMA_VERSION` when the generated API payload changes.
4. Update the current-version references, fixture counts, and feature summary
   in `README.md` and `docs/COPILOT_HANDOFF.md`.
5. Run:

   ```powershell
   python scripts/build.py
   python scripts/validate.py
   python scripts/test_build.py
   python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
   git diff --check
   ```

6. Do not commit generated `site/api/` files unless repository policy changes.
7. Create a Git tag only when explicitly requested after the commit is
   reviewed.
