# Changelog

High-level, user-facing changes by version, newest first. Details live in git
history and pull requests. Follows [Keep a Changelog](https://keepachangelog.com/)
headings (Added, Changed, Removed, Fixed).

**Contributors and agents:** add a line under `Unreleased` in every PR that
changes behavior, the data contract, the dashboard, or the contributor
workflow. When the version is bumped, rename `Unreleased` to the new version
and date and start a fresh `Unreleased` section.

## Unreleased

### Changed
- Rewrote `CONTRIBUTING.md` around submitting a result: a 5-step flow with a
  diagram, file-name and folder visuals, validated desktop/laptop/handheld/
  summary-only examples, a required-fields table, and a common-mistakes table.
  `data/community/README.md` now points to it.

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
