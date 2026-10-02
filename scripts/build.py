
"""
build.py - summary.yaml first, fallback to raw/ scan
If summary.yaml exists, use it. If missing, scan raw/**/*.csv and generate it.
Outputs site/api/v1/*.json
"""
import glob, json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("pip install pyyaml"); sys.exit(1)

from collections import defaultdict

def load_yaml(p):
    with open(p) as f:
        return yaml.safe_load(f)

def main():
    gpus_path=Path("data/gpus.yaml")
    gpus=load_yaml(gpus_path) if gpus_path.exists() else []

    # Scan official: look for summary.yaml first
    official_runs=[]
    # Check for game subfolders
    for summary in Path("data/official").rglob("summary.yaml"):
        try:
            d=load_yaml(summary)
            game = d.get("game") or summary.parent.name
            runs = d.get("runs", [d])
            for r in runs:
                if "game" not in r:
                    r["game"]=game
                official_runs.append(r)
            print(f"Loaded summary: {summary} -> {len(runs)} runs")
        except Exception as e:
            print(f"Skip {summary}: {e}")

    # Fallback: if no summary found, scan raw/
    if not official_runs:
        print("No summary.yaml found, scanning raw/...")
        # TODO: call parse.py for each CSV in raw/
        # Placeholder for Copilot: implement raw scan
        pass

    # Community approved
    bucket=defaultdict(list)
    community_raw=[]
    for pf in Path("data/community/approved").rglob("*.yaml"):
        try:
            d=load_yaml(pf)
            community_raw.append(d)
            key=(d.get("gpu_id"), d.get("game"), d.get("resolution"), d.get("settings"))
            bucket[key].append(d)
        except Exception as e:
            print(f"Skip {pf}: {e}")

    community_avg=[]
    for key,runs in bucket.items():
        gpu_id,game,res,settings=key
        avgs=[r["results"]["avg_fps"] for r in runs if "results" in r]
        p1s=[r["results"]["p1_low"] for r in runs if "results" in r]
        if not avgs: continue
        community_avg.append({
            "gpu_id": gpu_id, "game": game, "resolution": res, "settings": settings,
            "run_count": len(runs),
            "avg_fps": round(sum(avgs)/len(avgs),2),
            "p1_low": round(sum(p1s)/len(p1s),2) if p1s else None
        })

    out_dir=Path("site/api/v1")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir/"gpus.json","w") as f: json.dump(gpus,f,indent=2)
    with open(out_dir/"benchmarks.json","w") as f: json.dump({"official": official_runs, "count": len(official_runs)},f,indent=2)
    with open(out_dir/"community.json","w") as f: json.dump({"averaged": community_avg, "raw": community_raw, "count": len(community_raw)},f,indent=2)

    print(f"GPUs: {len(gpus)} | Official: {len(official_runs)} | Community: {len(community_raw)} -> {out_dir}")

if __name__=="__main__":
    main()
