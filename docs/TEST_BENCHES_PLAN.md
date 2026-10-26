# Plan: Official test benches by system generation

Status: planned 2026-10-24, implemented in 1.9.0.0 (2026-10-25). The deferred
items are in [TODO.md](TODO.md) ("Test bench follow-ups"); the current design is
documented in [COPILOT_HANDOFF.md](COPILOT_HANDOFF.md#test-benches).

Implementation differences from this plan: the registry is a `testbenches:`
list (like `games.yaml`), not a mapping; rule docs are in
`docs/COMMUNITY_SUBMISSIONS.md`; records also carry a short `testbench_label`
(`DDR5 current`) for bar suffixes; and the `benchmarks/` pages keep their
per-form-factor sections and add a "Test bench" column.

Changed after review (2026-10-25): benches are labeled by memory type, "DDR5
Bench", "DDR4 Bench", "DDR3 Bench", instead of current/previous/legacy. The
`generation` field is gone; the label comes from `memory_type`, so a DDR6
system needs no code change. API field `testbench_generation` became
`testbench_memory`, community desktop runs got their own chip, and every bench
badge looks the same (no bench is styled as lesser). The summaries table says
"Desktop: DDR5" rather than "DDR5 Bench", and every platform chip starts on
(no bench is hidden by default).

## Context

Official runs today record CPU and RAM per run (`system.cpu`, `memory_gb`,
`memory_type`, `memory_channels`), but none of those are grouping keys
(`build.aggregate_game_records`, scripts/build.py ~L186). If the same GPU is
tested on two machines, the dashboard silently averages a 9800X3D run with a
5600X3D run, which hides exactly what we want to show.

The goal: the same GPU tested on a current-, previous-, and legacy-generation
system, shown as **separate bars**, so a reader with, say, an RTX 5060 Ti in a
DDR4 system can see what FPS to expect next to the DDR5 result.

Benches:

| ID (proposed) | Generation | CPU | RAM | Status |
|---|---|---|---|---|
| `am5_9800x3d_ddr5` | current (primary) | Ryzen 7 9800X3D | 64 GB DDR5-6000, 2 channels | active, the main bench from now on |
| `am4_5600x3d_ddr4` | previous | Ryzen 5 5600X3D | 32 GB DDR4-3200, 2 channels | active |
| `lga1150_4790_ddr3` | legacy | Core i7-4790 | 16 GB DDR3 (speed and channels TBD) | planned, not yet confirmed working |
| `am5_9950x3d_ddr5` | current (interim) | Ryzen 9 9950X3D | 64 GB DDR5-6000, 2 channels | the maintainer's main PC; holds the 2 existing RTX 5080 FE runs |

Decisions already made with the user:
- Generation names: **current** (DDR5), **previous** (DDR4), **legacy** (DDR3).
- Benches are an **official-run concept only**. Community runs keep free-form
  CPU/RAM, and `community-outlier` compares against the primary bench only.
- The 9950X3D runs are interim. When the 5080 FE is re-run on the 9800X3D:
  within margin of error, fold them into the primary bench's average;
  clearly different, delete them and keep only the 9800X3D runs.
- Bench 3 is DDR3 with the speed TBD. Register it as `status: planned` and
  fill the speed in once the system is confirmed to work.

## How the site changes (what a reader sees)

The **Form factor** chip row becomes **Platform**, and the desktop chip splits
by generation:

```
Platform:  [Desktop · current gen] [Desktop · previous gen] [Desktop · legacy]
           [Laptop] [Handheld] [iGPU]
```

- Each generation chip turns its bars on or off, like form factor does today.
  Unselect "previous gen" and the DDR4 bars disappear.
- **Default:** everything on except previous gen and legacy. The first view
  looks like today's chart (one bar per GPU on the primary bench), and the
  older systems are one click away. Today an empty chip set means "show
  all"; this changes to an explicit default set.
- Turn on two generations and the same GPU gets **two bars side by side**,
  labeled e.g. "RTX 5060 Ti · DDR5 current" and "RTX 5060 Ti · DDR4
  previous". They group together under the same GPU when sorted by GPU.
- **Benchmark summaries table:** the "Form" column (site/index.html ~L383)
  becomes **"Platform"**. Its badge (~L789) shows the same labels as the chips:
  "Desktop · current gen", "Desktop · previous gen", "Desktop · legacy",
  "Laptop", "Handheld", "iGPU". Each generation gets its own badge color
  class, alongside the existing `form-desktop`. The table already follows the
  chip filters (`filteredRecords`), so a GPU on two benches is two rows,
  sorted together by the Platform column. Community desktop rows show
  "Desktop · community". Expanding a row shows the bench name next to the CPU
  and RAM in the run details (~L924).
- The 9950X3D runs, if they're kept separate rather than folded in, sit under
  "current gen" as their own bar with a "· 9950X3D" suffix.
- **Community desktop runs** have no bench. They show whenever any desktop
  chip is on, and keep their community styling. (A later option, in the
  backlog: sort them into generations by their `memory_type` prefix.)
- Chips only appear for generations that have runs, so legacy stays hidden
  until the first i7-4790 run lands.
- The JS-free `benchmarks/` pages and `llms-full.txt` get a "Test bench"
  column, so AI crawlers see the split too.

## Design

### 1. Registry: `data/testbenches.yaml`
Same pattern as `data/games.yaml` / `checks.load_games()` (scripts/checks.py
~L1136). Block-style YAML. Each entry:

```yaml
am5_9800x3d_ddr5:
  name: Ryzen 7 9800X3D · DDR5-6000
  generation: current    # current | previous | legacy
  primary: true          # exactly one bench
  status: active         # active | planned | interim | retired
  platform: AM5
  cpu: AMD Ryzen 7 9800X3D
  memory_gb: 64
  memory_type: DDR5-6000
  memory_channels: 2
  counts_as: ''          # optional: another bench ID whose summaries this one joins
  notes: ...
```

- `counts_as` covers the 9950X3D decision: set
  `am5_9950x3d_ddr5.counts_as: am5_9800x3d_ddr5` to fold its runs into the
  primary average. The runs keep their exact CPU in `implementations`. Delete
  the files instead if the re-run shows a real difference.
- Optional fields (motherboard, storage, BIOS) are allowed, but they are never
  grouping keys.

### 2. Checks (scripts/checks.py, each rule documented once)
Add `checks.load_testbenches()` and these rules. Each needs a ``#### `rule` ``
heading in `docs/COMMUNITY_SUBMISSIONS.md` or `data/gpus/README.md`
(`test_build.py` enforces the heading):
- `testbench-*`: registry shape. Required fields, exactly one `primary`,
  `generation`/`status` enums, `memory_type` format (reuse the
  `result-system-memory` parser), and `counts_as` must point at an existing
  non-alias bench of the same generation.
- `result-testbench-id`: **required on official desktop game runs**.
  Laptop, handheld, and iGPU runs are their own platforms, so they leave it out.
- `result-unknown-testbench`: the ID isn't in the registry.
- `result-testbench-community`: an error if a community file sets it.
- `result-testbench-mismatch`: a **warning** when the file's `system.cpu` or
  `memory_*` disagree with the registry, which catches a run tagged with the
  wrong bench. Planned benches skip the memory-speed comparison until it's
  filled in.
- `check_outliers` (~L1041): the baseline is official runs on the primary
  bench only (after resolving `counts_as`).

### 3. Build / API (scripts/build.py)
- `build_record`: add `testbench_id` (resolved through `counts_as`),
  `testbench_name`, and `testbench_generation`. Keep the raw ID as
  `testbench_source_id` so the interim runs stay traceable. All are empty for
  community runs.
- Add the resolved `testbench_id` to the grouping key in
  `aggregate_game_records`, and `testbench_source_id` to the
  `implementations` keys.
- Add a new `api/v1/testbenches.json` and reference it from the index/metadata.
- Add a "Test bench" column to `SUMMARY_COLUMNS` (`benchmarks/`, `llms-full.txt`).
- Bump `SCHEMA_VERSION` (0.18 → 0.19).

### 4. Importer (scripts/import_cyberpunk.py ~L509)
- Add `--testbench <id>`, required with `--source official` for desktop GPUs.
  It writes `testbench_id` and fills `system.cpu`/`memory_*` from the
  registry, so official runs no longer hit the DDR5-6000 default warning.
- A different bench for the same GPU and day goes in a `_2` file, because the
  bench applies to the whole file, like the CPU does today.
- `parse.py` and the official templates in `templates/` get the field.

### 5. Dashboard (site/index.html)
- Rename the "Form factor" label to "Platform" (~L148). Replace the
  `factors` array (~L325) with platform keys: `desktop:current`,
  `desktop:previous`, `desktop:legacy`, `Laptop`, `Handheld`, `Igpu`.
- Add `platformKey(record)`: for desktop official runs, `desktop:` plus
  `testbench_generation`; community desktop runs match any desktop chip.
- Update `renderFactorFilters` (~L648) and the filter in `filteredRecords`
  (~L371) to use it. Set the default state as above, and render only the
  chips that have records.
- Bar labels: add a bench suffix when the GPU appears on more than one bench
  in the current view.
- Summaries table: rename the column `{ key: "form", label: "Form" }` (~L383)
  to "Platform" (the key can stay `form`, or become `platform` throughout).
  `formatForm` (~L533) prints the platform label, and the badge class (~L789)
  adds `form-desktop-current|previous|legacy` CSS.
- The `form` sort key (~L426) sorts by platform order (current, previous,
  legacy, laptop, handheld, iGPU), then by GPU, so a GPU's generations sit
  together.
- The JS-free `benchmarks/` tables get the same "Platform" wording, so the
  column names match the dashboard.

### 6. Data migration
- Add `testbench_id: am5_9950x3d_ddr5` to both
  `data/official/rtx_5080_16gb_fe/result_2026101{3,5}_cyberpunk_2077.yaml`.
- Fixtures: give the official fixture runs a bench, add one fixture GPU on
  two benches to prove they don't average, and add one `counts_as` alias case.
  Update the fixture counts in `test_build.py` and `docs/COPILOT_HANDOFF.md`.

### 7. Docs & housekeeping (per CLAUDE.md)
- Add a CHANGELOG line. Version bump **MINOR** (1.8.0.0 → 1.9.0.0). Note for
  the user: requiring a new field on official files is arguably a
  data-contract break, which would make it MAJOR. Only maintainers write
  official files, so MINOR is the recommendation.
- Update `README.md`, `docs/COPILOT_HANDOFF.md`,
  `.github/copilot-instructions.md`, `CLAUDE.md`, and `AGENTS.md` with a new
  "non-obvious rule": the bench is a grouping key for official desktop runs
  only, and the dashboard's Platform chips split desktop by generation.
- Add the rule headings to `data/gpus/README.md` and
  `docs/COMMUNITY_SUBMISSIONS.md`, and document `--testbench` in
  `docs/CYBERPUNK_BENCHMARK.md`.
- Add the deferred items below to `docs/TODO.md`.

### Deferred (goes into docs/TODO.md)
- Re-run the RTX 5080 FE on the 9800X3D, then choose fold-in (`counts_as`)
  or delete.
- Confirm the i7-4790 bench works, fill in the DDR3 speed and channels, and
  flip it to `active`.
- Sort community desktop runs into generations by their `memory_type` prefix.
- A dedicated "platform scaling" view: one GPU, one bar per bench, each as a
  % of the primary.
- A blog post explaining the benches (POST bump, author-written).

## Branch
`git checkout main && git pull && git checkout -b feat/test-benches`
(don't stack it on the current `chore/github-sponsors` branch).

## Verification
In `.venv`:
- `python scripts/validate.py` and `python scripts/build.py` pass, and the two
  5080 runs carry `testbench_id: am5_9950x3d_ddr5`.
- `python scripts/test_build.py` gets new assertions: the two-bench fixture
  GPU yields two summaries, the alias case yields one, a community file with
  `testbench_id` fails, an official desktop run without one fails, and every
  new rule has a doc heading.
- Run `py_compile` on all scripts, `npm --prefix blog run build`, and
  `git diff --check`.
- `python scripts/build.py --data-dir tests/fixtures/data`, then
  `python -m http.server 8000 --directory site`. Check that the Platform row
  shows the generation chips, that the default view matches today's chart,
  and that turning on "previous gen" adds labeled side-by-side bars. Stop the
  server afterwards.
