# TODO

The backlog: deferred work that's out of scope for current PRs. Pick items up
only when asked.

**Every PR keeps this file current.** Remove items you finished, move them to
[Recently completed](#recently-completed), and add anything you deferred,
found broken, or were asked to do later. This applies to people and to every
AI agent. The same rule is in `CLAUDE.md`, `AGENTS.md`, and
`.github/copilot-instructions.md`.

## Catalog plan (next steps, one PR each)

Details are in "Planned next steps" in
[COPILOT_HANDOFF.md](COPILOT_HANDOFF.md#planned-next-steps).

- [ ] **Step 4: Linux vs Windows.** This is the last step of the catalog plan.
  Everything a new session needs is below. Do it on a new branch from `main`
  as one PR, and follow the "every change updates the changelog and backlog"
  rule.

  **Decisions already made by the maintainer (don't revisit):**
  - **OS is a grouping key; the distro is not.** Windows and Linux runs of the
    same product, game, resolution, and preset are never averaged together.
    The distro, kernel, Proton, and other details are recorded on each run
    and shown in the run details, but they never create separate chart bars.
  - **Dashboard filter:** Windows and Linux chips, both on by default, built
    like the existing form-factor chips. Each bar gets an OS badge or label so
    a product appearing twice (once per OS) isn't confusing. There are no
    per-distro bars.
  - **Per-distro breakdowns are DIY.** Tell readers (JSON API panel,
    `README.md`, `docs/COMMUNITY_SUBMISSIONS.md`): to compare distros, kernels,
    or Proton versions, download `community.json`, `official.json`, or the
    per-product `summary.json` and chart it yourself. Every run carries the
    detail fields.
  - **Block-style YAML only,** like everything else.
  - **Deferred, not part of this step:** a Linux-vs-Windows percentage
    comparison view. It's already listed under Dashboard below.

  **Data contract (result files, under `system:`):**
  - **Required:** `os`, either `windows` or `linux`, lowercase.
  - **Optional, free text unless marked bool:**

    | Applies to | Fields |
    | ---------- | ------ |
    | both | `os_detail` (`Windows 11 Pro 24H2`, `SteamOS 3.6.19`), `os_build`, `driver` (exists today; `566.36` or `Mesa 24.2.3`), `resizable_bar` (bool), `graphics_api` (`DX12`, `Vulkan`) |
    | windows | `game_mode` (bool), `hags` (bool, hardware-accelerated GPU scheduling), `memory_integrity` (bool, VBS/HVCI), `power_plan` |
    | linux | `distro` (`SteamOS`, `Bazzite`, `CachyOS`), `distro_version`, `kernel`, `mesa`, `runtime` (`native`, `proton`, or `wine`), `proton` (`GE-Proton9-20`), `dxvk`, `vkd3d_proton`, `launcher` (`Steam`, `Heroic`, `Lutris`), `session` (`gamescope`, `KDE Wayland`, `X11`), `gamemode` (bool, Feral GameMode) |

  - **Field placement checks:** Linux-only fields on a `windows` run, or
    Windows-only fields on a `linux` run, should be an error. They're almost
    always a copy-paste mistake.
  - **Today's state:** no result fixture has an OS field yet. Free-text OS
    values appear only in these places, and all must be migrated:
    - `templates/community_submission.yaml` (`system.os: Windows 11`)
    - the `CONTRIBUTING.md` examples (`os: Windows 11`, `os: SteamOS 3.6`)
    - `scripts/parse.py`, which writes a top-level `os:` from
      `--os` (default `"Windows 11"`)

    Move the free text to `os_detail`, and set `os` to `windows` or `linux`.

  **Code changes:**
  - **`scripts/checks.py`,** in `check_result_file()` (game runs, official and
    community):
    - require `system.os` in `windows`/`linux`
    - type-check the detail fields (bools and text)
    - error on detail fields that don't match the OS

    New rule names, each needing a ``#### `rule-name` `` heading in
    `docs/COMMUNITY_SUBMISSIONS.md`; `check_rules_are_documented()` enforces
    this:
    - `result-os` (missing or invalid)
    - `result-os-field` (wrong type, or a field that doesn't fit the OS)

    Consider an unknown-`system`-field warning too.
  - **`scripts/build.py`:**
    - In `build_record()`, add `os` and every detail field to the run record.
      Keep the existing `driver`, `cpu`, `memory`, and `power_mode` handling.
    - In `aggregate_game_records()`, add `record["os"]` to the group key, and
      add the detail fields to the `implementations` keys list.
    - In `main()`, add `"os"` to `comparison_policy.group_by`.
    - Bump `SCHEMA_VERSION` (currently `0.9`, so `0.10`).
  - **`scripts/parse.py`:**
    - Replace the free-text `--os` with `--os {windows,linux}` and add an
      optional `--os-detail`.
    - Write them under `system:`, not at the top level.
    - When `--os` isn't given, default from the capture format: `mangohud`
      means `linux`, PresentMon means `windows`. Print the chosen value so the
      submitter can confirm it.
    - Known bug, separate backlog item: MangoHud parsing returns 0 FPS. Fixing
      it here is reasonable if it's small.
  - **`site/index.html`:**
    - In the `state`, add `oses: new Set(["windows", "linux"])`.
    - Render OS chips next to `#factor-filters` (copy `renderFactorFilters()`).
    - In `filteredRecords()`, add `.filter((record) => state.oses.has(record.os))`.
    - In `renderChart()`, label each bar with the OS when both OSes are
      present, for example `${gpu_name} · Linux`, or use a badge.
    - Add an OS column or badge in the table.
    - In `formatRunLine()`, show `os_detail`, `distro`, `kernel`, `mesa`,
      `proton`, and similar.
    - Add the "per-distro: use the JSON" note to the `#data-api` panel.
  - **Fixtures** (synthetic, safe to edit):
    - Steam Deck runs (official and community under `steam_deck_oled_16gb`)
      get `system.os: linux` and `distro: SteamOS`.
    - Every other result file gets `system.os: windows`.
    - Consider adding one synthetic Linux run for a product that also has a
      Windows run of the same game, resolution, and preset. That shows the
      split and gives the test something to check.

  **Tests** (`scripts/test_build.py`):
  - Negative cases in `check_result_rules()` for `result-os` (missing,
    `Windows` capitalized, `macos`) and `result-os-field` (`proton` on a
    windows run, `hags: "yes"`).
  - A check that a Windows and a Linux run of the same profile stay in
    separate summaries, and that the summary records carry `os`.
  - Update the hard-coded `dashboard.json` record count (currently 24) if
    fixtures add a run.
  - `check_templates_are_valid()` only covers catalog templates. Consider
    adding a check that `templates/community_submission.yaml` passes the
    result checks after its placeholder username is replaced.

  **Docs to update:**
  - `docs/COMMUNITY_SUBMISSIONS.md`: the OS fields table, the rule headings,
    and the per-distro JSON note.
  - `CONTRIBUTING.md`: examples, the required-fields table, and the
    common-mistakes table.
  - `data/community/README.md`, `README.md`, and `docs/COPILOT_HANDOFF.md`:
    the data contract, schema 0.10, and fixture counts.
  - `.github/copilot-instructions.md`, `CLAUDE.md`, and `AGENTS.md`: the OS
    rule.
  - `CHANGELOG.md` (under `Unreleased`) and this backlog: move step 4 to
    Recently completed.
- [ ] **Require `sources`.** Turn the `sources-missing` warning into an
  error once the maintainer has re-validated the current sources by hand.
- [ ] **Re-validate catalog sources by hand.** The current sources were added
  on 2026-10-08. TechPowerUp blocks scripts, so those URLs were confirmed by
  page title and their values through search results. Also find a source for
  the `z1_extreme` silicon specs (die size, transistors, shader counts), and
  for any value not yet listed in a `covers`.
- [ ] **Replace `_generic` laptop IDs** with real laptop models, then turn the
  `id-generic` warning into an error.

## Data and submissions

- [ ] **Permission-based third-party submissions.** Let a maintainer add
  benchmarks on behalf of someone else, such as a YouTube channel or another
  user who has given permission. Today `submitted_by` must be the GitHub user
  opening the PR, and the file name must end with that username. This needs:
  - a way to credit the original source: name, channel or profile URL, and a
    link to the video or post
  - a record that permission was given
  - check and file-name rules that allow the PR author and the credited source
    to differ
  - updated contributor docs: `CONTRIBUTING.md`,
    `docs/COMMUNITY_SUBMISSIONS.md`, and `data/community/README.md`
  - dashboard and API attribution for the credited source
- [ ] **Roll-up view by GPU model.** Group products that share a `base`
  reference, for example every RTX 5060 Ti 16 GB board, and compare boards
  of the same GPU side by side.

## Dashboard

- [ ] **Linux vs Windows comparison view.** Show the percentage difference per
  product and game wherever both OSes have results.
- [ ] **Per-GPU or per-vendor icons** in the table and chart labels. The site
  favicon shipped in v0.5.0.
- [ ] **Rename "Benchmark summaries".** The table is now a per-card spec and
  results table, so give the section a more meaningful heading.
- [ ] **Make the table search more noticeable.** Widen the search input so it
  stands out as the table grows.
- [ ] **Remove the six-GPU selection limit.** Let users pin more than six GPUs
  to the top of the chart and table.
- [ ] **Overlay avg FPS and 1% low in one bar.** Test rendering the two
  metrics as a single overlaid bar so the chart stays compact as the GPU list
  grows.

## Tooling and bugs

- [ ] **Fix MangoHud parsing in `parse.py`.** The frame-time reader skips the
  header with `readline()` and then builds a second `DictReader`, which treats
  the first data row as the header. MangoHud captures parse to 0 FPS.
- [ ] **Clear stale build output.** `build.py` never deletes old files under
  `site/api/v1/`. After an ID rename, a local preview still serves the old
  per-product `summary.json` files. CI is unaffected because it starts from a
  clean checkout. Fix: clear `OUTPUT_DIR` at the start of a successful build.
- [ ] **Changelog check in CI.** Fail or warn on a PR that changes `scripts/`,
  `site/`, `templates/`, or catalog rules without touching `CHANGELOG.md`.
- [ ] **Python virtual environment.**
  - Add a `.venv` setup and ignore it in `.gitignore`.
  - Document `python -m venv .venv` and activation in `README.md` and
    `CONTRIBUTING.md`.
  - Consider a `requirements.txt` for `pyyaml` and `numpy`, and use it in
    both CI workflows.
- [ ] **Branch protection** (manual repo setting): mark the three PR checks
  (Catalog entries, Benchmark results, Build and tests) as required on
  `main`.

## Recently completed

- **v0.5.0 (2026-10-08)**
  - Catalog plan step 1: per-product catalog files, product-level IDs, shared
    checks in `scripts/checks.py`, and three PR checks.
  - Catalog plan step 2: reference files with `base`, `platform`,
    `board_partner`, and `skus`.
  - Per-card dashboard spec table.
- **Unreleased**
  - Catalog plan step 3: `sources` on every catalog entry, `source-invalid`
    and `sources-missing` checks, and source links in the dashboard.
  - Site favicon.
  - `AGENTS.md`.
