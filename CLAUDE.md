# CLAUDE.md

Guidance for Claude Code working in this repository.

## Read these first

Before changing the data schema, build logic, validation, the dashboard, or the
docs, read:

1. [.github/copilot-instructions.md](.github/copilot-instructions.md) — the
   short agent rulebook (data rules, version/release housekeeping). Treat it as
   binding for Claude too, not just Copilot.
2. [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md) — architecture, the data
   contract, current fixture counts, deployment, and the maintenance checklist.
   This is the project's living state document.
3. [README.md](README.md) — public description of the data flow and local dev.
4. [CONTRIBUTING.md](CONTRIBUTING.md) and
   [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) — contributor
   setup and the full submission/review rules.
5. [data/community/README.md](data/community/README.md) — folder-level rules for
   community result files.
6. [CHANGELOG.md](CHANGELOG.md) — high-level version history. Add an entry under
   `Unreleased` for every user-visible, schema, or workflow change.
7. [docs/TODO.md](docs/TODO.md) — deferred work. Do not pull items from it into
   a session unless asked; add new deferred ideas there instead.

The first five documents overlap on purpose. When a rule changes, it has to change
in every file that states it, or the next session gets contradictory context.

## What this project is

A static GitHub Pages dashboard that compares desktop, laptop, handheld, and
integrated GPUs from reviewable YAML. No backend, no database, no build
toolchain beyond Python.

- Repo: `MattyStacks/open-gpu-benchmarks`, default branch `main`
- Site: <https://mattystacks.github.io/open-gpu-benchmarks/>
- Current development version: `v0.4.0` (`RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py), with `SCHEMA_VERSION` alongside it)

### Layout

```text
data/gpus.yaml                     authoritative GPU catalog (IDs come from here)
data/reviews.yaml                  optional published-review links
data/official/<gpu_id>/result_*.yaml
data/community/<gpu_id>/result_*.yaml
data/community/<gpu_id>/raw/**     optional raw capture evidence
scripts/build.py                   YAML source -> site/api/v1/** JSON
scripts/validate.py                PR validator for source YAML
scripts/parse.py                   PresentMon/MangoHud CSV -> result YAML
scripts/test_build.py              build smoke test (runs in both CI workflows)
site/index.html                    the whole dashboard, single file
site/favicons/                     site icons (favicon.svg is primary, theme-aware)
templates/                         starting points for official/community runs
CHANGELOG.md                       high-level version history (update with every change)
docs/TODO.md                       deferred work, out of scope until asked
.github/workflows/build.yml        builds site/api and deploys Pages on main
.github/workflows/validate.yml     runs validate.py + test_build.py on PRs
```

Generated `site/api/` output is gitignored and recreated in CI. Do not commit it
unless repository policy changes.

### Non-obvious rules that bite

- Source files use `graphics_preset`. Never add a `settings` fallback.
- `result:` is always a YAML list; every resolution/preset profile needs its
  leading `-`. A duplicated `result:` key silently drops data.
- Desktop and laptop GPU records never share a summary group.
- `frame_generation: false` is required for comparable game runs.
- Catalog specs in `data/gpus.yaml` are nested (`identity`,
  `classification`, `silicon`, `memory`, `clocks`, `power`, `release`,
  `features`); quote every date so YAML keeps it a string.
- A result folder's name must exactly equal the `gpu_id` inside its files, and
  that ID must exist in `data/gpus.yaml`.
- Exact machine metadata stays on each run; charts show grouped summaries.
- Raw capture evidence is preferred; preserve its reference when correcting or
  removing a record.
- Community files need `submitted_by: <github_user>` and the name
  `result_YYYYMMDD_<game>_<github_user>.yaml` (case-insensitive match; same-day
  repeats use `_<game>_2_<github_user>`). Official files don't need it.
- The dashboard may move to a custom domain: keep GitHub links absolute and
  API/data links relative to the page.

## Checks to run before finishing

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python scripts/test_build.py
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

Preview the site with `python -m http.server 8000 --directory site` and open
<http://localhost:8000>.

Create a Git tag only when explicitly asked, after the commit is reviewed.

## Wrapping up a session

Context for the next session lives in the instruction files, not in this
conversation. Before you report a task complete, update whatever is now stale:

- **Data contract, schema, or build-output change** → update
  [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md),
  [README.md](README.md), and
  [.github/copilot-instructions.md](.github/copilot-instructions.md) if a rule
  changed. Bump `SCHEMA_VERSION` when the generated API payload changes.
- **Any behavior, schema, dashboard, or workflow change** → add a line under
  `Unreleased` in [CHANGELOG.md](CHANGELOG.md).
- **Version change** → rename `Unreleased` in `CHANGELOG.md` to the new version
  and date, and update `RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py) plus the version references and feature
  summary in `README.md` and `docs/COPILOT_HANDOFF.md`.
- **Fixtures added/removed** → refresh the fixture counts (catalog GPUs,
  official runs, community runs, dashboard summaries) in `README.md` and
  `docs/COPILOT_HANDOFF.md`. These counts are quoted in both files and go wrong
  easily.
- **Submission or validation rules changed** → update `CONTRIBUTING.md`,
  `docs/COMMUNITY_SUBMISSIONS.md`, `data/community/README.md`, and the data
  rules in `.github/copilot-instructions.md`.
- **New command, script, or workflow step** → add it to the check lists in
  `README.md`, `CONTRIBUTING.md`, `docs/COPILOT_HANDOFF.md`, and
  `.github/copilot-instructions.md`.
- **Anything a future session would have to rediscover by reading code** → put
  it in `docs/COPILOT_HANDOFF.md`, and add the rule here or in
  `.github/copilot-instructions.md` if it constrains future work.

Keep this file current too: if the layout, the checks, or the list of
instruction files changes, edit `CLAUDE.md` in the same commit.
