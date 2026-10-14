"""
import_cyberpunk.py - Cyberpunk 2077 built-in benchmark runs -> result YAML

Every time the game's benchmark finishes, it saves a folder such as
benchmarkResults/benchmark_2026-10-13_18-44-57/ with a summary.json in it. This
script reads those summary.json files and writes one result file per run:

    data/<source>/<gpu_id>/result_20261013_cyberpunk_2077_184457.yaml

Nothing is copied from the game folder; the runs stay where they are. Run the
script again any time: runs that already have a result file are skipped, so only
new benchmarks are added. Full instructions: docs/CYBERPUNK_BENCHMARK.md

    python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe --dry-run
    python scripts/import_cyberpunk.py --gpu-id rtx_5080_16gb_fe

Runs with frame generation, V-Sync, or an FPS limit on are skipped, as are runs
from a different GPU than --gpu-id. A run on the Custom preset needs a preset
name (--custom-preset, or answer the prompt); a Custom run with upscaling on is
skipped, because only a named preset may turn upscaling on.
"""
import argparse
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

GAME = "Cyberpunk 2077"
GAME_SLUG = "cyberpunk_2077"
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
RESOLUTIONS = {(1920, 1080): "1080p", (2560, 1440): "1440p", (3840, 2160): "4K"}
# Upscaler quality indices, in the order of the game's menu. UserSettings.json
# confirms DLSS 0 = Auto and FSR 2.1 1 = Quality; the rest follow that order.
# Other upscalers' indices are written as "(mode N)" rather than guessed.
# Changing a label later splits dashboard groups, so only add confirmed ones.
QUALITY_MODES = {0: "Auto", 1: "Quality", 2: "Balanced", 3: "Performance", 4: "Ultra Performance"}
DLSS_MODES = QUALITY_MODES
FSR2_MODES = QUALITY_MODES
WINDOW_MODES = {1: "Borderless windowed", 2: "Fullscreen"}


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


def output_name(folder_name):
    year, month, day, hour, minute, second = RUN_FOLDER.match(folder_name).groups()
    return f"result_{year}{month}{day}_{GAME_SLUG}_{hour}{minute}{second}.yaml"


def already_imported(data_dir, name):
    """A run counts as imported once a result file with its name exists anywhere."""
    return any(any((data_dir / source).glob(f"*/{name}")) for source in checks.RESULT_SOURCES)


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


def build_system(data, os_name):
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
        system["memory"] = f"{round(data['systemMemory'] / 1024)} GB"
    if driver_version(data.get("gpuDriverVersion")):
        system["driver"] = driver_version(data.get("gpuDriverVersion"))
    system["graphics_api"] = "DX12"
    if data.get("windowMode") in WINDOW_MODES:
        system["display_mode"] = WINDOW_MODES[data["windowMode"]]
    return system


def build_run(data, gpu_id, preset, source, os_name, submitted_by):
    entry = {"resolution": resolution(data), "graphics_preset": preset}
    upscaling = upscaler(data)
    if upscaling:
        entry["upscaling"] = upscaling
        entry["preset_upscaling"] = True
    entry["avg_fps"] = round(float(data["averageFps"]), 2)
    for key, field in (("min_fps", "minFps"), ("max_fps", "maxFps"), ("duration", "time")):
        if checks.is_number(data.get(field)):
            entry[key] = round(float(data[field]), 2)
    if checks.is_number(data.get("frameNumber")):
        entry["frame_count"] = int(data["frameNumber"])

    run = {"gpu_id": gpu_id}
    if source == "community" and submitted_by:
        run["submitted_by"] = submitted_by
    run.update({"benchmark_type": "game", "game": GAME})
    if data.get("gameVersion"):
        run["version"] = str(data["gameVersion"])
    run["frame_generation"] = False
    run["result"] = [entry]
    run["system"] = build_system(data, os_name)
    run["proof"] = {"method": "in_game_benchmark", "format": "cyberpunk_summary_json"}
    return run


class IndentedDumper(yaml.SafeDumper):
    """Indent list items under their key, like the hand-written data files."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def write_run(path, run, folder):
    header = (
        f"# Imported by scripts/import_cyberpunk.py from {folder.name}/summary.json\n"
        "# (Cyberpunk 2077's built-in benchmark). Re-running the script skips this run.\n"
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
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported and write nothing")
    parser.add_argument("--data-dir", default=str(checks.DATA_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    catalog, _ = checks.load_catalog(data_dir)
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    gpu = catalog_by_id.get(args.gpu_id)
    if gpu is None:
        print(f"Unknown --gpu-id '{args.gpu_id}'. Catalog IDs:")
        for gpu_id in sorted(catalog_by_id):
            print(f"  {gpu_id}")
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
    rows, written, previously = [], [], 0
    for folder in sorted(path for path in input_dir.iterdir() if path.is_dir() and RUN_FOLDER.match(path.name)):
        name = output_name(folder.name)
        if already_imported(data_dir, name):
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

        run = build_run(data, args.gpu_id, preset, args.source, args.os, args.submitted_by)
        rows.append(("new", folder.name, res, preset, upscaling, fps, ""))
        if not args.dry_run:
            path = out_dir / name
            write_run(path, run, folder)
            written.append(path)

    headers = ("status", "run", "resolution", "preset", "upscaling", "avg fps", "note")
    if rows:
        widths = [max(len(str(row[i])) for row in (headers, *rows)) for i in range(len(headers) - 1)]
        for row in (headers, *rows):
            print("  ".join(str(value).ljust(width) for value, width in zip(row, widths)) + "  " + row[-1])
    new = sum(row[0] == "new" for row in rows)
    skipped = len(rows) - new
    verb = "would import" if args.dry_run else "imported"
    print(f"\n{new} {verb}, {skipped} skipped, {previously} already imported earlier")

    if not written:
        return 0
    catalog, catalog_issues = checks.load_catalog(data_dir)
    _, result_issues = checks.load_results(catalog, data_dir)
    mine = {checks.relative_path(path) for path in written}
    issues = checks.Issues(issue for issue in [*catalog_issues, *result_issues] if issue.path in mine)
    if issues.errors:
        checks.report(checks.Issues(issues.errors), "New result files")
        return 1
    print("The new files pass the checks. Review them, then run python scripts/validate.py and open a pull request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
