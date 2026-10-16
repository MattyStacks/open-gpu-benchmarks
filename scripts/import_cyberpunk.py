"""
import_cyberpunk.py - Cyberpunk 2077 built-in benchmark runs -> result YAML

Every time the game's benchmark finishes, it saves a folder such as
benchmarkResults/benchmark_2026-10-13_18-44-57/ with a summary.json and a
frames.csv in it. This script reads the settings from summary.json and the
average FPS and 1% low from the frame times in frames.csv. frames.csv is
optional: without it a run gets summary.json's average and no 1% low, which the
checks note as info, never a warning or a failure. It writes the runs from
one day into one result file, one item in its result list per run:

    data/<source>/<gpu_id>/result_20261013_cyberpunk_2077.yaml

Each item's benchmark_run names the run folder it came from. Nothing is copied
from the game folder; the runs stay where they are. Run the script again any
time: runs already listed in a result file are skipped, and new runs from the
same day are added to that day's file, and runs already listed without a
p1_low get one from their frames.csv. A run with a different setup (game
version, driver, CPU, memory, or OS) goes in its own file, _2, _3, ..., because
those fields apply to the whole file. That includes --memory-type and
--memory-channels: pass the same ones every time, or new runs start a _2 file.
Full instructions: docs/CYBERPUNK_BENCHMARK.md

    python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
    python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe
    python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --memory-type DDR5-6400 --memory-channels 2

Runs with frame generation, V-Sync, or an FPS limit on are skipped, as are runs
from a different GPU than --gpu-id. A run on the Custom preset needs a preset
name (--custom-preset, or answer the prompt); a Custom run with upscaling on is
skipped, because only a named preset may turn upscaling on.
"""
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install -r requirements.txt"); sys.exit(1)

import checks
from parse import percentile

# The game's ID in data/games.yaml; result files are named after it too.
GAME_ID = "cyberpunk_2077"
STEAM_APP_ID = "1091500"
RESULTS_SUBPATH = Path("CD Projekt Red") / "Cyberpunk 2077" / "benchmarkResults"
RUN_FOLDER = re.compile(r"^benchmark_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})$")

# summary.json presetName -> the name the game shows in its settings menu.
PRESETS = {
    "Low": "Low",
    "Medium": "Medium",
    "High": "High",
    "Ultra": "Ultra",
    "Steam Deck": "Steam Deck",
    "RayTracingLow": "Ray Tracing: Low",
    "RayTracingMedium": "Ray Tracing: Medium",
    "RayTracingUltra": "Ray Tracing: Ultra",
    "RayTracingOverdrive": "Ray Tracing: Overdrive",
}
CUSTOM_PRESET = "Custom"
# windowMode, confirmed for 2 against UserSettings.json. It can change between
# runs, so it goes on each result item rather than under system.
WINDOW_MODES = {0: "Windowed", 1: "Borderless windowed", 2: "Fullscreen"}
# Each result item names its run folder here; that is how re-runs skip it.
RUN_KEY = "benchmark_run"
PROOF_FORMAT = "cyberpunk_summary_json"
FRAMES_FILE = "frames.csv"
FRAME_TIME_COLUMN = "frame time (ms)"
# frames.csv is ignored when its average is further than this from summary.json's.
FRAMES_AVG_TOLERANCE = 0.01
# File-level fields: runs share a file only when all of these match.
SETUP_KEYS = ("gpu_id", "submitted_by", "game_id", "version", "system", "proof")
RESOLUTIONS = {(1920, 1080): "1080p", (2560, 1440): "1440p", (3840, 2160): "4K"}
# Upscaler quality indices, in the order of the game's menu. UserSettings.json
# confirms DLSS 0 = Auto and FSR 2.1 1 = Quality; the rest follow that order.
# Other upscalers' indices are written as "(mode N)" rather than guessed.
# Changing a label later splits dashboard groups, so only add confirmed ones.
QUALITY_MODES = {0: "Auto", 1: "Quality", 2: "Balanced", 3: "Performance", 4: "Ultra Performance"}
DLSS_MODES = QUALITY_MODES
FSR2_MODES = QUALITY_MODES


def default_input_dirs():
    """Where the game saves benchmarkResults on this computer, most likely first."""
    home = Path.home()
    candidates = []
    if sys.platform == "win32":
        documents = windows_documents_dir()
        if documents:
            candidates.append(documents)
        candidates += [home / "Documents", home / "OneDrive" / "Documents"]
        return [folder / RESULTS_SUBPATH for folder in candidates]
    # Linux with Steam's Proton: the game writes into its Wine prefix.
    prefix = Path("steamapps") / "compatdata" / STEAM_APP_ID / "pfx" / "drive_c" / "users" / "steamuser" / "Documents"
    steam_roots = [
        home / ".steam" / "steam",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
    ]
    return [root / prefix / RESULTS_SUBPATH for root in steam_roots]


def windows_documents_dir():
    """The real Documents folder, which OneDrive or a user can move."""
    try:
        import ctypes
        from ctypes import wintypes
        from uuid import UUID

        class GUID(ctypes.Structure):
            _fields_ = [("data", ctypes.c_ubyte * 16)]

        folder_id = GUID()
        folder_id.data[:] = UUID("{FDD39AD0-238F-46AF-ADB4-6C85480369C7}").bytes_le  # FOLDERID_Documents
        path = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(path)) != 0:
            return None
        try:
            return Path(path.value)
        finally:
            ctypes.windll.ole32.CoTaskMemFree(path)
    except (AttributeError, OSError, ValueError):
        return None


def find_input_dir(given):
    if given:
        folder = Path(given).expanduser()
        if not folder.is_dir():
            sys.exit(f"--input folder not found: {folder}")
        return folder
    for folder in default_input_dirs():
        if folder.is_dir():
            return folder
    tried = "\n  ".join(str(folder) for folder in default_input_dirs())
    sys.exit(f"Couldn't find Cyberpunk 2077's benchmarkResults folder. Tried:\n  {tried}\nPass it with --input.")


def run_date(folder_name):
    """A run folder's day as 'YYYY-MM-DD', the result file's date field."""
    return "-".join(RUN_FOLDER.match(folder_name).groups()[:3])


def run_time(folder_name):
    """A run folder's local time as 'HH:MM:SS'; the game records no time zone."""
    return ":".join(RUN_FOLDER.match(folder_name).groups()[3:])


def load_run(path):
    try:
        run = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return run if isinstance(run, dict) else None


def imported_runs(data_dir):
    """Every benchmark_run already listed in a result file, so re-runs skip them."""
    seen = set()
    for source in checks.RESULT_SOURCES:
        for path in checks.result_paths(data_dir, source):
            entries = (load_run(path) or {}).get("result")
            if isinstance(entries, list):
                seen.update(entry[RUN_KEY] for entry in entries if isinstance(entry, dict) and entry.get(RUN_KEY))
    return seen


def same_setup(run, other):
    """Runs share a file only when every file-level field matches."""
    return all(run.get(key) == other.get(key) for key in SETUP_KEYS)


def target_file(out_dir, date, run, planned):
    """The day's file with the same setup, or the next free name for a new one."""
    repeat = 1
    while True:
        suffix = "" if repeat == 1 else f"_{repeat}"
        path = out_dir / f"result_{date.replace('-', '')}_{GAME_ID}{suffix}.yaml"
        if path not in planned and path.exists():
            existing = load_run(path)
            if existing is not None and isinstance(existing.get("result"), list):
                planned[path] = existing
        if path not in planned and not path.exists():
            planned[path] = {**run, "result": []}
            return path
        if path in planned and same_setup(planned[path], run):
            return path
        repeat += 1


def mode_label(modes, index):
    return modes.get(index, f"(mode {index})")


def upscaler(data):
    """The upscaler a run used, or "" when it rendered at native resolution."""
    if data.get("DLAAEnabled"):
        return "DLAA"
    if data.get("DLSSEnabled"):
        return f"DLSS {mode_label(DLSS_MODES, data.get('DLSSQuality'))}"
    if data.get("FSR4Enabled"):
        return f"FSR 4 {mode_label({}, data.get('FSR4Quality'))}"
    if data.get("FSR3Enabled"):
        return f"FSR 3 {mode_label({}, data.get('FSR3Quality'))}"
    if data.get("FSR2Enabled"):
        return f"FSR 2.1 {mode_label(FSR2_MODES, data.get('FSR2Quality'))}"
    if data.get("XeSSEnabled"):
        return f"XeSS {mode_label({}, data.get('XeSSQuality'))}"
    if data.get("FSREnabled"):
        return f"FSR 1.0 {mode_label({}, data.get('FSRQuality'))}"
    if data.get("DRSEnabled"):
        return "Dynamic resolution"
    return ""


def frame_generation_on(data):
    # DLSSMultiFrameGenEnabled is only the saved x2/x3/x4 choice; it stays true
    # while frame generation itself is off, so it isn't checked here.
    return bool(
        data.get("frameGenerationType")
        or data.get("DLSSFrameGenEnabled")
        or data.get("FSR3FrameGenEnabled")
        or data.get("XeSSFrameGenEnabled")
    )


def model_tokens(gpu_id):
    """The model part of a catalog ID: rtx_5080_16gb_fe -> 'rtx 5080'."""
    tokens = []
    for token in gpu_id.split("_"):
        if checks.MEMORY_TOKEN.match(token):
            break
        tokens.append(token)
    return " ".join(tokens)


def gpu_mismatch(data, gpu):
    """Why this run doesn't look like it came from the catalog GPU, or None."""
    name = " ".join(re.sub(r"[^a-z0-9]+", " ", str(data.get("gpuName", "")).lower()).split())
    model = model_tokens(gpu["id"])
    if model not in name or ("laptop" in name) != ("laptop" in model):
        return f"GPU is '{data.get('gpuName')}', not {gpu['id']}"
    capacity = checks.spec(gpu, "memory", "capacity_gb")
    memory_mb = data.get("gpuMemory")
    if not checks.spec(gpu, "memory", "shared") and checks.is_number(memory_mb) and capacity:
        if round(memory_mb / 1024) != capacity:
            return f"GPU has {memory_mb / 1024:.1f} GB, but {gpu['id']} has {capacity} GB"
    return None


def resolution(data):
    size = (data.get("renderWidth"), data.get("renderHeight"))
    return RESOLUTIONS.get(size, f"{size[0]}x{size[1]}")


def driver_version(raw):
    """'Nvidia v 61714 [r617_07]' -> '617.14'; other formats are kept as written."""
    match = re.match(r"nvidia v\s*(\d{4,})", str(raw or ""), re.IGNORECASE)
    if match:
        digits = match.group(1)
        return f"{digits[:-2]}.{digits[-2:]}"
    return str(raw or "").strip()


def linux_os_detail():
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


def build_system(data, os_name, memory_type="", memory_channels=None):
    system = {"os": os_name}
    if os_name == "windows":
        # Under Proton the game reports a Windows version, so these are Windows-only.
        if data.get("osName"):
            system["os_detail"] = str(data["osName"])
        if data.get("osVersion"):
            system["os_build"] = str(data["osVersion"])
    elif linux_os_detail():
        system["os_detail"] = linux_os_detail()
    if data.get("cpuName"):
        system["cpu"] = str(data["cpuName"]).strip()
    if checks.is_number(data.get("systemMemory")):
        system["memory_gb"] = round(data["systemMemory"] / 1024)
    # summary.json has the size only; the type and channels come from the options.
    if memory_type:
        system["memory_type"] = memory_type
    if memory_channels:
        system["memory_channels"] = memory_channels
    if driver_version(data.get("gpuDriverVersion")):
        system["driver"] = driver_version(data.get("gpuDriverVersion"))
    system["graphics_api"] = "DX12"
    return system


def read_frame_times(folder):
    """Frame times in ms from a run's frames.csv, or None when it can't be read."""
    try:
        with open(folder / FRAMES_FILE, newline="", encoding="utf-8") as file:
            rows = csv.reader(file)
            header = [cell.strip().lower() for cell in next(rows)]
            column = header.index(FRAME_TIME_COLUMN)
            times = [float(row[column]) for row in rows if len(row) > column and row[column].strip()]
    except (OSError, StopIteration, ValueError, UnicodeDecodeError):
        return None
    return times if times and all(ms > 0 for ms in times) else None


def frame_stats(folder, data):
    """(avg_fps, p1_low) from frames.csv, or None when it's missing or doesn't
    match summary.json (a different frame count or average)."""
    times = read_frame_times(folder)
    if times is None:
        return None
    avg = 1000 * len(times) / sum(times)
    if checks.is_number(data.get("frameNumber")) and len(times) != int(data["frameNumber"]):
        return None
    expected = data.get("averageFps")
    if checks.is_number(expected) and abs(avg - float(expected)) > FRAMES_AVG_TOLERANCE * float(expected):
        return None
    p1 = percentile([1000 / ms for ms in times], 1)
    return round(avg, 2), round(p1, 2)


def build_entry(data, preset, folder_name, stats):
    """One result list item for one benchmark run."""
    entry = {RUN_KEY: folder_name, "time": run_time(folder_name), "resolution": resolution(data), "graphics_preset": preset}
    upscaling = upscaler(data)
    if upscaling:
        entry["upscaling"] = upscaling
        entry["preset_upscaling"] = True
    if stats:
        entry["avg_fps"], entry["p1_low"] = stats
    else:
        entry["avg_fps"] = round(float(data["averageFps"]), 2)
    for key, field in (("min_fps", "minFps"), ("max_fps", "maxFps"), ("duration", "time")):
        if checks.is_number(data.get(field)):
            entry[key] = round(float(data[field]), 2)
    if checks.is_number(data.get("frameNumber")):
        entry["frame_count"] = int(data["frameNumber"])
    if data.get("windowMode") in WINDOW_MODES:
        entry["display_mode"] = WINDOW_MODES[data["windowMode"]]
    return entry


def build_run(data, gpu_id, source, os_name, submitted_by, date, memory_type="", memory_channels=None):
    """The file-level fields shared by every run in one result file."""
    run = {"gpu_id": gpu_id}
    if source == "community" and submitted_by:
        run["submitted_by"] = submitted_by
    run.update({"benchmark_type": "game", "game_id": GAME_ID, "date": date})
    if data.get("gameVersion"):
        run["version"] = str(data["gameVersion"])
    run["frame_generation"] = False
    run["result"] = []
    run["system"] = build_system(data, os_name, memory_type, memory_channels)
    run["proof"] = {"method": "in_game_benchmark", "format": PROOF_FORMAT}
    return run


class IndentedDumper(yaml.SafeDumper):
    """Indent list items under their key, like the hand-written data files."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def add_p1_lows(out_dir, input_dir, planned):
    """Give runs already in out_dir's files a p1_low (and the frames.csv
    average) when they have none and their frames.csv is still in input_dir.
    Changed files are added to planned. Returns status rows and the files."""
    rows, changed = [], []
    for path in sorted(out_dir.glob(f"result_*_{GAME_ID}*.yaml")):
        run = load_run(path)
        if run is None or not isinstance(run.get("result"), list):
            continue
        for index, entry in enumerate(run["result"]):
            folder_name = entry.get(RUN_KEY) if isinstance(entry, dict) else None
            if not folder_name or entry.get("p1_low") is not None or not RUN_FOLDER.match(str(folder_name)):
                continue
            folder = input_dir / folder_name
            if not folder.is_dir():
                continue
            try:
                data = json.loads((folder / "summary.json").read_text(encoding="utf-8"))["Data"]
            except (OSError, ValueError, KeyError, TypeError):
                data = {}
            stats = frame_stats(folder, data)
            shown = (entry.get("resolution", ""), entry.get("graphics_preset", ""), entry.get("upscaling", ""))
            if stats is None:
                # A deleted frames.csv is normal and stays quiet; one that doesn't match is worth a look.
                if (folder / FRAMES_FILE).exists():
                    rows.append(("no p1_low", folder_name, *shown, str(entry.get("avg_fps", "")), f"{FRAMES_FILE} doesn't match summary.json"))
                continue
            items = []
            for key, value in entry.items():
                if key == "avg_fps":
                    items += [("avg_fps", stats[0]), ("p1_low", stats[1])]
                else:
                    items.append((key, value))
            run["result"][index] = dict(items)
            rows.append(("updated", folder_name, *shown, f"{stats[0]:.1f}", f"{path.name}: p1_low {stats[1]}"))
            if path not in changed:
                changed.append(path)
        if path in changed:
            planned[path] = run
    return rows, changed


def with_key_after(mapping, key, value, after):
    """A copy of mapping with key set, placed after the key named by after."""
    items = [(name, item) for name, item in mapping.items() if name != key]
    at = next((i + 1 for i, (name, _) in enumerate(items) if name == after), len(items))
    return dict([*items[:at], (key, value), *items[at:]])


def upgrade_files(out_dir, planned):
    """Bring files from older imports up to date: game becomes game_id, each
    file gets its date (from the file name), each run its time (from its run
    folder), and system.memory ('64 GB') becomes memory_gb (64). Changed files
    are added to planned. Returns the changed files."""
    changed = []
    for path in sorted(out_dir.glob(f"result_*_{GAME_ID}*.yaml")):
        named = checks.RESULT_FILE_DATE.match(path.stem)
        run = planned.get(path) or load_run(path)
        if not named or run is None or not isinstance(run.get("result"), list):
            continue
        before = repr(run)
        if "game" in run:
            run = {("game_id" if key == "game" else key): (GAME_ID if key == "game" else value) for key, value in run.items()}
        system = run.get("system")
        if isinstance(system, dict) and "memory" in system and checks.memory_gb_from_text(system["memory"]):
            size = checks.memory_gb_from_text(system["memory"])
            run["system"] = {("memory_gb" if key == "memory" else key): (size if key == "memory" else value) for key, value in system.items()}
        if run.get("date") is None:
            run = with_key_after(run, "date", "-".join(named.groups()), "game_id")
        for index, entry in enumerate(run["result"]):
            folder_name = entry.get(RUN_KEY) if isinstance(entry, dict) else None
            if folder_name and entry.get("time") is None and RUN_FOLDER.match(str(folder_name)):
                run["result"][index] = with_key_after(entry, "time", run_time(folder_name), RUN_KEY)
        if repr(run) != before:
            planned[path] = run
            changed.append(path)
    return changed


def write_run(path, run):
    header = (
        "# Imported by scripts/import_cyberpunk.py from Cyberpunk 2077's built-in\n"
        "# benchmark. Each benchmark_run is a folder in the game's benchmarkResults;\n"
        "# re-running the script skips runs listed here and adds new ones.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.dump(run, Dumper=IndentedDumper, sort_keys=False, default_flow_style=False, allow_unicode=True)
    path.write_text(header + text, encoding="utf-8")


def ask_custom_preset(folder, data, last):
    default = f" (Enter for '{last}')" if last else ""
    print(
        f"\n{folder.name} used the Custom preset at {resolution(data)} with upscaling off.\n"
        f"Which preset did you start from? For example High, if you only turned upscaling off.{default}"
    )
    answer = input("Preset name, or 's' to skip this run: ").strip()
    if answer.lower() == "s":
        return None
    return answer or last or None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Turn Cyberpunk 2077 built-in benchmark runs (summary.json) into result YAML. "
        "See docs/CYBERPUNK_BENCHMARK.md.",
    )
    parser.add_argument("--gpu-id", required=True, help="Exact catalog ID of the GPU you tested, the file name under data/gpus/<form_factor>/<gpu_vendor>/")
    parser.add_argument("--input", default="", help="The benchmarkResults folder; found automatically when left out")
    parser.add_argument("--source", default="community", choices=checks.RESULT_SOURCES, help="community (default) or official (maintainer runs)")
    parser.add_argument("--submitted-by", default="", help="OPTIONAL - your GitHub username for community runs; leave it out to stay anonymous")
    parser.add_argument("--custom-preset", default="", help="Preset name for every Custom-preset run, for example High when you only turned upscaling off")
    parser.add_argument("--os", default="linux" if sys.platform.startswith("linux") else "windows", choices=checks.RESULT_OSES, help="Defaults to the OS this script runs on")
    parser.add_argument("--memory-type", default="", help="OPTIONAL - your RAM's type and speed, for example DDR5-6400")
    parser.add_argument("--memory-channels", type=int, default=None, help="OPTIONAL - RAM channels in use: 1 single, 2 dual, 4 quad, 8 on some servers")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported and write nothing")
    parser.add_argument("--data-dir", default=str(checks.DATA_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    if GAME_ID not in {game["id"] for game in checks.load_games(data_dir)[0]}:
        print(f"'{GAME_ID}' is missing from data/games.yaml; add it back (id, name, type, year) before importing.")
        return 1
    catalog, _ = checks.load_catalog(data_dir)
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    gpu = catalog_by_id.get(args.gpu_id)
    if gpu is None:
        print(f"Unknown --gpu-id '{args.gpu_id}'. Catalog IDs:")
        for gpu_id in sorted(catalog_by_id):
            print(f"  {gpu_id}")
        return 1
    if args.memory_channels is not None and not 1 <= args.memory_channels <= checks.MAX_MEMORY_CHANNELS:
        print(f"--memory-channels must be a whole number from 1 to {checks.MAX_MEMORY_CHANNELS}")
        return 1
    if args.submitted_by and not checks.GITHUB_USER_PATTERN.match(args.submitted_by):
        print(f"--submitted-by '{args.submitted_by}' isn't a valid GitHub username")
        return 1

    input_dir = find_input_dir(args.input)
    out_dir = data_dir / args.source / args.gpu_id
    print(f"Reading {input_dir}")
    print(f"Writing {checks.relative_path(out_dir)}/" + (" (dry run, nothing is written)" if args.dry_run else ""))

    custom_preset = args.custom_preset.strip()
    can_ask = not args.dry_run and not custom_preset and sys.stdin.isatty()
    last_custom = ""
    previously = 0
    seen = imported_runs(data_dir)
    planned, added = {}, {}
    rows, updated = add_p1_lows(out_dir, input_dir, planned) if out_dir.is_dir() else ([], [])
    dated = upgrade_files(out_dir, planned) if out_dir.is_dir() else []
    for folder in sorted(path for path in input_dir.iterdir() if path.is_dir() and RUN_FOLDER.match(path.name)):
        if folder.name in seen:
            previously += 1
            continue
        summary = folder / "summary.json"
        try:
            data = json.loads(summary.read_text(encoding="utf-8"))["Data"]
            float(data["averageFps"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            rows.append(("skipped", folder.name, "", "", "", "", f"unreadable summary.json ({error.__class__.__name__})"))
            continue

        res, upscaling, fps = resolution(data), upscaler(data), f"{float(data['averageFps']):.1f}"
        preset_key = str(data.get("presetName", ""))

        def skip(reason, preset=preset_key):
            rows.append(("skipped", folder.name, res, preset, upscaling, fps, reason))

        if frame_generation_on(data):
            skip("frame generation was on"); continue
        if data.get("verticalSync") or (checks.is_number(data.get("fpsClamp")) and data["fpsClamp"] > 0):
            skip("V-Sync or an FPS limit was on"); continue
        mismatch = gpu_mismatch(data, gpu)
        if mismatch:
            skip(f"{mismatch}; import it with that GPU's --gpu-id"); continue
        if preset_key == CUSTOM_PRESET:
            if upscaling:
                skip("Custom preset with upscaling on; re-run with upscaling off or on a named preset"); continue
            preset = custom_preset
            if not preset and can_ask:
                preset = ask_custom_preset(folder, data, last_custom) or ""
                last_custom = preset or last_custom
            if not preset:
                skip("Custom preset needs a name; pass --custom-preset (for example High)"); continue
        elif preset_key in PRESETS:
            preset = PRESETS[preset_key]
        else:
            skip(f"unknown preset '{preset_key}'"); continue

        date = run_date(folder.name)
        run = build_run(data, args.gpu_id, args.source, args.os, args.submitted_by, date, args.memory_type.strip(), args.memory_channels)
        path = target_file(out_dir, date, run, planned)
        stats = frame_stats(folder, data)
        planned[path]["result"].append(build_entry(data, preset, folder.name, stats))
        added[path] = added.get(path, 0) + 1
        note = "" if stats else f" (no usable {FRAMES_FILE}, so no 1% low)"
        rows.append(("new", folder.name, res, preset, upscaling, fps, path.name + note))

    headers = ("status", "run", "resolution", "preset", "upscaling", "avg fps", "file or reason")
    if rows:
        widths = [max(len(str(row[i])) for row in (headers, *rows)) for i in range(len(headers) - 1)]
        for row in (headers, *rows):
            print("  ".join(str(value).ljust(width) for value, width in zip(row, widths)) + "  " + row[-1])
    new = sum(row[0] == "new" for row in rows)
    filled = sum(row[0] == "updated" for row in rows)
    skipped = sum(row[0] == "skipped" for row in rows)
    verb = "would import" if args.dry_run else "imported"
    print(f"\n{new} {verb}, {skipped} skipped, {previously} already imported earlier")
    if filled:
        print(f"{filled} earlier run(s) {'would get' if args.dry_run else 'got'} a p1_low from {FRAMES_FILE}")
    if dated:
        print(f"{len(dated)} earlier file(s) {'would be' if args.dry_run else 'were'} upgraded (game_id, date, run times, and memory_gb)")
    for path, count in added.items():
        total = len(planned[path]["result"])
        print(f"  {checks.relative_path(path)}: {count} new, {total} in the file")

    written = list(dict.fromkeys([*updated, *dated, *added]))
    if args.dry_run or not written:
        return 0
    for path in written:
        write_run(path, planned[path])
    catalog, catalog_issues = checks.load_catalog(data_dir)
    games, _ = checks.load_games(data_dir)
    _, result_issues = checks.load_results(catalog, data_dir, games)
    mine = {checks.relative_path(path) for path in written}
    issues = checks.Issues(issue for issue in [*catalog_issues, *result_issues] if issue.path in mine)
    if issues.errors:
        checks.report(checks.Issues(issues.errors), "Written result files")
        return 1
    print("The written files pass the checks. Review them, then run python scripts/validate.py and open a pull request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
