# Submitting Cyberpunk 2077 benchmark runs

Cyberpunk 2077 has a built-in benchmark, and every run saves its results to
your computer. `scripts/import_cyberpunk.py` reads those results and writes the
result files for you. You don't have to type any numbers or copy files into the
repository; your benchmark folder stays where it is.

You can run the script again whenever you like. It remembers which runs it has
already turned into result files and only adds new ones, so you can benchmark a
few more presets later and run the same command again.

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
`benchmark_2026-10-13_18-44-57`, which holds a `summary.json`.

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
and create the virtual environment. Then activate it:

```powershell
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. Find your GPU's catalog ID

The ID is the file name of your card's entry under `data/gpus/`, for example
`rtx_5080_16gb_fe` for the GeForce RTX 5080 Founders Edition. Pick the exact
product you own, including the board partner. If your card isn't listed yet,
add it first (see [data/gpus/README.md](../data/gpus/README.md)).

## 4. Preview, then import

```powershell
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe
```

The dry run lists every run it found and what it would do with each one,
without writing anything. The second command writes one file per run to
`data/community/<gpu_id>/`, named after the run, for example
`result_20261013_cyberpunk_2077_184457.yaml`. It then checks the new files.

Useful options:

| Option | What it does |
|---|---|
| `--submitted-by <github-username>` | Shows your username with the runs. Leave it out to stay anonymous. |
| `--custom-preset High` | The name to use for every Custom-preset run, instead of answering a question for each one. |
| `--input <folder>` | The `benchmarkResults` folder, if the script can't find it. |
| `--os linux` | The OS the runs were on. It defaults to the OS you run the script on. |
| `--source official` | Maintainers only: writes to `data/official/`. |

The script looks for the benchmark folder here:

- **Windows:** `Documents\CD Projekt Red\Cyberpunk 2077\benchmarkResults`. It
  also finds a Documents folder that OneDrive has moved.
- **Linux (Steam with Proton):**
  `~/.local/share/Steam/steamapps/compatdata/1091500/pfx/drive_c/users/steamuser/Documents/CD Projekt Red/Cyberpunk 2077/benchmarkResults`.
  It checks `~/.steam/steam` and Flatpak Steam too. For other launchers, pass
  `--input`.

## 5. Review and open a pull request

Open a few of the new files and check the GPU, the resolution, and the preset.
Then run the checks and open a pull request as described in
[CONTRIBUTING.md](../CONTRIBUTING.md):

```powershell
python scripts/validate.py
```

## What gets recorded

Each file holds:

- **The run:** the game version, resolution, preset, and upscaler.
- **Performance:** average FPS, plus minimum and maximum FPS, the run time, and
  the frame count.
- **Your system:** CPU, system memory, GPU driver, OS, and display mode.

Everything comes from `summary.json`. The proof method is `in_game_benchmark`.

`summary.json` has no 1% low, so these runs have none. The checks print a
`result-no-p1-low` warning for each file, which is expected. If you want 1%
lows, capture the run with PresentMon instead, as described in
[COMMUNITY_SUBMISSIONS.md](COMMUNITY_SUBMISSIONS.md).

## Runs the script skips

| Reason | What to do |
|---|---|
| Frame generation was on | Run it again with frame generation off. |
| V-Sync or an FPS limit was on | Run it again uncapped. |
| A different GPU than `--gpu-id` | Import it with that GPU's ID. The script compares the GPU name and memory size in `summary.json` with the catalog entry. |
| Custom preset with upscaling on | Run it again on a named preset, or with upscaling off. |
| Custom preset with no name given | Run the script again and answer the question, or pass `--custom-preset`. |

Skipped runs aren't remembered, so once you fix the cause, running the script
again picks them up.
