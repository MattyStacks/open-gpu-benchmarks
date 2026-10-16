# Submitting Cyberpunk 2077 benchmark runs

Cyberpunk 2077 has a built-in benchmark, and every run saves its results to
your computer. [`scripts/import_cyberpunk.py`](../scripts/import_cyberpunk.py)
reads those results and writes the result files for you. You don't type any
numbers or copy any files into the repository; your benchmark folder stays
where it is.

You can run the script again whenever you like. It remembers which runs it has
already imported and only adds new ones, so you can benchmark a few more
presets later and run the same command again.

**Quick start**, once the repository is set up (steps 2 and 3):

```powershell
python scripts/import_cyberpunk.py --gpu-id <your_gpu_id> --dry-run   # preview
python scripts/import_cyberpunk.py --gpu-id <your_gpu_id>             # write the files
python scripts/validate.py                                            # check everything
```

## Contents

1. [Run the benchmark](#1-run-the-benchmark)
2. [Set up the repository (once)](#2-set-up-the-repository-once)
3. [Find your GPU's catalog ID](#3-find-your-gpus-catalog-id)
4. [Preview, then import](#4-preview-then-import)
5. [Review and open a pull request](#5-review-and-open-a-pull-request)
6. [Running it again later](#running-it-again-later)
7. [Command reference](#command-reference)
8. [The result file](#the-result-file)
9. [How settings are named](#how-settings-are-named)
10. [Runs the script skips](#runs-the-script-skips)
11. [Troubleshooting](#troubleshooting)
12. [For maintainers](#for-maintainers)

## 1. Run the benchmark

1. In Cyberpunk 2077, open **Settings > Graphics** and pick a **Quick Preset**,
   such as Ultra or Ray Tracing: Ultra, and a resolution.
2. Turn **Frame Generation** off (DLSS, FSR, or XeSS). Runs with frame
   generation on can't be compared, so the script skips them.
3. Turn **V-Sync** off, and turn off any **Maximum FPS** limit. The script also
   skips capped runs.
4. From the main menu, choose **Run Benchmark** and let it finish.
5. Repeat for every preset and resolution you want to share.

Every run is saved as its own folder, such as
`benchmark_2026-10-13_18-44-57`, which holds a `summary.json` and a
`frames.csv`. The script reads the settings from `summary.json` and the
average FPS and 1% low from the frame times in `frames.csv`.

### Presets and upscaling

Cyberpunk's presets turn an upscaler on by themselves. For example, the Ray
Tracing presets use DLSS on NVIDIA cards. That's fine: the script records the
upscaler with the run, and upscaled runs are never averaged with native ones.

If you change any setting after picking a preset, the game calls it
**Custom**. The script can't tell what a Custom preset contains, so you name it.
To benchmark a preset at native resolution, pick the preset, turn only the
upscaler off, and give the preset's name, such as `High`, when the script asks.
A Custom run with an upscaler still on is skipped. Use a named preset for those.

## 2. Set up the repository (once)

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) to fork and clone the repository
and create the virtual environment. The script needs Python 3.11 or newer and
the packages in `requirements.txt`. Activate the environment in every new
terminal:

```powershell
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the commands below from the repository's top folder.

## 3. Find your GPU's catalog ID

The ID is the file name of your card's entry under `data/gpus/`, for example
`rtx_5080_16gb_fe` for the GeForce RTX 5080 Founders Edition. Pick the exact
product you own, including the board partner. If your card isn't listed yet,
add it first (see [data/gpus/README.md](../data/gpus/README.md)). An unknown ID
makes the script list every catalog ID and stop.

## 4. Preview, then import

```powershell
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
```

The dry run reads every run, shows what it would do with each one, and writes
nothing. Each row says `new` with the file the run would go into, or `skipped`
with the reason:

```text
status   run                            resolution  preset              upscaling         avg fps  file or reason
new      benchmark_2026-10-13_18-44-57  4K          Ray Tracing: Ultra  DLSS Auto         88.5     result_20261013_cyberpunk_2077.yaml
new      benchmark_2026-10-13_18-50-40  4K          Steam Deck          FSR 2.1 Balanced  165.6    result_20261013_cyberpunk_2077.yaml
skipped  benchmark_2026-10-13_20-12-15  1080p       Custom              FSR 2.1 Quality   189.6    Custom preset with upscaling on; re-run with upscaling off or on a named preset
new      benchmark_2026-10-13_20-21-40  4K          High                                  91.5     result_20261013_cyberpunk_2077.yaml

3 would import, 1 skipped, 0 already imported earlier
```

When it looks right, run it again without `--dry-run`:

```powershell
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe
```

`summary.json` records how much RAM you have, but not its type, speed, or
channel mode. Give those with two options:

```powershell
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --memory-type DDR5-6000 --memory-channels 2
```

`--memory-type` is the type and speed, such as `DDR5-6000`. `--memory-channels`
is a whole number: 1 for single channel, 2 for dual, 4 for quad. If you leave
either one out, the script records the default, `DDR5-6000` or `2` (dual
channel), and prints a warning:

```text
WARNING: --memory-type was not given, so runs are recorded as DDR5-6000.
WARNING: --memory-channels was not given, so runs are recorded as 2 (dual channel).
  If that isn't your RAM, re-run with --memory-type and --memory-channels,
  or fix memory_type and memory_channels under system: in the files before you submit them.
```

If the defaults aren't right for your PC, pass the options, or edit
`memory_type` and `memory_channels` in the files before you open a pull
request. Use the same values every time you import on that PC. They go under
`system:`, so a run with different values starts a separate `_2` file.

This writes the runs to `data/community/<gpu_id>/`, one file per day with one
`result` item per run, for example
`data/community/rtx_5080_16gb_fe/result_20261013_cyberpunk_2077.yaml`. It then
runs the checks on the files it wrote and prints any errors.

If a run used the Custom preset and you didn't pass `--custom-preset`, the
script asks for the preset's name, one run at a time. Press Enter to reuse your
previous answer, or type `s` to skip that run.

## 5. Review and open a pull request

Open the new file and check the GPU, the resolutions, and the presets. Then run
the checks and open a pull request as described in
[CONTRIBUTING.md](../CONTRIBUTING.md):

```powershell
python scripts/validate.py
```

Runs imported without a `frames.csv` show one `result-no-p1-low` info note
per file; that's expected and isn't a warning (see
[The result file](#the-result-file)). Errors must be fixed before the pull
request can be merged.

## Running it again later

Run the same command again whenever you've benchmarked more:

- Runs that are already in a result file are skipped. The script finds them by
  each result item's `benchmark_run`, which names the run's folder.
- New runs from a day that already has a file are added to that file.
- Runs from a new day go in a new file for that day.
- Files imported before `date` and `time` existed get them filled in from the
  file name and run folder names.
- Files imported before the game registry, which say `game: Cyberpunk 2077`,
  are rewritten to `game_id: cyberpunk_2077`.
- Files from older imports with `memory: 64 GB` are rewritten to
  `memory_gb: 64`.
- Runs after a driver or game update, or on a different CPU, memory amount,
  `--memory-type`, `--memory-channels`, or OS, go in a separate file for the same day: `..._2.yaml`, `..._3.yaml`. The
  game version and everything under `system:` apply to every run in a file,
  so runs that differ there can't share one.
- Skipped runs aren't remembered. Fix the cause (or answer the Custom preset
  question) and run the script again to pick them up.

When the script adds runs to an existing file, it rewrites the whole file, so
any comments you added to it by hand are lost. The runs and values are kept.

## Command reference

```text
python scripts/import_cyberpunk.py --gpu-id <id> [options]
```

| Option | What it does |
|---|---|
| `--gpu-id <id>` | **Required.** The catalog ID of the GPU that ran the benchmarks. Runs from a different GPU are skipped. |
| `--dry-run` | Shows what would be imported and writes nothing. |
| `--custom-preset <name>` | The preset name to use for every Custom-preset run, for example `High`, instead of being asked for each one. |
| `--submitted-by <github-username>` | Shows your GitHub username with the runs. Leave it out to stay anonymous. Community runs only. |
| `--input <folder>` | The `benchmarkResults` folder, if the script can't find it on its own. |
| `--os windows` or `--os linux` | The OS the benchmarks ran on. It defaults to the OS you run the script on. |
| `--source community` or `--source official` | Where the files go. `community` (`data/community/`) is the default; `official` (`data/official/`) is for maintainers. |
| `-h`, `--help` | Shows the options. |

The script looks for the benchmark folder here, in order:

- **Windows:** `Documents\CD Projekt Red\Cyberpunk 2077\benchmarkResults`,
  using Windows' own Documents location, so a Documents folder moved by
  OneDrive is found too. Then `%USERPROFILE%\Documents` and
  `%USERPROFILE%\OneDrive\Documents`.
- **Linux (Steam with Proton):** the game's Proton prefix,
  `steamapps/compatdata/1091500/pfx/drive_c/users/steamuser/Documents/CD Projekt Red/Cyberpunk 2077/benchmarkResults`,
  under `~/.steam/steam`, `~/.local/share/Steam`, and Flatpak Steam
  (`~/.var/app/com.valvesoftware.Steam/.local/share/Steam`). For other
  launchers, such as Heroic, pass `--input`.

The script exits with code 0 when it finishes (even if it skipped runs) and 1
when the benchmark folder can't be found, the GPU ID or username is wrong, or
the files it wrote fail the checks.

## The result file

This is the start of a file the script wrote; the full file has one `result`
item per run:

```yaml
# Imported by scripts/import_cyberpunk.py from Cyberpunk 2077's built-in
# benchmark. Each benchmark_run is a folder in the game's benchmarkResults;
# re-running the script skips runs listed here and adds new ones.
gpu_id: rtx_5080_16gb_fe
benchmark_type: game
game_id: cyberpunk_2077
date: '2026-10-13'
version: '2.31'
frame_generation: false
result:
  - benchmark_run: benchmark_2026-10-13_18-44-57
    time: '18:44:57'
    resolution: 4K
    graphics_preset: 'Ray Tracing: Ultra'
    upscaling: DLSS Auto
    preset_upscaling: true
    avg_fps: 88.52
    p1_low: 76.51
    min_fps: 79.67
    max_fps: 99.79
    duration: 64.25
    frame_count: 5687
    display_mode: Borderless windowed
system:
  os: windows
  os_detail: Windows 11 Pro
  os_build: 10.0.26300
  cpu: AMD Ryzen 9 9950X3D 16-Core Processor
  memory_gb: 64
  memory_type: DDR5-6000
  memory_channels: 2
  driver: '617.14'
  graphics_api: DX12
proof:
  method: in_game_benchmark
  format: cyberpunk_summary_json
```

Where each value comes from in the run folder (`summary.json` unless noted):

| Field | From | Notes |
|---|---|---|
| `game_id` | | Always `cyberpunk_2077`, its ID in `data/games.yaml`. The script stops if that entry is missing. |
| `date` | the run folder's name | The day of the runs; the same as the file name. |
| `version` | `gameVersion` | Same for every run in the file. |
| `result[].benchmark_run` | the run's folder name | How re-runs recognize imported runs. Don't edit it. |
| `result[].time` | the run folder's name | Your PC's local time when the run started; the game records no time zone. |
| `result[].resolution` | `renderWidth` x `renderHeight` | See [How settings are named](#how-settings-are-named). |
| `result[].graphics_preset` | `presetName` | The in-game name, or your name for a Custom preset. |
| `result[].upscaling`, `preset_upscaling` | the upscaler settings | Only when the preset turned an upscaler on. |
| `result[].avg_fps` | `frames.csv` | Frames divided by total frame time, rounded to two decimals; the same as `averageFps`. This is the number the dashboard charts. |
| `result[].p1_low` | `frames.csv` | The 1% low: the 1st percentile of per-frame FPS, the same way PresentMon and MangoHud captures are measured. |
| `result[].min_fps`, `max_fps` | `minFps`, `maxFps` | Extra detail; not charted. |
| `result[].duration`, `frame_count` | `time`, `frameNumber` | Seconds and frames rendered. |
| `result[].display_mode` | `windowMode` | Per run, because it can change between runs. |
| `system.os` | `--os` | `windows` or `linux`. |
| `system.os_detail`, `os_build` | `osName`, `osVersion` | Windows only. On Linux, `os_detail` comes from `/etc/os-release`, because Proton reports a Windows version. |
| `system.cpu` | `cpuName` | |
| `system.memory_gb` | `systemMemory` | Converted from MB to a whole number of GB, for example `64`. |
| `system.memory_type` | `--memory-type` | For example `DDR5-6000`, the default when the option is left out (with a warning). The game doesn't report it. |
| `system.memory_channels` | `--memory-channels` | A whole number: 1 single, 2 dual, 4 quad. Defaults to `2` with a warning. |
| `system.driver` | `gpuDriverVersion` | NVIDIA's `Nvidia v 61714 [r617_07]` becomes `617.14`; other drivers are kept as written. |
| `system.graphics_api` | | Always `DX12`, the game's only API. |
| `proof.method` | | Always `in_game_benchmark`. |

`summary.json` has no 1% low, so the script works out the average and the 1%
low from `frames.csv`, which lists every frame's time. It uses `frames.csv`
only when its frame count matches `frameNumber` and its average is within 1%
of `averageFps`. When it's missing or doesn't match, the run gets
`summary.json`'s average and no 1% low. That's fine: the import still works,
the dashboard charts the average, and the checks print one `result-no-p1-low`
info note for the file, never a warning or an error. You don't need to keep
`frames.csv` files, but keeping them gives your runs a 1% low.

Runs imported before the script read `frames.csv` get their 1% low the next
time you run it, as long as their folders are still in `benchmarkResults`.
They show as `updated` in the table, and their `avg_fps` may move by 0.01.

Nothing else from your computer is recorded: no user name, computer name, or
file paths.

## How settings are named

The dashboard only averages runs whose GPU, resolution, preset, upscaler, and
OS match exactly, so the script always writes the same names.

**Resolution:** 1920x1080 is `1080p`, 2560x1440 is `1440p`, and 3840x2160 is
`4K`. Any other size is written as width x height, such as `3440x1440`.

**Preset:** the name the game shows in its menu.

| `presetName` in summary.json | Written as |
|---|---|
| `Low`, `Medium`, `High`, `Ultra` | the same |
| `Steam Deck` | `Steam Deck` |
| `RayTracingLow` | `Ray Tracing: Low` |
| `RayTracingMedium` | `Ray Tracing: Medium` |
| `RayTracingUltra` | `Ray Tracing: Ultra` |
| `RayTracingOverdrive` | `Ray Tracing: Overdrive` |
| `Custom` | the name you give (`--custom-preset` or the prompt) |

**Upscaler:** the upscaler, then its quality mode: `DLSS Auto`,
`DLSS Quality`, `FSR 2.1 Quality`, `FSR 2.1 Balanced`, and so on. DLSS and FSR
2.1 use the game's menu order: Auto, Quality, Balanced, Performance, Ultra
Performance. FSR 3, FSR 4, XeSS, and FSR 1.0 are written with the game's mode
number, such as `XeSS (mode 2)`, until their names are confirmed. DLAA and
dynamic resolution are written as `DLAA` and `Dynamic resolution`.

**Display mode:** `windowMode` 0 is `Windowed`, 1 is `Borderless windowed`, and
2 is `Fullscreen`. Any other value is left out.

## Runs the script skips

| Reason shown | What to do |
|---|---|
| `frame generation was on` | Run it again with frame generation off. |
| `V-Sync or an FPS limit was on` | Run it again uncapped. |
| `GPU is '...', not <id>` or `GPU has ... GB, but <id> has ... GB` | The run came from a different GPU. Import it with that GPU's `--gpu-id`. The script compares the GPU name and memory size in `summary.json` with the catalog entry. |
| `Custom preset with upscaling on` | Run it again on a named preset, or with upscaling off. |
| `Custom preset needs a name` | Run the script again and answer the question, or pass `--custom-preset`. |
| `unknown preset '...'` | A preset the script doesn't know yet, perhaps from a game update. Open an issue with the name. |
| `unreadable summary.json` | The run didn't finish or the file is damaged. Run the benchmark again. |

## Troubleshooting

**"Couldn't find Cyberpunk 2077's benchmarkResults folder"**: the script lists
every place it looked. Find the folder yourself (it's next to the game's save
games, under `CD Projekt Red\Cyberpunk 2077`) and pass it with `--input`.

**"Unknown --gpu-id"**: the script lists the catalog IDs. Use one exactly as
listed, or add your card to the catalog first.

**"isn't a valid GitHub username"**: check `--submitted-by`, or leave it out to
stay anonymous.

**"0 imported, ... already imported earlier"**: every run is already in a
result file. Benchmark something new first.

**The checks fail on the new file**: the script prints each error with a link
to the rule. Fix the cause, delete the new file, and run the script again; it
recreates the file from your benchmark folder.

**Wrong preset name for a Custom run**: edit `graphics_preset` in the file, or
delete the file and import again with the right `--custom-preset`.

## For maintainers

- Official runs: add `--source official` to write to `data/official/`.
- The code is in [`scripts/import_cyberpunk.py`](../scripts/import_cyberpunk.py).
  The preset, upscaler, and display mode names are the `PRESETS`,
  `QUALITY_MODES`, and `WINDOW_MODES` tables at the top. Changing a name
  splits dashboard groups, so update existing result files in the same pull
  request.
- `SETUP_KEYS` lists the file-level fields that must match for runs to share a
  file.
- `check_import_cyberpunk()` in [`scripts/test_build.py`](../scripts/test_build.py)
  imports synthetic runs into a temporary folder. It covers the field mapping,
  skips, appending same-day runs, the `_2` file after a driver change, and
  display mode per run. The hidden `--data-dir` option points the script at
  that folder.
- Design notes are in [COPILOT_HANDOFF.md](COPILOT_HANDOFF.md); open questions
  (unconfirmed mode names) are in
  [TODO.md](TODO.md).
