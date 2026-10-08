# Changelog

High-level, user-facing changes by version, newest first. Details live in git
history and pull requests. Follows [Keep a Changelog](https://keepachangelog.com/)
headings (Added, Changed, Removed, Fixed).

**Every PR updates this file.** Contributors and AI agents (Claude, Copilot,
or any other) add a line under `Unreleased` in every PR that changes behavior,
the data contract, the API schema, the dashboard, the checks, or the
contributor workflow. Data-only result submissions can skip it. When the
version is bumped, rename `Unreleased` to the new version and date, then start
a fresh empty `Unreleased` section.

## Unreleased

_Nothing yet._

## 0.5.0 - 2026-10-08

Per-product catalog: every card, laptop, and handheld is its own file and its
own benchmark group, with shared chip specs in reference files and checks that
report every problem at once.

### Added
- **Per-product GPU catalog.** One file per card, laptop, or handheld at
  `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. `data/gpus/README.md`
  documents the ID rules, a field reference, and every check.
- **Reference files** under `data/gpus/reference/<gpu_vendor>/` hold the specs
  shared by every product built on one GPU. Products inherit them with `base:`
  and list only what they change or add. Nine references were split out of the
  existing entries, including `z1_extreme`, now shared by the ROG Ally and the
  Legion Go.
- **Device specs.** A `platform` section for handhelds and laptops covers
  maker, CPU, RAM speed, OS shipped, display, power range, and battery. The
  dashboard's expanded row shows it as a "Device" grid. Desktop cards get
  `identity.board_partner`, and any product can list variants that share an
  entry under `skus`.
- **Full hardware specs per card** in nested sections (`identity`,
  `classification`, `silicon`, `memory`, `clocks`, `power`, `release`,
  `features`), backfilled for all 11 entries.
- **Dashboard spec table.**
  - Per-card columns: vendor, form, architecture, VRAM, bus, bandwidth,
    clocks, shaders, RT cores, TDP, process, release, and MSRP.
  - Every column sorts.
  - Search covers IDs, codenames, and architectures.
  - Expanding a row shows the silicon details, price history, device specs,
    and the exact runs behind the number.
- **Shared checks** in `scripts/checks.py`.
  - Both `build.py` and `validate.py` use them.
  - Each run reports every problem at once, tagged with a rule name that
    links to its explanation.
  - The build stops without writing `site/api/` when any error exists.
- **New check rules.**
  - Block-style YAML only: inline `[ ]` and `{ }` are rejected.
  - Unknown catalog fields are rejected.
  - Stray files in result folders, which the build would silently skip, are
    flagged.
  - Reference rules: `base-unknown`, `base-mismatch`, `reference-field`, and
    `field-not-allowed`.
  - `result-reference-id` rejects results that point at a reference file.
  - Range checks for the `platform` fields.
- **Validation commands.** `validate.py catalog` and `validate.py results` run
  each half on its own. Official result files are now checked too.
- **CI.** Pull requests show three separate checks: **Catalog entries**,
  **Benchmark results**, and **Build and tests**. The deploy workflow now
  validates the data before building.
- **Templates.** Catalog templates for desktop, laptop, handheld, and
  reference entries.
- **Contributor guide.** New section, "Adding a card, laptop, or handheld",
  with worked examples and a guide to reading a failed check.
- **Site favicon** (`site/favicons/`): an SVG icon that follows the dashboard's
  light/dark toggle, with ICO and Apple touch icon fallbacks.
- **`AGENTS.md`**: a tool-neutral entry point for AI agents, pointing to the
  shared rules, the changelog requirement, and the backlog.

### Changed
- **API schema.** The schema is now `0.8`. It passed through three versions in
  this release:
  - `0.6`: catalog specs are nested. Run records keep flat `vram_gb` and
    `tdp_w`; `vram_gb` is null for shared-memory handhelds instead of 0.
  - `0.7`: IDs are product-level and the vendor field is `gpu_vendor`.
  - `0.8`: `gpus.json` entries carry `base`, `board_partner`, `skus`, and
    `platform`, already merged with their reference.
- **Product-level IDs that include the memory size.** For example, `rtx_4090`
  became `rtx_4090_24gb_fe` and `legion_go` became
  `legion_go_z1_extreme_16gb`. Different memory sizes and board makers are
  never averaged together. Result folders were renamed to match. Laptops with
  an unknown model use a temporary `_generic` ID.
- **Vendor field renamed.** `identity.vendor` is now `identity.gpu_vendor`,
  and run records carry `gpu_vendor` instead of `vendor`.
- **Product names.** The vendors' own cards are now named "Founders Edition",
  "Limited Edition", and "(AMD reference)".
- **Required fields.** Only five catalog fields are required: `id`,
  `identity.name`, `identity.gpu_vendor`, `classification.form_factor`, and
  `memory.capacity_gb`. The dashboard shows `—` for anything missing.
- **`parse.py`** rejects IDs that aren't in the catalog and takes the form
  factor from the catalog entry.
- **`CONTRIBUTING.md`** is rewritten around submitting a result:
  - a 5-step flow with a diagram
  - visuals for the file name and folder
  - validated desktop, laptop, handheld, and summary-only examples
  - a table of required fields and a table of common mistakes

  `data/community/README.md` now points to it.

### Removed
- `data/gpus.yaml`, replaced by the per-product catalog.

## 0.4.0 - 2026-10-03

### Added
- Community result files require `submitted_by` (the submitter's GitHub
  username); file names end with the same username:
  `result_YYYYMMDD_<game>_<github_user>.yaml`. The validator enforces both.
- API schema `0.5`: `submitted_by` on every run record and a `contributors` list
  on every grouped summary.
- Dashboard "Get the data as JSON" panel with Open and Copy URL actions for each
  endpoint, plus `curl` and `fetch` examples.
- Dashboard header and footer links to the GitHub repository, contributing
  guide, and issues.
- `docs/TODO.md` for deferred work.
- This changelog.

### Changed
- `scripts/parse.py` requires `--submitted-by` and uses the new file name.
- Renamed all community fixtures to the new naming scheme.

### Removed
- The "Desktop vs Laptop vs Handheld" tagline from the dashboard header.

## 0.3.0

### Changed
- Restructured results by GPU: `data/official/<gpu_id>/` and
  `data/community/<gpu_id>/`, with generated per-GPU summary JSON and a
  GPU-rooted master API (`gpus.json`).
- Each result file holds a `result` list of resolution/preset profiles that are
  validated and grouped independently.

### Added
- `CLAUDE.md` agent entry point.

## 0.2.0

### Added
- Graphics preset filter and community submission guidance.
- Chart bars colored by GPU vendor.

## 0.1.0

### Added
- Initial data-driven benchmark dashboard on GitHub Pages, built from reviewable
  YAML.
