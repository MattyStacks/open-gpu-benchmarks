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

- `data/` holds only real data, because it's what deploys. Synthetic test runs
  live in `tests/fixtures/data/` (same layout, its own catalog snapshot);
  `test_build.py` builds them into a temp folder, never `site/api/`, and fails
  if a `synthetic: true` run appears in `data/`. Preview them with
  `python scripts/build.py --data-dir tests/fixtures/data`.
- The source schema uses `graphics_preset`; do not add a `settings` fallback.
- Desktop and laptop GPU records never share a summary group.
- Game runs require `system.os`: `windows` or `linux`, lowercase. The OS is a
  grouping key, so Windows and Linux runs are never averaged together; the
  distro, kernel, Mesa, and Proton are per-run detail fields, never grouping
  keys or extra chart bars. Linux-only fields on a windows run (or the
  reverse) are errors. Per-distro comparisons are DIY from the JSON.
- Frame generation must be disabled for comparable benchmark runs.
- `avg_fps` is required on every result entry; `p1_low` is optional (3DMark
  and in-game benchmarks report none) and is `null` in the API when missing.
  `proof.method` is required on every game run and says which tool captured it
  (`checks.PROOF_METHODS`: PresentMon, CapFrameX, FrameView, MSI Afterburner,
  AMD Adrenalin, MangoHud, OCAT, in-game benchmark, synthetic benchmark, or
  other); PresentMon is the recommended default, and the method is never a
  grouping key. Frame-time tools (`checks.P1_LOW_METHODS`) must include
  `p1_low` (`result-p1-low-required`); the rest only warn. A 3DMark run is
  a normal game run (`game: 3DMark Steel Nomad`) with the graphics-test FPS as
  `avg_fps` and the result URL as `proof.summary_source`.
- A community average more than 25% from the matching official average fails
  `community-outlier` (`OUTLIER_RATIO` in `scripts/checks.py`).
- Keep exact machine metadata with each run while charts display grouped
  summaries.
- Treat raw capture evidence as preferred and preserve its reference when
  correcting or removing a record.
- Community result files are anonymous by default and named
  `result_YYYYMMDD_<game>.yaml` (same-day repeats add `_2`, `_3`).
  `submitted_by` is optional and must be a valid GitHub username when set.
  Only `gpu_id`, `game`, the `result` list, `system.os`, and `proof.method`
  are required; community runs with no evidence get `proof_level: none`
  ("Unverified"). Official runs are maintainer-verified by definition
  (`maintainer-verified`, "Verified") and may carry a `credit` with just a
  `name` for a run entered on someone's behalf.
  A result someone else measured adds a `credit` block with an https
  `source_url` saying where it was found (no permission needed); unpublished
  numbers give `permission` (at least one of `url`, `screenshot`, `note`)
  instead. `name` and `url` are optional. Example credits use made-up names
  and `example.com` URLs, never a real creator.
- Upscaling is off by default. `upscaling` is allowed only with
  `preset_upscaling: true` (the graphics preset turned it on); otherwise
  `result-upscaling` fails. Upscaling is a grouping key.
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
  works on every host. The canonical origin is `https://opengpubenchmarks.com/`
  (`build.SITE_URL`). The canonical link, `og:url`, and JSON-LD in
  `site/index.html`, plus `site/robots.txt` and the generated sitemap and
  pages, are the only absolute site URLs, and `test_build.py` checks they
  agree. robots.txt never disallows crawlers: AI tools are meant to use the
  site.
- `build.py` writes `benchmarks.html`, `llms.txt`, `llms-full.txt`, and
  `sitemap.xml` into `site/` from the dashboard summaries (gitignored, like
  `site/api/`). Keep them in step with any dashboard field change.
- Deploys: `build.yml` publishes `main` to GitHub Pages and Cloudflare Pages.
  `preview.yml` deploys Cloudflare previews only for the owner's own
  same-repo PRs. Never switch it to `pull_request_target`.

## Version and release housekeeping

Record every behavioral, data-contract, dashboard, or workflow change under
`Unreleased` in [CHANGELOG.md](../CHANGELOG.md).

For a versioned dashboard change:

1. Rename `Unreleased` in `CHANGELOG.md` to the new version and date, then add
   a fresh empty `Unreleased` section.
2. Update `RELEASE_VERSION` in `scripts/build.py`.
3. Increment `SCHEMA_VERSION` when the generated API payload changes.
4. Update the current-version references, published and fixture counts, and feature summary
   in `README.md` and `docs/COPILOT_HANDOFF.md`.
5. Run, inside the activated `.venv` (create it once with
   `python -m venv .venv`):

   ```powershell
   .venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
   python -m pip install -r requirements.txt
   python scripts/validate.py
   python scripts/build.py
   python scripts/test_build.py
   python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
   git diff --check
   ```

6. Do not commit generated `site/api/` files unless repository policy changes.
7. Create a Git tag only when explicitly requested after the commit is
   reviewed.

## Python environment and cleanup

- Dependencies are listed once in `requirements.txt`. Run every script inside
  the project's `.venv` virtual environment, not the global Python; never
  commit `.venv/`.
- Before you report a task complete, stop every server or background process
  you started (for example the `python -m http.server 8000 --directory site`
  preview), then run `deactivate` to leave the virtual environment.
