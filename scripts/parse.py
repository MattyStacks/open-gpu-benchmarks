
"""
parse.py - Handles ALL PresentMon formats + MangoHud -> YAML
Supports:
1. PresentMon SUMMARY (your screenshot): Duration, Total Frames, Average FPS, Minimum FPS, 1st Percentile FPS, 5th Percentile FPS, Maximum FPS, AnimationErrorPerSecond
2. PresentMon DETAILED: MSBetweenPresents, Dropped
3. MangoHud: frametime

Driver is OPTIONAL for community PRs per your request.
form_factor supported: desktop, laptop, handheld, igpu
"""
import argparse, csv, sys
from datetime import datetime
from pathlib import Path
try:
    import yaml
except ImportError:
    print("pip install pyyaml"); sys.exit(1)

try:
    import numpy as np
    HAS_NUMPY=True
except ImportError:
    HAS_NUMPY=False

def percentile(data, p):
    if not data: return 0
    if HAS_NUMPY:
        return float(np.percentile(data, p))
    s=sorted(data)
    k=(len(s)-1)*(p/100)
    f=int(k); c=min(f+1,len(s)-1)
    return float(s[f] if f==c else s[f]*(c-k)+s[c]*(k-f))

def detect_and_load(path):
    with open(path, newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        headers = [h.strip() for h in (reader.fieldnames or [])]
        h_lower = [h.lower().strip() for h in headers]
        joined = " ".join(h_lower)

        # Format 1: SUMMARY - your screenshot
        if "average fps" in joined and "1st percentile" in joined:
            for row in reader:
                # handle case insensitive keys
                def get_key(target):
                    for h in headers:
                        if h.lower().strip() == target:
                            return row.get(h)
                    return None
                try:
                    avg = float(get_key("average fps"))
                    p1 = float(get_key("1st percentile fps"))
                    p5 = None
                    if "5th percentile fps" in joined:
                        try: p5 = float(get_key("5th percentile fps"))
                        except: pass
                    min_f = None
                    if "minimum fps" in joined:
                        try: min_f = float(get_key("minimum fps"))
                        except: pass
                    max_f = None
                    if "maximum fps" in joined:
                        try: max_f = float(get_key("maximum fps"))
                        except: pass
                    duration = None
                    if "duration" in joined:
                        try: duration = float(get_key("duration"))
                        except: pass
                    total_frames = 0
                    if "total frames" in joined:
                        try: total_frames = int(float(get_key("total frames")))
                        except: pass
                    anim = None
                    if "animationerrorpersecond" in joined:
                        try: anim = float(get_key("animationerrorpersecond"))
                        except: pass
                    return {
                        "format": "presentmon_summary",
                        "avg": avg, "p1": p1, "p5": p5, "min": min_f, "max": max_f,
                        "duration": duration, "anim_err": anim, "frame_count": total_frames
                    }
                except Exception as e:
                    raise ValueError(f"Failed to parse summary CSV: {e} Headers: {headers}")

        # Format 2: Detailed PresentMon
        if "msbetweenpresents" in joined:
            fps_vals=[]
            f.seek(0); f.readline()
            reader2 = csv.DictReader(f)
            ms_key = next((k for k in reader2.fieldnames if "msbetweenpresents" in k.lower()), None)
            drop_key = next((k for k in reader2.fieldnames if k.lower()=="dropped"), None)
            for row in reader2:
                try:
                    if drop_key and row.get(drop_key)=="1": continue
                    ms=float(row[ms_key])
                    if ms<=0 or ms>500: continue
                    fps_vals.append(1000.0/ms)
                except: continue
            return {
                "format": "presentmon_detailed",
                "avg": sum(fps_vals)/len(fps_vals) if fps_vals else 0,
                "p1": percentile(fps_vals,1),
                "p01": percentile(fps_vals,0.1),
                "frame_count": len(fps_vals)
            }

        # Format 3: MangoHud
        if "frametime" in joined:
            fps_vals=[]
            f.seek(0); f.readline()
            reader2 = csv.DictReader(f)
            ft_key = next((k for k in reader2.fieldnames if "frametime" in k.lower()), None)
            for row in reader2:
                try:
                    ms=float(row[ft_key])
                    if ms<=0 or ms>500: continue
                    fps_vals.append(1000.0/ms)
                except: continue
            return {
                "format": "mangohud",
                "avg": sum(fps_vals)/len(fps_vals) if fps_vals else 0,
                "p1": percentile(fps_vals,1),
                "p01": percentile(fps_vals,0.1),
                "frame_count": len(fps_vals)
            }
    raise ValueError(f"Unknown CSV format. Headers: {headers}")

def main():
    p=argparse.ArgumentParser(description="PresentMon/MangoHud -> YAML")
    p.add_argument("csv_file")
    p.add_argument("--gpu-id", required=True, help="Must exist in gpus.yaml")
    p.add_argument("--game", required=True)
    p.add_argument("--submitted-by", required=True, help="GitHub username of the PR submitter")
    p.add_argument("--resolution", default="1440p")
    p.add_argument("--graphics-preset", default="Ultra")
    p.add_argument("--form-factor", default="desktop", choices=["desktop","laptop","handheld","igpu"])
    p.add_argument("--driver", default="", help="OPTIONAL - not required for PR approval")
    p.add_argument("--os", default="Windows 11")
    p.add_argument("--output", default="")
    args=p.parse_args()

    csv_path=Path(args.csv_file)
    result=detect_and_load(csv_path)

    data={
        "gpu_id": args.gpu_id,
        "submitted_by": args.submitted_by,
        "benchmark_type": "game",
        "game": args.game,
        "form_factor": args.form_factor,
        "os": args.os,
        "capture_method": result["format"],
        "result": [{
            "avg_fps": round(float(result["avg"]),2),
            "p1_low": round(float(result["p1"]),2),
            "resolution": args.resolution,
            "graphics_preset": args.graphics_preset,
            "p5_low": round(float(result["p5"]),2) if result.get("p5") else None,
            "p01_low": round(float(result["p01"]),2) if result.get("p01") else None,
            "min_fps": round(float(result["min"]),2) if result.get("min") else None,
            "max_fps": round(float(result["max"]),2) if result.get("max") else None,
            "duration": result.get("duration"),
            "anim_error_per_sec": result.get("anim_err"),
            "frame_count": result.get("frame_count")
        }],
        "system": {"driver": args.driver} if args.driver else {},
        "overclock": {"is_oc": False, "power_limit_percent": 100},
        "proof": {"raw_log": str(csv_path.name), "format": result["format"]},
    }
    data["result"][0]={k:v for k,v in data["result"][0].items() if v is not None}

    if not args.output:
        safe_game=args.game.lower().replace(" ","_").replace(":","")
        date = datetime.now().strftime("%Y%m%d")
        handle = args.submitted_by.lower()
        folder = Path(f"data/community/{args.gpu_id}")
        out = folder / f"result_{date}_{safe_game}_{handle}.yaml"
        repeat = 2
        while out.exists():
            out = folder / f"result_{date}_{safe_game}_{repeat}_{handle}.yaml"
            repeat += 1
    else:
        out=Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out,"w") as f:
        yaml.safe_dump(data,f,sort_keys=False)
    print(f"Detected: {result['format']} | Avg: {result['avg']:.2f} | 1%: {result['p1']:.2f} -> {out}")

if __name__=="__main__":
    main()
