
"""
validate.py - PR validation, driver OPTIONAL
"""
import glob, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("pip install pyyaml"); sys.exit(1)

def load_yaml(p):
    with open(p) as f: return yaml.safe_load(f)

failed=False
pending=list(Path("data/community/pending").rglob("*.yaml"))
if not pending:
    print("No pending files")
    sys.exit(0)

for pf in pending:
    print(f"\nChecking {pf}")
    try:
        data=load_yaml(pf)
    except Exception as e:
        print(f"::error:: Invalid YAML {pf}: {e}"); failed=True; continue

    # Required
    for field in ["gpu_id","game","resolution","settings","results"]:
        if field not in data:
            print(f"::error:: {pf} missing {field}"); failed=True

    if "results" in data:
        if "avg_fps" not in data["results"] or "p1_low" not in data["results"]:
            print(f"::error:: {pf} needs results.avg_fps and p1_low"); failed=True
        avg=data["results"].get("avg_fps",0)
        p1=data["results"].get("p1_low",0)
        if p1>avg:
            print(f"::error:: p1_low {p1} > avg {avg} impossible"); failed=True

    # Driver OPTIONAL - only warn
    if not data.get("system",{}).get("driver"):
        print(f"::warning:: {pf} missing optional driver - OK, but encourage adding it")

    proof=data.get("proof",{})
    if not proof.get("raw_log"):
        if proof.get("summary_source"):
            print(f"::warning:: {pf} is a summary-only submission; raw proof is encouraged")
        else:
            print(f"::warning:: {pf} has no raw_log or summary_source proof reference")

print("\nValidation done" + (" - FAILED" if failed else " - PASSED"))
sys.exit(1 if failed else 0)
