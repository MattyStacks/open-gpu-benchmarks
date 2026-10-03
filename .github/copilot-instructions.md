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

## Version and release housekeeping

For a versioned dashboard change:

1. Update `RELEASE_VERSION` in `scripts/build.py`.
2. Increment `SCHEMA_VERSION` when the generated API payload changes.
3. Update the current-version references, fixture counts, and feature summary
   in `README.md` and `docs/COPILOT_HANDOFF.md`.
4. Run:

   ```powershell
   python scripts/build.py
   python scripts/validate.py
   python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
   git diff --check
   ```

5. Do not commit generated `site/api/` files unless repository policy changes.
6. Create a Git tag only when explicitly requested after the commit is
   reviewed.
