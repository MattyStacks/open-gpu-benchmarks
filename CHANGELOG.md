# Changelog

High-level, user-facing changes by version, newest first. Details live in git
history and pull requests. Follows [Keep a Changelog](https://keepachangelog.com/)
headings (Added, Changed, Removed, Fixed).

**Contributors and agents:** add a line under `Unreleased` in every PR that
changes behavior, the data contract, the dashboard, or the contributor
workflow. When the version is bumped, rename `Unreleased` to the new version
and date and start a fresh `Unreleased` section.

## Unreleased

### Added
- Per-product GPU catalog: one file per card, laptop, or handheld at
  `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`, documented in
  `data/gpus/README.md` with the ID rules, a field reference, and an
  explanation of every check.
- `scripts/checks.py`: every catalog and result rule in one place. Both
  `build.py` and `validate.py` use it. Each run reports all problems at once,
  each tagged with a rule name that links to its explanation, and the build
  stops without writing `site/api/` when any error exists.
- `validate.py catalog` and `validate.py results` subcommands. Official
  result files are now checked as well.
- New checks: block-style YAML only (inline `[ ]` and `{ }` are rejected),
  unknown catalog fields are rejected, and stray YAML files in result
  folders that the build would silently skip are flagged.
- Three separate pull-request checks: **Catalog entries**, **Benchmark
  results**, and **Build and tests**. The deploy workflow now validates data
  before building.
- Catalog templates for desktop, laptop, and handheld entries.
- Contributor guide section "Adding a card, laptop, or handheld", with
  worked examples and a guide to reading a failed check.
- Site favicon (`site/favicons/`): an SVG icon that follows the dashboard's
  light/dark toggle, with ICO and Apple touch icon fallbacks.
- Expanded GPU catalog: `data/gpus.yaml` now carries full per-card specs in
  nested sections (`identity`, `classification`, `silicon`, `memory`,
  `clocks`, `power`, `release`, `features`), backfilled for all 11 cards.
  The build and validator enforce types and ranges. Later in this release
  the catalog was split into per-product files (see below).
- Dashboard benchmark table now shows per-card spec columns (vendor, form,
  architecture, VRAM, bus, bandwidth, clocks, shaders, RT cores, TDP,
  process, release, MSRP) next to each result. Columns sort, search covers
  IDs, codenames, and architectures, and expanding a row reveals a silicon
  deep dive, price history, and the exact runs behind the number.

### Changed
- API schema `0.7`. Catalog IDs are now product-level and include the memory
  size (`rtx_4090` became `rtx_4090_24gb_fe`; `legion_go` became
  `legion_go_z1_extreme_16gb`), so different memory sizes and board makers
  are never averaged together. Result folders were renamed to match.
  Laptops whose model is unknown use a temporary `_generic` ID.
- `identity.vendor` is now `identity.gpu_vendor`, and run records carry
  `gpu_vendor` instead of `vendor`.
- Only five catalog fields are required (`id`, `identity.name`,
  `identity.gpu_vendor`, `classification.form_factor`,
  `memory.capacity_gb`). The dashboard shows `—` for anything missing.
- `parse.py` rejects IDs that aren't in the catalog and takes the form factor
  from the catalog entry.
- Rewrote `CONTRIBUTING.md` around submitting a result: a 5-step flow with a
  diagram, file-name and folder visuals, validated desktop/laptop/handheld/
  summary-only examples, a required-fields table, and a common-mistakes table.
  `data/community/README.md` now points to it.
- API schema `0.6`: catalog GPUs in `gpus.json` and the per-GPU summaries
  carry nested hardware spec sections instead of flat `name`/`vendor`/
  `form_factor`/`vram_gb`/`tdp_w` fields. Run records keep their flat
  `vram_gb`/`tdp_w` values, now derived from the nested specs (`vram_gb` is
  null for shared-memory handhelds instead of 0).

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
