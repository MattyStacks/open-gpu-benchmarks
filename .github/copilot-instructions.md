# Open GPU Benchmarks agent instructions

## Start here

Read [README.md](../README.md), [docs/COPILOT_HANDOFF.md](../docs/COPILOT_HANDOFF.md),
[docs/COMMUNITY_SUBMISSIONS.md](../docs/COMMUNITY_SUBMISSIONS.md), and
[data/gpus/README.md](../data/gpus/README.md) before changing the data schema,
build logic, validation, or dashboard behavior. These rules apply to every AI
agent, not just Copilot; [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
point here.

## Every change: update the changelog and the backlog

These two steps are required, not optional, for every PR an agent or a person
prepares:

1. **[CHANGELOG.md](../CHANGELOG.md)** — add a line under `Unreleased` for any change to
   behavior, the data contract, the API schema, the dashboard, the checks, the
   templates, or the contributor workflow. Data-only result submissions are the
   only exception. Don't finish a task with an empty `Unreleased` section if
   you changed any of those.
2. **[docs/TODO.md](../docs/TODO.md)** (the backlog) — remove items you completed, and
   add anything you deferred, found broken, or were asked to do later.

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
- The catalog is one file per product at
  `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`; the file name equals `id`
  and the folders equal `classification.form_factor` and
  `identity.gpu_vendor` (the GPU chip maker, never the board or device maker).
- IDs are product-level and include exactly one `<N>gb` token equal to
  `memory.capacity_gb`. Different memory sizes or board makers are different
  IDs and are never averaged together. Patterns: desktop
  `<gpu_model>_<vram>gb_<brand>_<product_line>` (`_fe`/`_reference`/`_le` for
  the vendor's own card), laptop `<gpu_model>_<vram>gb_<oem>_<model>` (temporary
  `_generic` allowed with a warning), handheld `<device>_<chip>_<ram>gb`.
  Handheld RAM is in the ID (soldered); laptop system RAM is recorded per run.
- Catalog specs are nested (`identity`, `classification`, `silicon`, `memory`,
  `clocks`, `power`, `release`, `features`). Only `id`, `identity.name`,
  `identity.gpu_vendor`, `classification.form_factor`, and
  `memory.capacity_gb` are required; unknown fields are rejected. Quote every
  date and version number.
- Data and templates use block-style YAML only: no inline `[ ]` or `{ }`.
- Shared chip specs live in `data/gpus/reference/<gpu_vendor>/<ref_id>.yaml`.
  Products inherit them with `base: <ref_id>`, deep-merged (product wins,
  lists replaced whole). References need only `id`, `identity.name`, and
  `identity.gpu_vendor`, and may not carry `base`, `skus`, `platform`,
  `identity.board_partner`, or `classification.form_factor`. Results never
  point at a reference ID.
- `platform` (device specs) is only for handheld and laptop products;
  `identity.board_partner` is only for desktop products.
- Every catalog file lists `sources`: a block list of `{url, title, accessed,
  covers}` with `https://` URLs. Only cite pages you actually used, and only
  list sections in `covers` that the page backs. Never invent a source or a
  spec value; leave unknown values out. A missing `sources` list is a warning
  for now.
- Every check rule lives once in `scripts/checks.py` (used by `build.py` and
  `validate.py`). Each rule name needs a ``#### `rule-name` `` heading in
  `data/gpus/README.md` or `docs/COMMUNITY_SUBMISSIONS.md`; `test_build.py`
  enforces it. The build stops before writing `site/api/` on any error.
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
   python scripts/validate.py
   python scripts/build.py
   python scripts/test_build.py
   python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
   git diff --check
   ```

6. Do not commit generated `site/api/` files unless repository policy changes.
7. Create a Git tag only when explicitly requested after the commit is
   reviewed.
