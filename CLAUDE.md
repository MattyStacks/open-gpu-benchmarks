# CLAUDE.md

Guidance for Claude Code working in this repository.

## Every change: update the changelog and the backlog

These two steps are required, not optional, for every PR an agent or a person
prepares:

1. **[CHANGELOG.md](CHANGELOG.md)** — add a line under `Unreleased` for any change to
   behavior, the data contract, the API schema, the dashboard, the checks, the
   templates, or the contributor workflow. Data-only result submissions are the
   only exception. Don't finish a task with an empty `Unreleased` section if
   you changed any of those.
2. **[docs/TODO.md](docs/TODO.md)** (the backlog) — remove items you completed, and
   add anything you deferred, found broken, or were asked to do later.

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
   community result files. [data/gpus/README.md](data/gpus/README.md) — catalog
   layout, ID grammar, field reference, and an explanation of every check rule.
6. [CHANGELOG.md](CHANGELOG.md) — high-level version history. Add an entry under
   `Unreleased` for every user-visible, schema, or workflow change.
7. [docs/TODO.md](docs/TODO.md) — the backlog of deferred work. Do not pull
   items from it into a session unless asked; add new deferred ideas there
   instead, and remove items when they're done.
8. [AGENTS.md](AGENTS.md) — the tool-neutral entry point for other AI agents.
   Keep it in step with this file.

The first five documents overlap on purpose. When a rule changes, it has to change
in every file that states it, or the next session gets contradictory context.

## What this project is

A static GitHub Pages dashboard that compares desktop, laptop, handheld, and
integrated GPUs from reviewable YAML. No backend, no database, no build
toolchain beyond Python.

- Repo: `MattyStacks/open-gpu-benchmarks`, default branch `main`
- Site: <https://mattystacks.github.io/open-gpu-benchmarks/>
- Current development version: `v0.6.0` (`RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py), with `SCHEMA_VERSION` alongside it)

### Layout

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml
                                   authoritative catalog, one file per product
data/gpus/reference/<gpu_vendor>/<ref_id>.yaml
                                   shared chip specs products inherit via base:
data/gpus/README.md                catalog rules, ID grammar, every check explained
data/reviews.yaml                  optional published-review links
data/official/<gpu_id>/result_*.yaml
data/community/<gpu_id>/result_*.yaml
data/community/<gpu_id>/raw/**     optional raw capture evidence
scripts/checks.py                  every catalog and result rule, written once
scripts/build.py                   YAML source -> site/api/v1/** JSON (runs checks first)
scripts/validate.py                PR validator: validate.py [catalog|results]
scripts/parse.py                   PresentMon/MangoHud CSV -> result YAML
scripts/test_build.py              build smoke test (runs in both CI workflows)
site/index.html                    the whole dashboard, single file
site/favicons/                     site icons (favicon.svg is primary, theme-aware)
templates/                         starting points for runs and catalog entries
requirements.txt                   Python dependencies (pyyaml, numpy); CI and .venv use it
.venv/                             local virtual environment (gitignored, never committed)
CHANGELOG.md                       high-level version history (update with every change)
docs/TODO.md                       backlog: deferred work (update with every change)
AGENTS.md                          tool-neutral agent entry point (keep in step with this file)
.github/workflows/build.yml        builds site/api and deploys Pages on main
.github/workflows/validate.yml     three PR checks: Catalog entries, Benchmark results,
                                   Build and tests
```

Generated `site/api/` output is gitignored and recreated in CI. Do not commit it
unless repository policy changes.

### Non-obvious rules that bite

- Source files use `graphics_preset`. Never add a `settings` fallback.
- `result:` is always a YAML list; every resolution/preset profile needs its
  leading `-`. A duplicated `result:` key silently drops data.
- Desktop and laptop GPU records never share a summary group.
- Game runs require `system.os`: `windows` or `linux`, lowercase. The OS is a
  grouping key, so Windows and Linux runs are never averaged together; the
  distro, kernel, Mesa, and Proton are per-run detail fields, never grouping
  keys or extra chart bars. Linux-only fields on a windows run (or the
  reverse) are errors. Per-distro comparisons are DIY from the JSON.
- `frame_generation: false` is required for comparable game runs.
- `avg_fps` is required; `p1_low` is optional (3DMark and in-game benchmarks
  report none) and is `null` in the API when missing. `proof.method` is
  required on every game run and says which tool captured it
  (`checks.PROOF_METHODS`: PresentMon, CapFrameX, FrameView, MSI Afterburner,
  AMD Adrenalin, MangoHud, OCAT, in-game benchmark, synthetic benchmark, or
  other); PresentMon is the recommended default and the method is never a
  grouping key. Frame-time tools (`checks.P1_LOW_METHODS`) must include
  `p1_low` (`result-p1-low-required`); the rest only warn. A 3DMark run is a normal game run with the
  graphics-test FPS as `avg_fps` and its result URL as `proof.summary_source`.
- A community average more than 25% from the matching official average fails
  `community-outlier` (`OUTLIER_RATIO` in `scripts/checks.py`).
- Catalog specs are nested (`identity`, `classification`, `silicon`,
  `memory`, `clocks`, `power`, `release`, `features`). Only five fields are
  required (`id`, `identity.name`, `identity.gpu_vendor`,
  `classification.form_factor`, `memory.capacity_gb`); quote every date and
  version number so YAML keeps it a string.
- A result folder's name must exactly equal the `gpu_id` inside its files, and
  that ID must be a catalog file name under `data/gpus/`.
- Catalog IDs are product-level with one `<N>gb` token equal to
  `memory.capacity_gb`. Different memory sizes and board partners are
  different IDs. Handheld RAM is in the ID; laptop system RAM is recorded per
  run. The catalog folder is `<form_factor>/<gpu_vendor>`, where
  `gpu_vendor` is the GPU chip maker. The field is `identity.gpu_vendor`, not
  `vendor`.
- `data/gpus/reference/` holds shared chip specs, not products. Products use
  `base: <ref_id>` and the build deep-merges them over the reference.
  Results never point at a reference ID. `platform` is for handhelds and
  laptops only, and `board_partner` is for desktop cards only.
- Catalog files list `sources` (https URLs, `covers` = sections that page
  actually backs). Never invent a source or a spec value; leave unknowns out.
  Quote source titles that contain `: `.
- Block-style YAML only in data and templates: no inline `[ ]` or `{ }`.
- Every rule lives once in `scripts/checks.py`. A new rule needs a
  ``#### `rule-name` `` heading in `data/gpus/README.md` or
  `docs/COMMUNITY_SUBMISSIONS.md`, and `test_build.py` enforces that.
- Exact machine metadata stays on each run; charts show grouped summaries.
- Raw capture evidence is preferred; preserve its reference when correcting or
  removing a record.
- Community files need `submitted_by: <github_user>` and the name
  `result_YYYYMMDD_<game>_<github_user>.yaml` (case-insensitive match; same-day
  repeats use `_<game>_2_<github_user>`). Official files don't need it.
- Results measured by someone else keep the PR author in `submitted_by` and add
  a `credit` block (`name`, optional https `url`/`source_url`, and
  `permission` with at least one of `url`, `screenshot`, `note`). The
  dashboard shows "Name (via @user)". Example credits use made-up names and
  `example.com` URLs, never a real creator or channel.
- The dashboard may move to a custom domain: keep GitHub links absolute and
  API/data links relative to the page.

## Checks to run before finishing

Run the checks inside the project's virtual environment, never the global
Python. Create it once with `python -m venv .venv`; after that, only activate it.

```powershell
.venv\Scripts\Activate.ps1               # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
git diff --check
```

Preview the site with `python -m http.server 8000 --directory site` and open
<http://localhost:8000>. Stop the server when you're done with it, and run
`deactivate` at the end of the session (see "Wrapping up a session").

Create a Git tag only when explicitly asked, after the commit is reviewed.

## Wrapping up a session

Context for the next session lives in the instruction files, not in this
conversation. Before you report a task complete, clean up and update whatever
is now stale:

- **Clean up your environment** → stop every server or background process you
  started (for example the `python -m http.server 8000 --directory site`
  preview), then run `deactivate` to leave the `.venv` virtual environment.

- **Data contract, schema, or build-output change** → update
  [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md),
  [README.md](README.md), and
  [.github/copilot-instructions.md](.github/copilot-instructions.md) if a rule
  changed. Bump `SCHEMA_VERSION` when the generated API payload changes.
- **Any behavior, schema, dashboard, or workflow change** → add a line under
  `Unreleased` in [CHANGELOG.md](CHANGELOG.md). Always; see the top of this
  file.
- **Work finished, deferred, or discovered** → update the backlog in
  [docs/TODO.md](docs/TODO.md).
- **Agent instructions changed** → keep `CLAUDE.md`,
  `.github/copilot-instructions.md`, and `AGENTS.md` consistent.
- **Version change** → rename `Unreleased` in `CHANGELOG.md` to the new version
  and date, and update `RELEASE_VERSION` in
  [scripts/build.py](scripts/build.py) plus the version references and feature
  summary in `README.md` and `docs/COPILOT_HANDOFF.md`.
- **Fixtures added/removed** → refresh the fixture counts (catalog GPUs,
  official runs, community runs, dashboard summaries) in `README.md` and
  `docs/COPILOT_HANDOFF.md`. These counts are quoted in both files and go wrong
  easily.
- **Submission or validation rules changed** → update `CONTRIBUTING.md`,
  `docs/COMMUNITY_SUBMISSIONS.md`, `data/community/README.md`,
  `data/gpus/README.md`, and the data rules in
  `.github/copilot-instructions.md`.
- **New command, script, or workflow step** → add it to the check lists in
  `README.md`, `CONTRIBUTING.md`, `docs/COPILOT_HANDOFF.md`, and
  `.github/copilot-instructions.md`.
- **Anything a future session would have to rediscover by reading code** → put
  it in `docs/COPILOT_HANDOFF.md`, and add the rule here or in
  `.github/copilot-instructions.md` if it constrains future work.

Keep this file current too: if the layout, the checks, or the list of
instruction files changes, edit `CLAUDE.md` in the same commit.
