
"""Validate pending community benchmark submissions."""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUTLIER_RATIO = 0.5


def load_yaml(path):
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source) or {}


def official_records():
    records = []
    for path in sorted((ROOT / "data" / "official").rglob("summary.yaml")):
        summary = load_yaml(path)
        defaults = {
            "game": summary.get("game", path.parent.name.replace("_", " ").title()),
            "version": summary.get("version", ""),
        }
        for run in summary.get("runs", [summary]):
            results = run.get("results", run)
            system = run.get("system", {})
            records.append(
                {
                    "gpu_id": run.get("gpu_id"),
                    "game": run.get("game", defaults["game"]),
                    "resolution": run.get("resolution"),
                    "graphics_preset": run.get("graphics_preset"),
                    "form_factor": run.get("form_factor"),
                    "gpu_power_w": run.get(
                        "gpu_power_w",
                        run.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w"))),
                    ),
                    "avg_fps": results.get("avg_fps"),
                }
            )
    return records


def matching_official_baseline(data, baselines):
    system = data.get("system", {})
    power = data.get("gpu_power_w", data.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w"))))
    candidates = [
        record
        for record in baselines
        if all(
            (
                data.get(field)
                == record.get(field)
                or (field == "form_factor" and not data.get(field))
            )
            for field in ("gpu_id", "game", "resolution", "graphics_preset")
        )
        and (
            not data.get("form_factor")
            or record.get("form_factor") is None
            or data["form_factor"].lower() == str(record.get("form_factor", "")).lower()
        )
        and (power is None or record.get("gpu_power_w") in (None, power))
        and record.get("avg_fps") is not None
    ]
    if not candidates:
        return None
    return sum(float(record["avg_fps"]) for record in candidates) / len(candidates)


failed = False
pending = list((ROOT / "data" / "community" / "pending").rglob("*.yaml"))
if not pending:
    print("No pending files")
    sys.exit(0)

baselines = official_records()
for pf in pending:
    print(f"\nChecking {pf}")
    try:
        data=load_yaml(pf)
    except Exception as e:
        print(f"::error:: Invalid YAML {pf}: {e}"); failed=True; continue

    for field in ["gpu_id","game","resolution","graphics_preset","results"]:
        if field not in data:
            print(f"::error:: {pf} missing {field}"); failed=True

    if "results" in data:
        if "avg_fps" not in data["results"] or "p1_low" not in data["results"]:
            print(f"::error:: {pf} needs results.avg_fps and p1_low"); failed=True
        avg = data["results"].get("avg_fps", 0)
        p1 = data["results"].get("p1_low", 0)
        if p1>avg:
            print(f"::error:: p1_low {p1} > avg {avg} impossible"); failed=True

    if data.get("frame_generation", False):
        print(f"::error:: {pf} must disable frame generation for comparable runs")
        failed = True

    if str(data.get("form_factor", "")).lower() == "laptop":
        system = data.get("system", {})
        if data.get("gpu_power_w", data.get("tgp_w", system.get("gpu_power_w", system.get("tgp_w")))) is None:
            print(f"::warning:: {pf} is a laptop submission without TGP; add it when discoverable")

    if not data.get("system",{}).get("driver"):
        print(f"::warning:: {pf} missing optional driver - OK, but encourage adding it")

    proof=data.get("proof",{})
    if not proof.get("raw_log"):
        if proof.get("summary_source"):
            print(f"::warning:: {pf} is a summary-only submission; raw proof is encouraged")
        else:
            print(f"::warning:: {pf} has no raw_log or summary_source proof reference")

    baseline = matching_official_baseline(data, baselines)
    avg = data.get("results", {}).get("avg_fps")
    if baseline and avg:
        difference = abs(float(avg) - baseline) / baseline
        if difference > OUTLIER_RATIO:
            print(
                f"::error:: {pf} avg_fps {avg} differs {difference:.0%} from "
                f"matching official baseline {baseline:.1f}; correct, explain the "
                "profile difference, or remove the entry"
            )
            failed = True
    elif not baseline:
        print("::warning:: no matching official baseline found; maintainer review is required")

print("\nValidation done" + (" - FAILED" if failed else " - PASSED"))
sys.exit(1 if failed else 0)
