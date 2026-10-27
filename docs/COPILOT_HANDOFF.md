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
- Blog: <https://opengpubenchmarks.com/blog/> (RSS at `/blog/rss.xml`)
- Current version: `v1.13.0.0` (2026-10-27). Versions are now
  `MAJOR.MINOR.DATA.POST`, always four parts (see the Versioning section of
  [CHANGELOG.md](../CHANGELOG.md)). Every PR except a data-only result
  submission bumps it; a catalog PR (new GPUs) is a DATA bump.
  - v1.13.0.0: a `gpu-catalog` Copilot agent adds one or more GPUs from
    their makers' spec pages (from an "Add a GPU" issue or the agents
    panel) and makes the DATA bump. Board changes from the reference are
    listed in gpus.json as `reference_overrides` (schema 0.20) and on the
    dashboard; new rules `base-chip-override`, `base-redundant`, `base-id`.
  - v1.12.0.0: a `benchmark-processor` Copilot agent turns an assigned
    benchmark issue into a ready-to-approve data pull request, and
    `parse.py` takes `--date`. The benchmark bot takes one attached or pasted result file
    (the new "Benchmark result (file)" form, or any `benchmark` issue), and
    submitting is the CC BY 4.0 agreement: the forms have no required
    checkboxes. Unconvertible attachments get `needs-maintainer`
    (`docs/PROCESSING_ISSUES.md`).
  - v1.11.0.0: every release gets an annotated `v<version>` tag on its
    merge commit once the pull request merges; tags v1.3.0.0 through
    v1.10.0.0 were backfilled.
  - v1.10.0.0: fixes the summaries table's VRAM column, which showed the
    test system's RAM because two dashboard functions were both named
    `formatMemory`. `test_build.check_unique_site_functions()` now fails on
    a duplicate function name in `site/index.html`.
  - v1.9.0.0: official test benches (schema 0.18 → 0.19). The registry
    `data/testbenches.yaml` (`checks.load_testbenches()`, `testbench-*`
    rules) lists the maintainer's systems, each labeled by its memory type:
    DDR5 Bench, DDR4 Bench, DDR3 Bench. Official desktop runs require a
    top-level `testbench_id`, and the bench is a grouping key. The dashboard's
    "Form factor" chips became **Platform**, with one chip per DDR type. Also `api/v1/testbenches.json`, a "Test bench" column in
    `benchmarks/` and `llms-full.txt`, and `import_cyberpunk.py --testbench`.
    See [Test benches](#test-benches).
  - v1.8.0.0: `.github/FUNDING.yml` adds the GitHub Sponsors button
    (`github: MattyStacks`). No code, data, or API change.
  - v1.7.0.0: 309 reference GPU files (79 NVIDIA, 203 AMD, 27 Intel) from
    the vendors' spec pages, and new catalog fields for what vendors publish
    (schema 0.17 → 0.18): `silicon.tensor_cores`/`cache_mb`,
    `memory.speed_gbps`, `clocks.game_mhz`, `power.psu_w`, and
    `features.ray_tracing`/`ai_tops`/`encoder`/`decoder`/`directx`/`vulkan`/
    `opengl`/`cuda`/`technologies`. `bus_width_bits` allows up to 4096 (HBM).
    The RTX 5080 reference says DLSS 5. The dashboard's spec panel shows
    the new fields.
  - v1.6.0.0: system RAM in numbers (schema 0.16 → 0.17). `system.memory`
    (free text) is now `system.memory_gb` (a number), plus optional
    `memory_type` (`DDR5-6400`) and `memory_channels` (a whole number), rule
    `result-system-memory`. Added to the issue form and to
    `import_cyberpunk.py` (`--memory-type`, `--memory-channels`, which default
    to DDR5-6000 and 2 channels with a warning).
  - v1.5.0.0: the Dataset JSON-LD adds `creator` (Organization) and a
    `CreativeWork` `license`, Google's recommended Dataset fields.
  - v1.4.0.0: README rewritten as a short overview (dashboard, JSON
    endpoints, contributing, local dev, layout). Catalog usage notes moved
    to `data/gpus/README.md`; schema history and fixture details live only
    here.
  - v1.3.0.0: data license CC0 → CC BY 4.0 with reasonable attribution (AI
    training explicitly permitted), the `/license/` page, `_license` and
    `_source` in every API file (schema 0.15 → 0.16), and copyright lines on
    blog posts. Also the "Benchmark result" issue form and its bot pull
    requests (`benchmark-issue.yml`, `scripts/issue_to_result.py`), and
    macOS/Linux/WSL venv setup docs.
  - v1.2.0.0: the game registry. `data/games.yaml` (`checks.load_games()`,
    `game-*` rules) lists every game by `id`, `name`, `type`, and `year`, plus
    optional `steam_appid`, `igdb_id`, and `url`. Results name their game by
    `game_id` (schema 0.14 → 0.15, new `games.json`), and the dashboard picker
    became "Benchmark". It also brings required result `date`s with an
    optional per-run `time` (schema 0.14), and phone layout fixes.
  - v1.1.0.0: `/blog/` (Astro) for posts, guides, and reviews, with
    data-driven `<BenchChart>`, affiliate links with an automatic disclosure,
    and an AI-editing note. Also four-part versions and a fourth PR check,
    **Blog**. The dashboard's empty reviews panel became **Featured GPU
    picks** (`data/picks.yaml`, `checks.load_picks()`, `pick-*` rules), and
    API schema 0.12 → 0.13 adds `picks` to `dashboard.json`. The first post,
    `why-im-starting-open-gpu-benchmarks`, ships with it.
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
data/official/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
data/community/<gpu_id>/raw/**                         optional raw evidence
data/games.yaml                                        game registry (game_id -> name, type, year)
data/testbenches.yaml                                  test bench registry (official desktop runs' testbench_id)
                 |
                 v
python scripts/build.py
                 |
                 v
site/api/v1/gpus.json
site/api/v1/official/<gpu_id>/summary.json
site/api/v1/community/<gpu_id>/summary.json
site/api/v1/dashboard.json
site/api/v1/games.json
site/api/v1/testbenches.json
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

Schema `0.13` adds `picks` to `dashboard.json`, the featured GPU cards (see
[Featured GPU picks](#featured-gpu-picks)), and `metadata.license` (see
[Licenses](#licenses)) to every API file.

Schema `0.14` adds `date` and `time` to every run record. `date` is the result
file's required top-level `date: 'YYYY-MM-DD'` (`checks.check_result_date()`):
the day it was run, or a found result's publish date, and it must equal the
file name's `YYYYMMDD` (`checks.RESULT_FILE_DATE`). `time` is a `result`
item's optional local `'HH:MM'` or `'HH:MM:SS'` (`checks.TIME_OF_DAY`, no
time zone), `""` when not set. Neither is a grouping key; they exist so old
runs can be filtered, charted over time, or retired later.
`import_cyberpunk.py` writes both from the run folder name and backfills
files that lack them (`upgrade_files()`); `parse.py` writes today's date.

Schema `0.18` adds catalog fields for what vendor spec pages publish:
`silicon.tensor_cores` (NVIDIA tensor cores, AMD AI accelerators, Intel XMX
engines), `silicon.cache_mb` (last-level cache), `memory.speed_gbps`,
`clocks.game_mhz` (AMD game frequency, Intel graphics clock), `power.psu_w`
(100-2000 W), and `features.ray_tracing`, `ai_tops`, `encoder`, `decoder`,
`directx`, `vulkan`, `opengl`, `cuda`, and `technologies` (a list of the
vendor's feature names as written). `memory.bus_width_bits` now allows
32-4096. All are optional and pass through `gpus.json` unchanged.

Schema `0.19` adds test benches. Every run record and summary carries
`testbench_id` (the bench its summaries join, after `counts_as`),
`testbench_source_id` (the bench the file names), `testbench_name`,
`testbench_memory` (the DDR type, such as `DDR5`), and `testbench_label`
(`DDR5 Bench`, the dashboard's chip and bar label). All five are
`""` on community runs and on laptop, handheld, and iGPU runs.
`testbench_id` joins the grouping key and `comparison_policy.group_by`;
`testbench_source_id` is in every `implementations` entry, so a folded-in
interim run stays traceable. `dashboard.json` gains a `testbenches` list, and
the new `testbenches.json` holds the registry.

### Test benches

`data/testbenches.yaml` (`checks.load_testbenches()`) is a `testbenches:` list.
Each entry needs `id`, `name`, `status` (`active`, `planned`, `interim`, or
`retired`), `cpu`, and `memory_type` (`DDR5-6000`; a planned bench may write
just `DDR3`), plus `memory_gb` and `memory_channels` unless it's `planned`.
There is no generation field: the bench's label comes from the DDR type in
`memory_type` (`checks.testbench_memory()`, `testbench_label()`), and
`checks.testbench_rank()` orders benches newest memory first, so a DDR6
system needs no code change; move `primary: true` to it. Exactly one bench is
`primary: true` (`testbench-primary`). `counts_as: <bench>` folds a bench into
another with the same DDR type (`testbench-counts-as`;
`checks.resolve_testbench_id()`). The
file is optional to the loader, but without it no official desktop run passes.

The current benches: `am5_9800x3d_ddr5` (DDR5, primary),
`am4_5600x3d_ddr4` (DDR4), `lga1150_4790_ddr3` (DDR3, planned until the
system is confirmed working), and `am5_9950x3d_ddr5` (DDR5, interim: the
maintainer's main PC, which holds the RTX 5080 FE runs). When the 5080 FE is
re-run on the 9800X3D, either set `counts_as: am5_9800x3d_ddr5` on the
9950X3D bench (results within margin of error) or delete its runs.

`checks.check_testbench()` applies these result rules on game runs:
`result-testbench-id` (an official desktop run without one, or a non-desktop
run with one), `result-unknown-testbench`, `result-testbench-community` (a
community file that sets one), and the `result-testbench-mismatch` warning
(`checks.testbench_mismatches()`: `system.cpu` or memory disagrees with the
bench; the CPU matches when either name contains the other). The
`community-outlier` baseline (`checks.official_baseline()`) counts only
official runs with no bench (non-desktop) or on the primary bench.

`import_cyberpunk.py --testbench <id>` is required with `--source official`
for a desktop GPU and refused otherwise. It writes `testbench_id` after
`gpu_id`, takes `memory_type` and `memory_channels` from the bench (so no
default warning), and `testbench_id` is in `SETUP_KEYS`, so a second bench on
the same day goes in a `_2` file.

**Reference catalog (v1.7.0.0).** `data/gpus/reference/` holds 309 files:
NVIDIA desktop RTX 50/40/30/20 and GTX 16/10, plus RTX 50/40/30 laptop GPUs;
every Radeon on amd.com's specification list (desktop and mobile, back to
HD 5000); and Intel Arc B/A desktop, mobile, and embedded, plus the six
integrated Arc GPUs on Intel's laptop page (no memory token, `memory.shared`).
The vendor's value always wins. Wikipedia fills only chip details the vendor
leaves out, and only when they agree with the vendor's counts; NVIDIA's are
also checked against the per-series articles. Where a vendor lists two
configurations or contradicts itself, the field is left out and `notes`
says why. The files were generated by scratch scripts that aren't in the
repo, so edit them by hand from now on. TechPowerUp blocks automated fetches,
and amd.com only works with a browser user agent. Reference files appear in
`gpus.json` only through a product's `base:` (see `docs/TODO.md`).

Schema `0.17` makes system RAM numeric. `system.memory_gb` (a number of GB,
1-65536) replaces the free-text `system.memory`. Optional `memory_type` is
text such as `DDR5-6400` and only warns when it doesn't look like
`<type>-<MT/s>` (`checks.MEMORY_TYPE_PATTERN`). Optional `memory_channels` is
a whole number from 1 to `checks.MAX_MEMORY_CHANNELS` (32). All three are
checked by `checks.check_system_memory()` (rule `result-system-memory`), and a
missing one is never reported. The old `memory` and `ram` keys are errors.
Run records carry `memory_gb` and `memory_channels` as numbers or `null` and
`memory_type` as a string (`""` when missing). Summary `implementations` list
the same three keys. None of them group runs or are charted. The dashboard's
run details join them as "64 GB DDR5-6400 dual channel" (`formatMemory()`).
Cyberpunk's `summary.json` only reports the size, so `import_cyberpunk.py`
takes `--memory-type` and `--memory-channels`. When either is left out, it
records `DEFAULT_MEMORY_TYPE` (`DDR5-6000`) or `DEFAULT_MEMORY_CHANNELS` (2)
and prints a warning (`memory_defaults()`). Because `system` applies to the
whole file, a re-import without the same options starts a `_2` file.
`upgrade_files()` rewrites an older `memory: 64 GB` to `memory_gb: 64`.

Schema `0.16` switches the data license to CC BY 4.0 and leads every API file
with `_license` and `_source` (see Licenses).

Schema `0.15` adds the game registry. Result files name their game with
`game_id`, an ID from `data/games.yaml` (`checks.load_games()`), instead of
free-text `game`; the old key fails `result-game-id`, and an unregistered ID
fails `result-unknown-game` with a stub entry to paste in. Each registry entry
needs `id`, `name`, `type` (`checks.GAME_TYPES`: `game`, `synthetic`,
`engine_demo`), and `year`; `steam_appid`, `igdb_id` (positive integers), `url`
(https), and `notes` are optional. Every run record carries `game_id`, `game`
(the registry name), `game_type`, and `game_year`. Summaries group by `game_id`,
and `comparison_policy.group_by` says so. `dashboard.json` `games` is now a list
of `{id, name, type, year}` objects for the games with summaries, sorted by name,
and the new `games.json` holds the whole registry. The dashboard's picker is
labeled "Benchmark" and groups options by type; the plain tables' column is
"Benchmark". `validate.py` reports the registry on both the `catalog` and
`results` targets, because a result for a new game adds its entry in the same
pull request. `import_cyberpunk.py` rewrites its older files' `game:` to
`game_id:` when re-run. A remaster, edition, or different test gets its own ID;
a patch stays in `version`, which never groups.

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
  upgradeable, so it stays on each run in `system.memory_gb` (a number since
  schema 0.17).
- **Vendor field.** `identity.vendor` is renamed to `identity.gpu_vendor`.
  Run records carry `gpu_vendor` instead of `vendor`, and the dashboard
  reads `record.gpu_vendor`.
- **Required fields.** Only five are required: `id`, `identity.name`,
  `identity.gpu_vendor`, `classification.form_factor`, and
  `memory.capacity_gb`.
- **Optional fields.** These are still type-checked and range-checked: quoted
  dates, capacity 1-512 GB, bus width 32-4096 bits, TDP 5-600 W, PSU
  100-2000 W. Unknown
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
- **Board changes (schema 0.20).** `checks.reference_overrides()` compares
  every field a product writes with its reference. A differing chip field
  (`BASE_CHIP_FIELDS`: codename, architecture, `silicon.*`, memory
  capacity/type/bus/shared) is `base-chip-override`; an equal value is the
  `base-redundant` warning; any other difference goes in the merged entry's
  `reference_overrides`, a list of `{field, value, reference}` in
  `CATALOG_FIELDS` order (`[]` without a base or changes). `identity.name`,
  `identity.gpu_vendor`, `notes`, `sources`, and fields the reference lacks
  are never compared. The dashboard's expanded row shows the list as
  "Changed from the reference" chips (`formatOverrides()`). Desktop and
  laptop IDs must start with `<base>_` (`base-id`, in `check_catalog_id`).
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
- Official desktop runs name their test bench (`testbench_id`, from
  `data/testbenches.yaml`), and the bench is a grouping key, so one GPU on two
  benches is two summaries. Only official desktop runs use it; community
  files and other form factors never do.
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
  name is `result_YYYYMMDD_<game_id>.yaml`, with `_2`, `_3` for same-day repeats
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

`benchmark_type` defaults to `game`. Game source files need `game_id` and a
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
`p1_low` is the `result-no-p1-low` warning per entry, one `info` per file
for `P1_LOW_INFO_METHODS` (`in_game_benchmark`), and silent for
`synthetic_benchmark`). `info` is the third issue level: `Issues.info()`,
shown by `validate.py` (counted as "N info"), hidden by `build.py`, written as
a `::notice` annotation in GitHub Actions, and it never fails a check. The community outlier limit is 25%
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
an ordinary game run (`game_id: 3dmark_steel_nomad`, its fixed resolution, a fixed
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
python -m py_compile scripts/checks.py scripts/build.py scripts/validate.py scripts/parse.py scripts/import_cyberpunk.py scripts/issue_to_result.py scripts/test_build.py
npm --prefix blog ci                     # Node 22.12+; once, or after the lockfile changes
npm --prefix blog run build              # after build.py; writes site/blog/
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
every pull request as four jobs, so the PR shows which part failed:

- **Catalog entries**: `validate.py catalog`
- **Benchmark results**: `validate.py results`
- **Build and tests**: `py_compile`, `build.py`, `test_build.py`
- **Blog**: `build.py`, then `npm --prefix blog ci` and `npm --prefix blog run build` (Node 22)

There is deliberately no `paths:` filter. A required check that is skipped
never reports, and that blocks the merge. Each job takes seconds.

[`build.yml`](../.github/workflows/build.yml) runs `validate.py` before
`build.py`, so `main` cannot deploy bad data.

**Repo setting (manual):** `main` is protected by the "Base Rules" ruleset
(Settings → Rules), not classic branch protection. It requires a pull request
and the required status checks; see
[Benchmark issues and the bot App](#benchmark-issues-and-the-bot-app-manual-setup)
for the code-owner approval settings.
[`scripts/parse.py`](../scripts/parse.py) writes converted CSV output directly
to `data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml`. `--game-id` must
be in `data/games.yaml`; an unknown one exits with the known IDs. `--submitted-by` is optional and only written when given. It
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
  with `summary.json` (settings) and `frames.csv` (one row per frame; the
  `Frame time (ms)` column gives `avg_fps` = frames / total time and
  `p1_low` = the 1st percentile of per-frame FPS, `parse.percentile`). The
  frames.csv numbers are used only when its frame count equals `frameNumber`
  and its average is within 1% of `averageFps` (`FRAMES_AVG_TOLERANCE`);
  otherwise the run gets summary.json's average and no `p1_low`. Each import
  also fills `p1_low` (and the frames.csv average) on runs already in the
  `--gpu-id`/`--source` folder that lack one, when their run folder is still
  there (`add_p1_lows`). `PROOF_FORMAT` stays `cyberpunk_summary_json`
  because `proof` is a file-level setup key. The script finds the
  folder through the Windows Documents known folder (handles OneDrive), or
  the Proton prefix of Steam app 1091500 on Linux; `--input` overrides.
  Nothing is copied into the repo.
- **Files and re-runs.** Runs go in `result_YYYYMMDD_cyberpunk_2077.yaml` by
  run date, one `result` item per run. Each item's `benchmark_run` holds its
  folder name (it ends up in the API under `metrics`). A run whose
  `benchmark_run` is in any `data/{official,community}/*/` result file is
  skipped. A new same-day run is appended to the day's file when every
  file-level field matches (`SETUP_KEYS`: `gpu_id`, `submitted_by`, `game_id`,
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
  dashboard groups. `avg_fps` and `p1_low` come from `frames.csv` (see
  Input); without it, `avg_fps` is `averageFps` and there is no `p1_low`
  (`proof.method: in_game_benchmark`, one `result-no-p1-low` info per file).
  A missing `frames.csv` never fails the import.
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

**Published data (`data/`).** 1 catalog GPU entry (`rtx_5080_16gb_fe`) plus
309 reference files under `data/gpus/reference/`, 34
official result runs, 0 community runs, and 30 dashboard summaries: Cyberpunk
2077 built-in benchmark runs on Windows at 1080p, 1440p, and 4K, imported with
`scripts/import_cyberpunk.py`. Every run has an `avg_fps` and `p1_low` from
its `frames.csv`. `data/` is what
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

The fixtures have 11 catalog GPU entries, 21 official result runs, 12
community result runs, and 31 combined dashboard summaries. Their own
`testbenches.yaml` copies the real benches, except that the interim 9950X3D
bench `counts_as` the primary one. Every official desktop fixture is on the
primary bench, except two: the RTX 4070 Super's Cyberpunk 2077 1440p Ultra run
on the previous-gen bench (its own summary, next to the primary one), and an
RTX 4090 Cyberpunk 2077 run on the interim bench that folds into the primary
summary (`run_count` 2). `check_testbench_payload()` asserts both. Six Linux runs pair
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

**Platform chips.** The "Platform" chip row (`platforms()`,
`renderFactorFilters()`) has one chip per test bench memory type, built from
the data and sorted newest first ("DDR5 Bench", "DDR4 Bench", ...), then
"Desktop · community", Laptop, Handheld, and iGPU. `platformKey()` is
`desktop:<testbench_memory>` for official desktop runs and
`desktop:community` for community ones. Every chip starts on
(`state.factors = new Set(platforms())` in `initialize()`), so the first view
shows every platform. Only platforms with records get a chip. `benchSuffix()` adds the bench
to a bar label (`testbench_label`, or `testbench_name` when two benches share
a label) only when the same GPU is on more than one bench in view. The table's
"Platform" column (sort key `form`, by `platformRank()` then GPU name) shows
`formatForm()`: "Desktop: DDR5", "Desktop: community", or the form factor (the
chips say "DDR5 Bench"; the column leaves "Bench" out). Every bench badge uses the plain `form-desktop`
style (no bench is shown as lesser); `platformClass()` gives only community
rows a `form-desktop-community` shade mixed from `--form-desktop` (no new
color tokens).
Run details show "Bench: <name>" from `dashboard.json`'s `testbenches`.

**Upscaled vs native.** Many presets turn an upscaler on, so one GPU can have
several bars at one resolution and preset (4K High: FSR 2.1 Quality and
native). Each y-axis label is ECharts rich text: the label text plus a pill
holding `upscalingLabel()`, the upscaler or `Native`. `upscalerFamily()` picks
the pill's rich style and the table badge class from the upscaler's maker:
`dlss` (DLSS and DLAA, green `--up-dlss`), `fsr` (red `--up-fsr`), `xess` (blue
`--up-xess`), `upscaled` (any other upscaler, amber `--upscaled`), and `native`
(`--muted`). Each token has a softer dark-theme and a deeper light-theme shade,
all at least 4.5:1 against the panel. Pill colors are rgba()
from the hex tokens, because canvas text can't use CSS `color-mix()`. The label
text comes from `displayParts()`: the GPU name, the preset when more than one
preset is visible, and the OS under the existing both-OSes rule. The GPU name is
shortened first so the pill and the distinguishing parts stay whole, and when
every visible bar is the same GPU the label leaves the name out
(`singleGpuName()`; the chart description names it). `plainName()` adds
`(upscaler)` or `(native)` for the comparison sentence and "Top result". The
Native/Upscaled chips (`state.upscaling`, `renderUpscalingFilters()`) filter
like the OS chips. The table's Settings column shows the preset and an
`.upscale-badge upscale-<family>`, and sorts native rows first. The tooltip shows the preset and
upscaler.
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

## Blog

`/blog/` holds posts, guides, and reviews. It's an Astro project in
[`blog/`](../blog/) (Node 22.12+, exact versions in
`blog/package-lock.json`). It renders
`content/posts/<slug>/index.md(x)` into `site/blog/`, which is gitignored like
`site/api/`. The author's guide is [content/README.md](../content/README.md).

```text
content/posts/<slug>/index.md(x) + images
                 |
python scripts/build.py   -> site/api/v1/** (charts read it), sitemap + llms.txt list non-draft posts
npm --prefix blog run build -> site/blog/<slug>/, /posts/, /guides/, /reviews/, /tags/<tag>/, rss.xml
```

- **Schema**: `blog/src/content.config.ts`, using Zod through `astro/zod`.
  - Required: `title`, `description`, a quoted `date`, and `type`
    (`post`/`guide`/`review`).
  - Optional: `updated`, kebab-case `tags`, and `gpu_ids`, which must be
    catalog file names (a review requires at least one). Also `author`,
    `ai_generated`, `ai_assistance`, `affiliate`, `draft`, `hero` + `hero_alt`, and, for reviews
    only, `verdict`, `pros`, and `cons`.
  - The schema is `.strict()`, so unknown fields fail.
  - The glob loader's `base` is relative (`../content/posts`), because an
    absolute Windows path breaks it.
- **Body rules**: `blog/src/lib/posts.ts` enforces two rules that need the
  post body:
  - Reserved slugs (`tags`, `posts`, `guides`, `reviews`) are rejected.
  - `<AffiliateLink>` is only allowed with `affiliate: true`.

  Drafts show only on the dev server (`import.meta.env.DEV`).
- **Components** are passed to MDX through `<Content components={...}>` in
  `src/pages/[slug].astro`, so posts don't import them:
  - `<BenchChart>` (`src/components/BenchChart.astro`) filters
    `dashboard.json` records by gpu, exact `game_id`, resolution, preset,
    os, and source (official by default). It renders HTML/CSS bars, no SVG and
    no JS, so it reflows on phones, and it throws if nothing matches.
  - `<Callout>` is a note, tip, or warning banner.
  - `<AffiliateLink>` gives the link `rel="sponsored nofollow noopener"` and
    an "affiliate" badge. `src/data/retailers.ts` lists Amazon (adds its
    `tag` param once an ID is set), Newegg, and Best Buy (paste the network
    tracking URL). No IDs are set yet.
  - `PostLayout` adds `DisclosureBanner` when `affiliate: true` (with
    Amazon's required sentence), `ReviewSummary` for reviews (specs from
    `gpus.json`, plus verdict and pros/cons), and the "Edited with AI
    assistance" footer for `ai_generated`/`ai_assistance`.
- **Base path**: `BLOG_BASE` (default `/blog`) is Astro's `base`.
  - `build.yml` builds the blog once for Cloudflare and uploads the `site`
    artifact. It then rebuilds with `BLOG_BASE=/open-gpu-benchmarks/blog` for
    the GitHub Pages artifact. Astro empties `site/blog/` on each build.
  - `siteRoot()` gives the dashboard root.
  - Canonical, `og:url`, `og:image`, JSON-LD, and RSS links always use
    `https://opengpubenchmarks.com/blog/`.
- **Style**: `blog/src/styles/tokens.css` is a verbatim copy of the two
  `:root` blocks in `site/index.html`, and `test_build.check_blog_tokens()`
  compares them. `blog.css` re-creates the dashboard's header, buttons,
  chips, and panels without touching `index.html`. The theme script uses the
  dashboard's `open-gpu-benchmarks-theme` localStorage key. The dashboard's
  only change is a relative "Blog" header link.
- **Tests**: `test_build.check_blog_posts()` covers draft exclusion and
  sitemap `lastmod` from `updated`. `check_release_version()` checks the
  four-part `RELEASE_VERSION` against the newest changelog release.
- **Images**: Astro's sharp converts post images to WebP at build.
  `site/_headers` caches `/blog/_assets/*` as immutable (the file names are
  content-hashed).

## Licenses

- **Code**: MIT, in [`LICENSE`](../LICENSE) ("MattyStacks and Open GPU
  Benchmarks contributors", 2026).
- **Data**: CC BY 4.0 with reasonable attribution. [`data/LICENSE`](../data/LICENSE)
  is a short project header followed by the unmodified official legal code.
  The public explanation is the checked-in `site/license/index.html`
  (<https://opengpubenchmarks.com/license/>). AI training is explicitly
  permitted. Sites credit "Data from Open GPU Benchmarks" with a link, and a
  chart image or video may use "Source: opengpubenchmarks.com". AI models
  credit it in their model card or docs, not in every output. Data published
  before the switch (through v1.2.0.0) was CC0, and copies made then keep
  those terms.
- **Where it's stated**: `build.DATA_LICENSE` (`CC-BY-4.0` + URL),
  `build.DATA_ATTRIBUTION`, and `build.API_LICENSE`. `write_json()` puts
  `_license` (`API_LICENSE`) and `_source` (`url`, `generated_at`) first in
  every API file. `metadata.license` is still written too. `llms.txt`,
  `llms-full.txt`, and `benchmarks/index.html` carry the license and the
  credit line, and the sitemap lists `license/`. `site/index.html`'s Dataset
  JSON-LD has `creator` (an `Organization`), `license` (a `CreativeWork`
  with the CC BY 4.0 URL), `usageInfo` (the license page), and `creditText`;
  Google lists `creator` and `license` as recommended Dataset fields.
  The footers of the dashboard and the blog link `license/`.
- **Blog writing** (`content/`) stays the author's copyright, all rights
  reserved, and is under neither license. A post with `ai_generated: true`
  claims no copyright in its text. `PostLayout.astro` prints the matching
  line on every post and adds `copyrightHolder` and `copyrightYear` to a human
  post's JSON-LD.
- **Submissions**: the plain-English terms ("Your results become public
  data" in `docs/COMMUNITY_SUBMISSIONS.md`) say five things:
  1. anyone can use a submitted result for anything, AI training included;
  2. sites must credit Open GPU Benchmarks and link back;
  3. the submitter's own credit stays here;
  4. it can't be taken back;
  5. it covers raw captures and machine details.

  The same five points appear in full on the dashboard's submission panel, on
  `license/`, and in both issue forms (a markdown notice: submitting the
  issue is the agreement, so there's no checkbox, and a result file needs no
  license line). Found results
  contribute only the numbers and a link, and a friend's numbers need their
  agreement to public release. `.github/pull_request_template.md` has a
  CC BY 4.0 checkbox for results and an MIT checkbox for code.
- **Test**: `test_build.check_licenses()` checks both license files, every
  API file's `_license` and `_source`, the JSON-LD, the license page,
  `llms.txt`, and `benchmarks/`.

## Featured GPU picks

The dashboard panel near the bottom shows three cards, one per GPU maker, in
`checks.PICK_SLOTS` order (`amd`, `nvidia`, `intel`). They come from
[`data/picks.yaml`](../data/picks.yaml), which is optional and may be empty.
`checks.load_picks()` validates it (`pick-slot`, `pick-field`, `pick-gpu-id`,
`pick-link`, documented in `data/gpus/README.md`). `validate.py catalog` and
`build.py` both run it.

- **Fields**: `slot`, `note` (required), `name` (required unless `gpu_id`
  names a catalog product), an optional `gpu_id` whose vendor must match the
  slot, `label` (a badge of at most 24 characters), and `links` (at least one
  `retailer` + https `url`).
- **Retailers**: `checks.PICK_RETAILERS` lists amazon, newegg, and bestbuy.
  Keep it in step with `blog/src/data/retailers.ts`.
- **API**: `build.py` writes `dashboard.json` → `picks`, adding `vram_gb`,
  `tdp_w`, and `form_factor` from the catalog and `retailer_name` per link.
- **Dashboard** (`renderPicks()` in `site/index.html`):
  - Each card's top border is its maker's color (the chart's vendor colors).
    Empty slots say "<Maker> pick coming soon".
  - Store buttons use `rel="sponsored nofollow noopener"`.
  - A catalog pick with published runs gets "See benchmarks", which filters
    the table by the card's name.
  - The affiliate disclosure is above the cards, adds Amazon's sentence when
    any Amazon link exists, and hides when there are no picks.
- **No prices**, because they go stale and Amazon's Operating Agreement
  forbids prices not taken from its API.
- **Fixtures**: `tests/fixtures/data/picks.yaml` has an NVIDIA catalog pick
  and an Intel free-form pick. The AMD slot is empty on purpose.
- **Reviews**: `data/reviews.yaml` and the API's `reviews` field remain, but
  the dashboard no longer shows them. Reviews are blog posts now.

## Planned next steps

The approved catalog plan is complete. Steps 1-4 are done: the catalog split,
product IDs, shared checks, and the CI split; reference files, `base`,
`platform`, `board_partner`, and `skus`; `sources`; and Linux vs Windows
(`system.os`). Remaining ideas, including a Linux-vs-Windows percentage view,
are in [TODO.md](TODO.md).

## Version and deployment

The project deploys `site/` using
[.github/workflows/build.yml](../.github/workflows/build.yml). Generated
`site/api/` files, the generated pages below, and `site/blog/` are ignored and recreated in CI.

### Hosts

`build.yml` builds once on every push to `main`. The `deploy` job then publishes
to GitHub Pages, and `deploy-cloudflare` publishes the same files to the
Cloudflare Pages project `open-gpu-benchmarks` with
`cloudflare/wrangler-action@v3` (`pages deploy site --branch=main`). The
custom domain opengpubenchmarks.com is attached to that project. Both hosts
stay live.

[`preview.yml`](../.github/workflows/preview.yml) runs `build.py` and the blog build, and deploys a
Cloudflare **preview** for a pull request only when the PR comes from this
repository (not a fork) **and** its author is `github.repository_owner`. Every
other PR skips the job, so nobody else can trigger deployments. A
`benchmark/*` branch (a bot PR from a benchmark issue) always skips it, even
after a maintainer pushes to it. It uses
`pull_request`, never `pull_request_target`, so fork code never runs with
secrets. It posts or updates one PR comment (marker `<!-- cf-preview -->`)
with the commit URL and the branch alias URL. Cloudflare adds
`X-Robots-Tag: noindex` to preview deployments. "Cloudflare preview" is a
required check in the "Base Rules" ruleset; a job skipped by its `if:` reports
as passing, so other PRs aren't blocked.

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

### Benchmark issues and the bot App (manual setup)

The issue is the primary way to submit a result. Pull requests are for bulk
or scripted uploads (the Cyberpunk importer, many files, raw captures).

**Flow.** [`.github/ISSUE_TEMPLATE/benchmark.yml`](../.github/ISSUE_TEMPLATE/benchmark.yml)
(fields) and [`benchmark_file.yml`](../.github/ISSUE_TEMPLATE/benchmark_file.yml)
(one result file) are forms that apply the `benchmark` label; any other issue
with that label is read too.
[`benchmark-issue.yml`](../.github/workflows/benchmark-issue.yml) runs on
`issues` (opened, edited, labeled, reopened) when that label is present. It
checks out `main` and runs
[`scripts/issue_to_result.py`](../scripts/issue_to_result.py), which parses
the form and writes `data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml`:

- the GPU from its ID or exact `identity.name`, with `difflib` suggestions;
- the game from its `game_id` or exact name in `data/games.yaml`
  (`find_game`, also with suggestions). Only listed games are accepted; the
  bot never writes `games.yaml`, so a new game needs its own pull request;
- preset spellings reused from existing runs of that game, ignoring case;
- `_2`, `_3`, ... for a name that's taken.

Without the form's `### GPU` heading, the script looks for one result file
instead (`issue_file`): a `github.com/user-attachments/files/<id>/<name>` link
ending `.yaml`/`.yml`/`.json`, a ```` ```yaml ````/```` ```json ```` block, or
the file form's **Result file** box pasted as plain text. Downloads follow
redirects only to `*.githubusercontent.com` (`GitHubRedirects`), stop at
`MAX_FILE_BYTES` (1 MB) and `DOWNLOAD_SECONDS` (20), and are saved under
`$OUT/attachments`, outside the checkout. YAML loads with `NoAliasLoader`
(aliases refused). `run_from_file` requires `gpu_id`, `game_id`, `date`, and
`result`, resolves the GPU and game like the form, drops `DROPPED_KEYS`
(`submitted_by`, `testbench_id`, `source`, `synthetic`), sets `submitted_by`
only from the Credit box, and keeps every other field. Two result files fail
("one per issue"). Attachments with no result file exit 3: the workflow
replies and adds the `needs-maintainer` label, and a maintainer follows
[PROCESSING_ISSUES.md](PROCESSING_ISSUES.md). An issue with nothing to read
gets a reply linking both forms. Tests pass the hidden `--attachment-dir`
(`tests/fixtures/issues/attachments/<id>/<name>`), so they never touch the
network; the workflow must never pass it (`check_bot_safety`).

**The benchmark-processor agent.** For a `needs-maintainer` issue, or any
benchmark issue the bot couldn't finish, a maintainer assigns the issue to
Copilot and picks the `benchmark-processor` custom agent
([`.github/agents/benchmark-processor.agent.md`](../.github/agents/benchmark-processor.agent.md)).
It writes the result YAML from whatever the issue holds, using `parse.py`
(with `--date`) or `import_cyberpunk.py` when they fit, adds a missing GPU or
game with sources, runs `validate.py`, `build.py`, and `test_build.py`, and
opens a data-only pull request (no version bump) listing its assumptions, or
a draft with questions. Its environment is
[`copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml)
(one read-only job; Copilot reads it from `main` only). Attachment downloads
may need `objects.githubusercontent.com` on the repository's Copilot
internet-access allowlist. `check_bot_safety` checks the profile's
frontmatter and that the setup job is the only job, read-only, and
secret-free. Setup and usage are in [PROCESSING_ISSUES.md](PROCESSING_ISSUES.md).

**The gpu-catalog agent.** [`.github/agents/gpu-catalog.agent.md`](../.github/agents/gpu-catalog.agent.md)
adds catalog products. Start it by assigning an "Add a GPU" issue
([`gpu_request.yml`](../.github/ISSUE_TEMPLATE/gpu_request.yml), label
`gpu-request`; no workflow reacts to it) to Copilot with this agent, or by
prompting it in the agents panel ("Add the SPARKLE Arc A310 ECO, spec sheet:
<url>"). For each product it downloads the maker's page or PDF (read with
`pdftotext`, which `copilot-setup-steps.yml` installs from `poppler-utils`),
picks the reference, writes only the board's changes and product-only
fields, and checks `reference_overrides` in the built gpus.json. One pull
request covers every product in the request and makes one DATA bump:
`RELEASE_VERSION`, a `CHANGELOG.md` heading with one "Catalog:" line per GPU,
the current-version lines, and the catalog GPU counts. Spec sites such as a
board maker's may need adding to the Copilot internet-access allowlist; the
agent opens a draft naming the domain when it's blocked.

Submitting the issue is the CC BY 4.0 agreement. Neither form has a required
checkbox (`check_issue_form_matches_script` fails on one), and the pull request
body says the result was submitted under CC BY 4.0.

The script then runs `checks.load_results` and keeps only the new file's
issues. On errors it writes nothing, and the bot updates one marker comment
(`<!-- benchmark-bot -->`) on the issue saying what to fix. On success the bot:

- commits only that file to `benchmark/issue-<N>` and force-pushes it;
- opens or updates the pull request (label `benchmark`, body with the YAML
  and a reviewer checklist, `Closes #N`);
- links the pull request in the marker comment.

Editing the issue reruns the whole flow on the same branch. While
`MAX_OPEN_PRS` (10) `benchmark/issue-*` pull requests are open, new issues get
a "queue full" reply instead.

The forms' labels and options must match `FIELDS`, `FILE_FIELDS`,
`CAPTURE_TOOLS`, `WHO_RAN_IT`, `OSES`, and `GRAPHICS_APIS` in the script. The capture-tool
options must also match `checks.PROOF_METHODS`. `test_build.py`
(`check_issue_form_matches_script`) enforces both, and
`tests/fixtures/issues/` holds rendered issue bodies for the tests
(`valid.md`, `file_attached.md`, `file_form.md`, `csv_attached.md`) and
their attachments.

**Why a GitHub App and not `GITHUB_TOKEN` or a personal token.**

- Pull requests opened with `GITHUB_TOKEN` trigger no workflows, so the
  required checks would never report.
- Using `GITHUB_TOKEN` would also need "Allow GitHub Actions to create and
  approve pull requests", which must stay **off**.
- A personal token would make the owner the PR author. Cloudflare previews
  would then run, and the owner couldn't approve their own PR.
- An App's pull requests run `validate.yml` normally. The required "Cloudflare
  preview" check reports as *skipped*, which counts as passing.

**Safety.** These hold, and `test_build.py` (`check_bot_safety`) checks the
parts it can:

- **No deploys.** `benchmark-issue.yml` never references the Cloudflare
  secrets. `preview.yml` deploys only when the PR author is the owner *and*
  the branch isn't `benchmark/*`. `build.yml` deploys only from a push to
  `main`, and the App can't push there: the ruleset requires a pull request
  and the App isn't a bypass actor.
- **No workflow edits.** The App has **no Workflows permission**, so GitHub
  rejects any push from it that touches `.github/workflows/`.
- **No approvals or merges.** The App isn't a code owner, and the workflow
  never calls a review or merge API.
- **Untrusted text.** The issue body reaches the script through an `env:` var
  and a file, never `${{ }}` inside a shell line. YAML is written with
  `yaml.dump`, and replies put user text in escaped code spans or fences. The
  workflow checks that the only change is the one
  `data/community/*/result_*.yaml` file before committing.
- **Short-lived token.** The token is minted per run, expires within an
  hour, and is scoped to contents, pull-requests, and issues on this repo.
- **Residual risk.** Spam issues produce bot PRs, capped by the queue limit,
  that a maintainer closes. Fake numbers are caught the same way as any PR:
  `community-outlier` plus review.

**One-time setup:**

1. Create a GitHub App (Settings → Developer settings → GitHub Apps → New):
   - webhook off;
   - repository permissions **Contents: Read and write**, **Pull requests:
     Read and write**, **Issues: Read and write**, Metadata: Read;
   - **Workflows: No access**, and no organization or account permissions;
   - installable "Only on this account".
2. Install it on this repository only.
3. Save the App ID as the Actions *variable* `BENCHMARK_BOT_APP_ID`, and a
   generated private key as the Actions *secret* `BENCHMARK_BOT_PRIVATE_KEY`.
4. Edit the "Base Rules" ruleset:
   - required approvals **1**;
   - **Require review from Code Owners**;
   - **Require approval of the most recent reviewable push**;
   - add **Repository admin** as a bypass actor in "pull requests only" mode,
     so the owner's own PRs can still merge;
   - optionally add "Catalog entries" and "Benchmark results" as required
     checks.
5. Leave Settings → Actions → General → "Allow GitHub Actions to create and
   approve pull requests" **off**.

**Maintainers.** [`.github/CODEOWNERS`](../.github/CODEOWNERS) is the list of
maintainers, and a code owner's approval is required to merge. To add one,
append their `@username` to the `*` line and give them write access
(Settings → Collaborators). Never add a bot or an App.

**Sponsors.** [`.github/FUNDING.yml`](../.github/FUNDING.yml) shows the
Sponsor button on the repo (`github: MattyStacks`, GitHub Sponsors). Add
more platforms there if needed.

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

Versions are `MAJOR.MINOR.DATA.POST`, always four parts:
- MAJOR is a breaking data contract or API change.
- MINOR is any code change, features and fixes alike.
- DATA is newly published runs.
- POST is a new or materially updated blog post.

A release bumps the part for its biggest change and resets the parts to its
right, for example `1.1.0.3` becomes `1.1.1.0` when new runs ship. Tags are
`v1.1.0.0`. The post count comes from the content, not the version.

For a release:

1. Update `RELEASE_VERSION` in [`scripts/build.py`](../scripts/build.py), and
   `SCHEMA_VERSION` when the API payload changes.
2. Update current-version references, published counts, and feature summary
   in [README.md](../README.md) and this document (fixture counts are only in
   this document), and move `Unreleased` in
   [CHANGELOG.md](../CHANGELOG.md) under the new version heading.
3. Run the build, validation, compile checks, and `git diff --check`.
4. Do not commit `site/api/` unless repository policy changes.
5. After the pull request merges, create an annotated tag
   `v<RELEASE_VERSION>` on the merge commit (first line
   `vX.Y.Z.W: <short summary>`, then a short paragraph) and push it. Every
   release from v1.1.0.0 on has one; data-only submissions get none.
