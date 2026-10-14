# Open GPU Benchmarks - Project Handoff

## Project identity

- Repository: `MattyStacks/open-gpu-benchmarks`
- Default branch: `main`
- Public site: <https://opengpubenchmarks.com> (Cloudflare Pages, canonical)
- Mirror: <https://mattystacks.github.io/open-gpu-benchmarks/> (GitHub Pages)
- Public dashboard API: <https://opengpubenchmarks.com/api/v1/dashboard.json>
- GPU master API: <https://opengpubenchmarks.com/api/v1/gpus.json>
- Crawlable summaries: <https://opengpubenchmarks.com/benchmarks/>,
  <https://opengpubenchmarks.com/llms.txt>, <https://opengpubenchmarks.com/llms-full.txt>
- Current version: `v1.0.0` (2026-10-14)
  - v1.0.0: the published catalog was reset to one product, the GeForce RTX
    5080 Founders Edition (`rtx_5080_16gb_fe`, base `rtx_5080_16gb`), with
    its first 33 official Cyberpunk 2077 runs, imported by the new
    `scripts/import_cyberpunk.py`. API schema unchanged (0.12).
  - v0.6.0: Linux vs Windows (`system.os` required and a grouping key, OS
    detail fields, `result-os`/`result-os-field`/`result-system-field`
    checks, OS chips and striped Linux bars), catalog `sources`, one overlaid
    avg/1% low bar per GPU, and `parse.py` MangoHud/PresentMon fixes. API
    schema 0.8 → 0.9 → 0.10.
  - v0.5.0: the per-product catalog under `data/gpus/` (one file per product,
    product-level IDs with a memory token, `identity.gpu_vendor`, five
    required fields), reference files with `base` merging, `platform`,
    `identity.board_partner`, `skus`, shared checks in `scripts/checks.py`,
    three separate CI checks, and the per-card dashboard spec table. API
    schema 0.6 → 0.7 → 0.8.
  - v0.4.0: community files require `submitted_by` and a `_<github_user>` file
    name suffix, API schema 0.5 (`submitted_by`, `contributors`), dashboard
    JSON API panel and GitHub links.
  - **Every PR updates [CHANGELOG.md](../CHANGELOG.md)** under `Unreleased`
    when it changes behavior, the data contract, the schema, the dashboard,
    the checks, or the workflow. This applies to humans and to every AI agent.
  - Open follow-ups live in [docs/TODO.md](TODO.md).

## Current data contract

The static dashboard is built from a GPU-rooted source tree. The catalog under
`data/gpus/` is authoritative, one file per product. Every official and
community result must be in the folder named by its exact catalog ID and must
carry the same `gpu_id`.

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml
data/official/<gpu_id>/result_YYYYMMDD_<benchmark>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml
data/community/<gpu_id>/raw/**                         optional raw evidence
                 |
                 v
python scripts/build.py
                 |
                 v
site/api/v1/gpus.json
site/api/v1/official/<gpu_id>/summary.json
site/api/v1/community/<gpu_id>/summary.json
site/api/v1/dashboard.json
```

There are no source `summary.yaml` files. Each source file describes one
benchmark capture and has a non-empty `result` YAML list. Each dashed list
entry is a separate resolution/preset profile. The dash is required YAML list
syntax: duplicate `result:` keys overwrite each other. The build validates and
expands every entry before deriving source-specific per-GPU and dashboard
summaries. The per-GPU summaries retain all records and metrics, allowing
future benchmark types such as 3DMark to coexist with game FPS results.

`gpus.json` is the master API. Each catalog entry includes official/community
run and game-summary data plus links to the generated per-GPU summary JSON.
`dashboard.json` remains a game-FPS-only, chart-ready projection.

Schema `0.5` adds `submitted_by` (string, empty for official runs) to every run
record and the per-run `implementations` entries, and a sorted, de-duplicated
`contributors` list to every grouped summary.

Schema `0.12` makes community submissions anonymous by default: `submitted_by`
is optional and empty when left out, `proof_level` is `raw-log`,
`summary-only`, `maintainer-verified` (an official run with no linked
evidence; official runs are verified by the maintainer by definition, and the
dashboard says "Verified"), or `none` (a community run with no raw log,
summary source, or `credit.source_url`; the dashboard says "Unverified"), and
`checks.proof_reference()` picks the evidence. Official files may carry a
`credit` block (the maintainer entering a run on someone's behalf) that needs
only `name`. `upscaling` is normalized by `checks.upscaling()` to `""` when off and
is a grouping key. Summary `credits` entries are `{name, url, source_url}`, and
`implementations` entries carry `credit_source_url` and `upscaling`.

Schema `0.6` nests the catalog hardware specs. Each catalog entry keeps its
`id` at the top level with `identity`, `classification`, `silicon`,
`memory`, `clocks`, `power`, `release`, and `features` sections. Run records
keep flat `vram_gb`/`tdp_w` derived from the nested specs, with `vram_gb` null
for shared-memory handhelds instead of 0.

Schema `0.7` splits the catalog into one file per product and makes IDs
product-level:

- **Path.** `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. The file name
  equals `id`, and the folders equal `classification.form_factor` and
  `identity.gpu_vendor`. `gpu_vendor` is the GPU chip maker, never the board
  partner or device OEM.
- **Memory token.** Every ID has exactly one `<N>gb` token equal to
  `memory.capacity_gb`. Different memory sizes and board partners are
  different IDs, which is what keeps them in separate summary groups. No new
  grouping key was needed.
- **ID patterns.**
  - desktop: `<gpu_model>_<vram>gb_<brand>_<product_line>`, with
    `_fe`/`_reference`/`_le` for the vendor's own card
  - laptop: `<gpu_model>_<vram>gb_<oem>_<model>`, or a temporary `_generic`
    that warns
  - handheld: `<device>_<chip>_<ram>gb`

  Handheld RAM is soldered, so it is part of the ID. Laptop system RAM is
  upgradeable, so it stays on each run in `system.memory`.
- **Vendor field.** `identity.vendor` is renamed to `identity.gpu_vendor`.
  Run records carry `gpu_vendor` instead of `vendor`, and the dashboard
  reads `record.gpu_vendor`.
- **Required fields.** Only five are required: `id`, `identity.name`,
  `identity.gpu_vendor`, `classification.form_factor`, and
  `memory.capacity_gb`.
- **Optional fields.** These are still type-checked and range-checked: quoted
  dates, capacity 1-512 GB, bus width 32-512 bits, TDP 5-600 W. Unknown
  fields are rejected. Missing values become `null` in the API and `—` on
  the dashboard.
- **Ordering.** `gpus.json` lists entries by form factor, then vendor, then ID.

Schema `0.8` adds reference files.

- **Reference files.** `data/gpus/reference/<gpu_vendor>/<ref_id>.yaml`
  holds a GPU's shared specs. A product sets `base: <ref_id>`, and
  `resolve_base()` in `checks.py` deep-merges the product over the
  reference: product values win, sections merge field by field, and lists
  are replaced whole.
- **Checks run in two stages.** Required fields, ranges, the ID memory token,
  and the folder are checked on the merged entry. Field names and types are
  checked on each file as written, so errors point at the file that has
  them.
- **Reference contents.**
  - Required: `id`, `identity.name`, `identity.gpu_vendor`.
  - Not allowed: `base`, `skus`, `platform`, `identity.board_partner`,
    `classification.form_factor` (rule `reference-field`).
  - ID: `<gpu_model>_<vram>gb`, or a bare chip name for APUs
    (`z1_extreme`).
- **References are never products.** `load_catalog()` returns only merged
  products, so references never appear in `gpus.json`. A result that
  points at one fails as `result-reference-id`. `gpus.json` entries carry
  `base`.
- **Product-only fields.**
  - `identity.board_partner`: desktop only.
  - `skus`: a string list.
  - `platform`: handheld and laptop only, rule `field-not-allowed`. Its
    fields are `oem`, `cpu`, `ram_mts`, `os_shipped`, `display`,
    `power_min_w`, `power_max_w`, and `battery_wh`, each range-checked, and
    the minimum power can't exceed the maximum.
- **Current references.** `data/` has one: `rtx_5080_16gb`, the base of
  `rtx_5080_16gb_fe`. Its specs come from NVIDIA's RTX 5080 page and
  Wikipedia's RTX 50 series table; TechPowerUp blocks automated fetches with a
  bot check. The fixture catalog snapshot keeps the nine pre-1.0 references
  (`rtx_4090_24gb`, `z1_extreme`, ...), and `steam_deck_oled_16gb` there
  deliberately has no `base`.
- **Dashboard.** The expanded row shows a "Device" grid from `platform` and
  chips for the board partner and base.

Schema `0.9` (v0.6.0) adds `sources`:

- **The field.** Every catalog file can carry a block list of
  `{url, title, accessed, covers}` items. `url` must be `https://`.
  `accessed` is a quoted `YYYY-MM-DD`. `covers` lists section names from
  `CATALOG_FIELDS`. `release.msrp_history` items may carry their own
  `source` link.
- **Checks.** A malformed item fails as `source-invalid`. A file with no
  `sources` warns as `sources-missing`; that becomes an error later.
- **Merging.** `merge_sources()` in `checks.py` lists the product's sources
  first, then the reference's. A URL cited by both appears once, with the
  two `covers` lists combined.
- **Dashboard.** The expanded row lists the sources as links (https only,
  via `safeHttpsUrl()`). A price row links its own `source`.
- **Current data.** Every catalog file has sources (accessed 2026-10-08):
  - TechPowerUp GPU database pages for the discrete GPUs
  - Intel's A770M spec page
  - AMD's Z1 Extreme page
  - ASUS's ROG Ally spec page
  - Lenovo's Legion Go PSREF
  - Valve's Steam Deck OLED tech specs
- **How they were checked.** TechPowerUp serves scripts a bot check, so its
  URLs were confirmed by page title and its values through search results.
  The maintainer plans to re-validate sources by hand.
  - `covers` only lists sections a page was confirmed to back.
  - The silicon specs of `z1_extreme` (die size, transistors, shader
    counts) have no source yet.

Schema `0.10` (v0.6.0) adds the OS:

- **The field.** Game runs (official and community) require `system.os`,
  `windows` or `linux`, lowercase. A top-level `os:` (written by the old
  `parse.py`) or free text such as `Windows 11` fails as `result-os`.
- **Grouping.** `aggregate_game_records()` adds `os` to the group key, and
  `comparison_policy.group_by` lists it. Windows and Linux runs of one profile
  are two summaries. The distro is not a grouping key.
- **Detail fields.** `checks.OS_FIELDS` maps each optional field to the OS it
  applies to (`both`, `windows`, `linux`) and its kind (`text`, `bool`):
  - both: `os_detail`, `os_build`, `resizable_bar`, `graphics_api`
  - windows: `game_mode`, `hags`, `memory_integrity`, `power_plan`
  - linux: `distro`, `distro_version`, `kernel`, `mesa`, `runtime`
    (`native`/`proton`/`wine`), `proton`, `dxvk`, `vkd3d_proton`,
    `launcher`, `session`, `gamemode`

  A wrong type, a bad `runtime`, or a field on the wrong OS fails as
  `result-os-field`. An unknown `system` key (not in `checks.SYSTEM_FIELDS`)
  warns as `result-system-field`. `build_record()` copies every detail field
  (text as `""` when missing, bools as `null`), and they are in each
  summary's `implementations`.
- **Outliers.** `official_baseline()` only uses official runs on the same OS,
  so a Linux community run with only Windows official data gets
  `result-no-baseline`.
- **Dashboard.** Windows/Linux chips (`state.oses`, both on by default; none selected shows every run, like the
  form-factor chips), an OS
  column and badge, OS details in `formatRunLine()`, and a per-distro note in
  `#data-api`. When both OSes are visible, `displayName()` adds `· Linux`
  to Linux bars and `· Windows`/`· Linux` to products shown under both, and
  Linux bars get an ECharts `decal` stripe plus a legend entry.
- **Per-distro charts are DIY** from `community.json`, `official.json`, or a
  per-product `summary.json`.

Old-to-new ID map from v0.5.0, applied to the result folders as well. Since
v1.0.0 these products live only in the test fixtures:

| Old ID | New ID |
| ------ | ------ |
| `rtx_4090` | `rtx_4090_24gb_fe` |
| `rtx_4080_super` | `rtx_4080_super_16gb_fe` |
| `rtx_4070_super` | `rtx_4070_super_12gb_fe` |
| `rx_7900_xtx` | `rx_7900_xtx_24gb_reference` |
| `arc_a770` | `arc_a770_16gb_le` |
| `rtx_4090_laptop` | `rtx_4090_laptop_16gb_generic` |
| `rtx_4070_laptop` | `rtx_4070_laptop_8gb_generic` |
| `arc_a770m` | `arc_a770m_16gb_generic` |
| `rog_ally_z1_extreme` | `rog_ally_z1_extreme_16gb` |
| `legion_go` | `legion_go_z1_extreme_16gb` |
| `steam_deck_oled` | `steam_deck_oled_16gb` |

## Data rules

- The source schema uses `graphics_preset`; do not add a `settings` fallback.
- Desktop and laptop GPU records never share a summary group.
- Frame generation must be disabled for comparable game runs.
- Keep exact machine metadata with each run while charts display grouped
  summaries.
- Game runs require `system.os` (`windows` or `linux`). The OS is a grouping
  key; distro, kernel, Mesa, and Proton are per-run details. OS-specific
  fields must match the OS.
- Treat raw capture evidence as preferred and preserve its reference when
  correcting or removing a record.
- Community files are anonymous by default. `submitted_by` is optional; when
  set it must be a valid GitHub username (`community-submitter`). The file
  name is `result_YYYYMMDD_<game>.yaml`, with `_2`, `_3` for same-day repeats
  (`COMMUNITY_FILENAME`, `community-filename`). Older files that end in a
  username still match. Nothing compares the name to the PR author.
- Upscaling is off by default (missing, `off`, `none`, `native`, or `false`).
  A result entry (or the run) may set `upscaling` only with
  `preset_upscaling: true`, meaning the graphics preset turned it on;
  otherwise `result-upscaling` fails. Upscaling is a grouping key and part of
  the official-baseline match.
- Different memory sizes, board partners, or handheld RAM configurations are
  different catalog IDs. Never merge them into one entry.
- Data files and templates use block-style YAML only (no inline `[ ]` or
  `{ }`); `checks.py` rejects inline style as `yaml-inline`.

`benchmark_type` defaults to `game`. Game source files need `game` and a
`result` list whose entries each carry `resolution`, `graphics_preset`, and
`avg_fps`; `p1_low` is optional (schema `0.11`), so 3DMark and in-game
benchmark runs that report only an average are valid. A run record's `p1_low`
is `null` when missing; a summary averages `p1_low` over only the runs that have
one, and is `null` (with a `null` `p1_low_range`) when none do. `proof.method`
is required on every game run and must be one of `checks.PROOF_METHODS`
(`presentmon`, `capframex`, `frameview`, `msi_afterburner`, `amd_adrenalin`,
`mangohud`, `ocat`, `in_game_benchmark`, `synthetic_benchmark`, `other`; add a
tool by editing that tuple and the table in `docs/COMMUNITY_SUBMISSIONS.md`). It
is run detail, copied to `capture_method` on every record and
`implementations` entry, and never a grouping key. PresentMon is the
recommended method. The synthetic test fixtures use `other`. The tuple is
split: `P1_LOW_METHODS` (frame-time tools; a missing `p1_low` is the
`result-p1-low-required` error) and `AVERAGE_ONLY_METHODS` (a missing
`p1_low` is the `result-no-p1-low` warning, silent for
`synthetic_benchmark`). The community outlier limit is 25%
(`OUTLIER_RATIO`), pinned by a test.

Found results: anyone may submit a result someone else measured (a video, a
review, a post) with a `credit` block. It needs an https `source_url` (where
it was found, so a reviewer can check it) or, for unpublished numbers such as
a friend's run, a `permission` block with at least one of an https `url`, a
`screenshot` file inside the GPU folder, or a `note`. `name` and `url` are
optional. `credit_errors()` reports `community-credit` and, when `permission`
is given, `community-permission`. Run records carry `credit_name`,
`credit_url`, `credit_source_url`; summaries carry `credits`. Permission proof
is not copied into the API. The dashboard's "By" line, built by
`formatContributors()` and `creditName()`, shows "Name (via @user)", the
source's host name when there's no `name`, and "Anonymous" for a community run
with neither credit nor username. `templates/community_found_result.yaml` is
the starting point. Examples always use made-up names and `example.com`
URLs. A 3DMark run is
an ordinary game run (`game: 3DMark Steel Nomad`, its fixed resolution, a fixed
preset, `avg_fps` from the "Graphics test" FPS, optional `score`, and the result
URL as `proof.summary_source`); see `templates/community_steel_nomad.yaml`.
Each entry is independently validated and expanded.
The build averages matching entries from one or several files, while different
resolution/preset profiles remain distinct. Other types retain their `result`
entries in per-GPU API data but do not enter dashboard charts.

## Build and validation

Dependencies are listed once in [`requirements.txt`](../requirements.txt)
(`pyyaml`, plus `numpy` for `parse.py` percentiles). Local work runs inside a
`.venv` virtual environment (gitignored); CI installs the same file into the
runner's Python with `pip install -r requirements.txt` and a pip cache.

```powershell
python -m venv .venv                     # once
.venv\Scripts\Activate.ps1               # each terminal; macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate.py            # or: validate.py catalog / validate.py results
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\import_cyberpunk.py scripts\test_build.py
git diff --check
deactivate                               # when done
```

`python scripts/build.py --data-dir tests/fixtures/data` (or the same flag on
`validate.py`) runs against the synthetic test fixtures instead of `data/`.

Agents clean up before reporting a task complete: stop any server they
started (such as the `python -m http.server` preview), then `deactivate`.
The scripts need Python 3.11+ (`build.py` uses `datetime.UTC`); CI pins 3.11.

Every rule lives once in [`scripts/checks.py`](../scripts/checks.py).

- **Shared by both scripts.** `build.py` and `validate.py` both call
  `load_catalog()` and `load_results()`.
- **Issues, not exceptions.** Each check appends an
  `Issue(path, level, rule, message)` instead of raising, so one run reports
  every problem in every file.
- **Output format.** Under GitHub Actions, issues print as
  `::error file=<path>::[rule] message`, which puts annotations on the PR
  diff. Each message links to the rule's `####` heading in
  `data/gpus/README.md` (catalog rules) or `docs/COMMUNITY_SUBMISSIONS.md`
  (result rules).
- **Build stops on errors.** `build.py` exits 1 before writing any
  `site/api/` output if any error exists. It prints only errors plus a
  warning count; `validate.py` prints the warnings.
- **What `validate.py results` covers.** It checks official **and**
  community files. Community-only nudges (no proof, no driver, laptop TGP,
  no baseline) are warnings that apply only to community files. Any other
  YAML file in a result folder fails as `result-filename`, so it can't be
  skipped silently.

To add a rule, call `issues.error(path, "<rule-name>", ...)` or
`issues.warning(...)` in `checks.py`, then add a ``#### `<rule-name>` `` heading
to the matching doc. `check_rules_are_documented()` in `test_build.py` fails
until the heading exists. Also add a negative case to `check_catalog_rules()`
or `check_result_rules()`.

### CI

[`.github/workflows/validate.yml`](../.github/workflows/validate.yml) runs on
every pull request as three jobs, so the PR shows which part failed:

- **Catalog entries**: `validate.py catalog`
- **Benchmark results**: `validate.py results`
- **Build and tests**: `py_compile`, `build.py`, `test_build.py`

There is deliberately no `paths:` filter. A required check that is skipped
never reports, and that blocks the merge. Each job takes seconds.

[`build.yml`](../.github/workflows/build.yml) runs `validate.py` before
`build.py`, so `main` cannot deploy bad data.

**Repo setting (manual):** mark the three checks as required status checks in
the `main` branch protection rules (Settings → Branches).
[`scripts/parse.py`](../scripts/parse.py) writes converted CSV output directly
to `data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml`, with the game
name slugified. `--submitted-by` is optional and only written when given. It
rejects a `--gpu-id` that isn't in the catalog, takes the form factor from the
catalog entry, and adds `_2`, `_3`, ... rather than overwrite an existing
file. `--os` is `windows` or
`linux` and defaults from the capture format (MangoHud means linux,
PresentMon means windows); it is written to `system.os`, with `--os-detail`
to `system.os_detail`. MangoHud logs with the `os,cpu,gpu,...,kernel,driver`
header block fill `system.kernel` and `system.driver`.

[`scripts/import_cyberpunk.py`](../scripts/import_cyberpunk.py) turns
Cyberpunk 2077 built-in benchmark runs into result files; the user guide is
[CYBERPUNK_BENCHMARK.md](CYBERPUNK_BENCHMARK.md).

- **Input.** The game writes `benchmarkResults/benchmark_YYYY-MM-DD_HH-MM-SS/`
  with `summary.json` (read) and `frames.csv` (ignored). The script finds the
  folder through the Windows Documents known folder (handles OneDrive), or
  the Proton prefix of Steam app 1091500 on Linux; `--input` overrides.
  Nothing is copied into the repo.
- **Files and re-runs.** Runs go in `result_YYYYMMDD_cyberpunk_2077.yaml` by
  run date, one `result` item per run. Each item's `benchmark_run` holds its
  folder name (it ends up in the API under `metrics`). A run whose
  `benchmark_run` is in any `data/{official,community}/*/` result file is
  skipped. A new same-day run is appended to the day's file when every
  file-level field matches (`SETUP_KEYS`: `gpu_id`, `submitted_by`, `game`,
  `version`, `system`, `proof`); otherwise it goes in `_2`, `_3`, ...
  Appending rewrites the file, so hand-added comments in it are lost.
  `display_mode` (from `windowMode`) goes on each result item, because it
  can vary between runs and `system` is file-level; `build_record()` prefers
  the item's `display_mode` over `system.display_mode`. Skipped runs are not
  remembered.
- **Mapping.** `presetName` maps to the in-game name (`RayTracingUltra` is
  `Ray Tracing: Ultra`). Presets that enable an upscaler get `upscaling` and
  `preset_upscaling: true`. DLSS and FSR 2.1 quality indices use the menu
  order Auto, Quality, Balanced, Performance, Ultra Performance;
  `UserSettings.json` confirmed DLSS 0 = Auto and FSR 2.1 1 = Quality. Other
  upscalers' indices are written as `(mode N)`. Changing a label later splits
  dashboard groups. `avg_fps` is `averageFps`; there is no `p1_low`
  (`proof.method: in_game_benchmark`, `result-no-p1-low` warning per file).
  The driver string `Nvidia v 61714 [r617_07]` becomes `617.14`.
- **Skips.** Frame generation on (`frameGenerationType` or a frame-gen flag;
  `DLSSMultiFrameGenEnabled` alone is just the saved multiplier), V-Sync or an
  FPS cap, a GPU whose name lacks the ID's model tokens or whose memory
  doesn't match `memory.capacity_gb`, and Custom presets with upscaling on.
  Custom presets with upscaling off need a name (`--custom-preset`, or a
  prompt on a terminal).
- **Tests.** `check_import_cyberpunk()` in `test_build.py` imports synthetic
  summaries into a temp copy of the fixture catalog through `main(argv)`.
`scripts/test_build.py` covers:

- aggregation and `submitted_by`/`contributors` output
- anonymous submissions, file names, and `proof_level` (`check_anonymous_submissions()`)
- found results with a source or permission (`check_third_party_credit()`)
- upscaling rules and grouping (`check_upscaling()`)
- one negative case per check rule, run in temporary data directories
- that one run reports errors from several files at once
- that `build.main()` returns 1 and writes nothing on errors
- that a build deletes per-GPU summary folders for GPUs no longer in the
  catalog (`remove_stale_gpu_folders()`; other files in `site/api/` are
  overwritten, never deleted)
- that a required-fields-only catalog entry builds
- that every rule has a doc heading
- that the `templates/catalog_*.yaml` files pass the catalog checks
  alongside the fixture reference files (their example bases aren't published)
- `base` merge behavior (inherit, override, and list replacement)
- OS rules, Windows/Linux summary separation, and OS-aware outlier baselines
- MangoHud parsing (`check_parse_mangohud()`)
- the Cyberpunk 2077 importer (`check_import_cyberpunk()`): mapping, skips,
  and that a second import writes nothing
- that every `templates/community_*.yaml` passes the result checks as written,
  against the published `data/gpus` catalog (so they use `rtx_5080_16gb_fe`)
- the generated payload shape, from a temp build of `tests/fixtures/data/`
- that `data/` passes every check and has no `synthetic: true` runs

## Published data and test fixtures

**Published data (`data/`).** 1 catalog GPU entry (`rtx_5080_16gb_fe`), 33
official result runs, 0 community runs, and 29 dashboard summaries: Cyberpunk
2077 built-in benchmark runs on Windows at 1080p, 1440p, and 4K, imported with
`scripts/import_cyberpunk.py`. Every run has `p1_low: null`. `data/` is what
CI builds and deploys, so it holds only real data. With no runs,
`dashboard.json` has an empty `records` list and `showNoBenchmarks()` in
`site/index.html` replaces the filters, chart, and table with a "No benchmarks
published yet" message.

**Test fixtures (`tests/fixtures/data/`).** The synthetic runs moved here
from `data/` before the first real runs. The folder copies the `data/` layout,
including a snapshot of the catalog and `reviews.yaml`, so changes to the real
catalog (such as replacing the `_generic` laptop IDs) don't break the tests.
Leave the snapshot alone unless a test needs a new catalog entry.

- `build.py` and `validate.py` take `--data-dir`, for example
  `python scripts/build.py --data-dir tests/fixtures/data` for a local preview
  of the full dashboard. `build.main(data_dir, output_dir)` takes both folders.
- `test_build.py` builds the fixtures with `build.main(FIXTURES_DIR, <temp>)`,
  never into `site/api/`: `build.yml` runs the test after the real build and
  then deploys `site/`. `check_fixture_build()` asserts the payload numbers.
- `check_real_data()` asserts that `data/` passes every check and holds no
  `synthetic: true` run.

The fixtures have 11 catalog GPU entries, 19 official result runs, 12
community result runs, and 30 combined dashboard summaries. Six Linux runs pair
with a Windows run of the same profile: official RX 7900 XTX (Alan Wake 2,
Baldur's Gate 3, Helldivers 2; CachyOS) and RTX 4090 (Cyberpunk 2077), and
community ROG Ally (Cyberpunk 2077; Bazzite) and Arc A770 LE (Helldivers 2;
Fedora). The Steam Deck runs are Linux (SteamOS); every other run is Windows. The Arc A770 LE
fixtures exercise a multi-profile source file and matching-run aggregation.
The three laptop entries use `_generic` IDs and show `id-generic` warnings.
Every fixture is marked `synthetic: true`. All community fixtures use
`submitted_by: MattyStacks`, except the anonymous Steam Deck Cyberpunk 2077 run
(`result_20261003_cyberpunk.yaml`). Catalog specs are real published specs; only the
benchmark runs are synthetic.

## Dashboard

`site/index.html` is the whole dashboard. It reads `record.gpu_vendor` for the
vendor column, color, and search. It loads `./api/v1/dashboard.json`
relative to the page, so it works on GitHub Pages or a future custom domain.
It also loads `./api/v1/gpus.json` for the per-card spec columns. The chart
draws one bar per GPU: the average is a faded full-length bar and the 1% low a
solid bar over it (`barGap: "-100%"`). The legend swatches use a neutral
series color, and each bar uses its vendor color. The chart grows 30 px per
GPU from a 260 px minimum, and y-axis labels truncate at 42% of the chart
width. The
benchmark table sorts by any column, searches IDs, codenames, and
architectures, and expands each row into silicon details, price history,
and the exact runs behind the number.
The header has **JSON API** (jumps to `#data-api`) and **GitHub** buttons, and
the footer links to the repository, contributing guide, and issues. GitHub
links are absolute (`https://github.com/MattyStacks/open-gpu-benchmarks`); API
links stay relative. The **Get the data as JSON** panel (`#data-api`) lists
each endpoint with Open and Copy URL actions, plus curl/fetch snippets built
from `location` at runtime, and shows the schema version.

Icons live in `site/favicons/` (committed static files, linked relatively).
`favicon.svg` is the primary icon and carries its own
`prefers-color-scheme` light/dark styles. `syncFavicon()` in `index.html`
fetches it and swaps in a `data:` URI whose media query is forced to match the
site's ◐ theme toggle, so the tab icon follows the toggle rather than the OS.
If the fetch fails, the static link still follows the OS. `favicon.ico` and
`apple-touch-icon.png` are dark-only fallbacks.

## Planned next steps

The approved catalog plan is complete. Steps 1-4 are done: the catalog split,
product IDs, shared checks, and the CI split; reference files, `base`,
`platform`, `board_partner`, and `skus`; `sources`; and Linux vs Windows
(`system.os`). Remaining ideas, including a Linux-vs-Windows percentage view,
are in [TODO.md](TODO.md).

## Version and deployment

The project deploys `site/` using
[.github/workflows/build.yml](../.github/workflows/build.yml). Generated
`site/api/` files, and the generated pages below, are ignored and recreated in CI.

### Hosts

`build.yml` builds once on every push to `main`. The `deploy` job then publishes
to GitHub Pages, and `deploy-cloudflare` publishes the same files to the
Cloudflare Pages project `open-gpu-benchmarks` with
`cloudflare/wrangler-action@v3` (`pages deploy site --branch=main`). The
custom domain opengpubenchmarks.com is attached to that project. Both hosts
stay live.

[`preview.yml`](../.github/workflows/preview.yml) runs `build.py` and deploys a
Cloudflare **preview** for a pull request only when the PR comes from this
repository (not a fork) **and** its author is `github.repository_owner`. Every
other PR skips the job, so nobody else can trigger deployments. It uses
`pull_request`, never `pull_request_target`, so fork code never runs with
secrets. It posts or updates one PR comment (marker `<!-- cf-preview -->`)
with the commit URL and the branch alias URL. Cloudflare adds
`X-Robots-Tag: noindex` to preview deployments. The preview is not a required
check.

Secrets: `CLOUDFLARE_API_TOKEN` (Account > Cloudflare Pages > Edit) and
`CLOUDFLARE_ACCOUNT_ID`.

### SEO and AI crawlers

- Canonical origin: `build.SITE_URL = "https://opengpubenchmarks.com/"`.
  `site/index.html` has the canonical link, `og:url`, OG/Twitter tags, and
  `WebSite` + `Dataset` JSON-LD with the JSON endpoints as `DataDownload`. The
  same canonical on every host (github.io, `*.pages.dev`) makes search engines
  treat the mirrors as copies of the custom domain instead of competing
  duplicates. The mirrors deliberately get no `noindex`, since a canonical
  plus noindex is a mixed signal. The dashboard still fetches data relative
  to the page.
- `build.main(..., site_dir=SITE_DIR)` (the CLI passes it, tests pass a temp
  folder) also writes `benchmarks/index.html`, `llms.txt`, `llms-full.txt`, and
  `sitemap.xml` from the dashboard records, because most AI crawlers don't
  run JavaScript. They are listed in `build.SITE_PAGES` and gitignored.
- `site/robots.txt` (committed) allows everything, names the major AI
  crawlers explicitly, and sets
  `Content-Signal: search=yes, ai-input=yes, ai-train=yes`. `site/_headers` is
  read by Cloudflare only (CORS on `/api/*`, short caching, `nosniff`).
- `test_build.check_site_seo()` checks that the canonical, `og:url`, robots
  sitemap line, sitemap, and generated pages agree on `SITE_URL`, that
  robots.txt has no `Disallow`, and that every fixture summary appears in
  `benchmarks/index.html` and `llms-full.txt`. The page lives in a folder
  because Cloudflare Pages 308-redirects `*.html` to the bare path, and a
  canonical URL must not redirect.

### Cloudflare Pages (manual setup)

1. Workers & Pages > Create > Pages > **Direct Upload** project
   `open-gpu-benchmarks`, production branch `main`. Do not connect Git: that
   would build every branch and can't filter by PR author.
2. Custom domains: `opengpubenchmarks.com` and `www.opengpubenchmarks.com`.
3. Redirect Rule: `www.opengpubenchmarks.com/*` to `https://opengpubenchmarks.com/${1}` (301).
4. Bulk Redirect: `open-gpu-benchmarks.pages.dev` to `https://opengpubenchmarks.com`
   (301, preserve path and query, subdomain matching off so previews keep working).
5. Repo secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
6. Security > Bots: **Block AI bots off**, Bot Fight Mode off. AI Crawl
   Control: allow the crawlers, and turn off the managed robots.txt so ours is
   served unchanged.
7. Google Search Console Domain property (DNS TXT through Cloudflare); submit
   `https://opengpubenchmarks.com/sitemap.xml`. Optionally Bing Webmaster Tools.

### Versioned changes

For a versioned dashboard payload change:

1. Update `RELEASE_VERSION` and `SCHEMA_VERSION` in
   [`scripts/build.py`](../scripts/build.py).
2. Update current-version references, fixture counts, and feature summary in
   [README.md](../README.md) and this document, and move `Unreleased` in
   [CHANGELOG.md](../CHANGELOG.md) under the new version heading.
3. Run the build, validation, compile checks, and `git diff --check`.
4. Do not commit `site/api/` unless repository policy changes.
5. Create a Git tag only when explicitly requested after review.
