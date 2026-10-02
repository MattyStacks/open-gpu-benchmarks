
# Copilot Handoff - Open GPU Atlas (V4 Base)

## Current State
Dashboard v4 is keeper: chart at top, table at bottom, selected GPUs sort to top with neon glow, fixed bar width 20px, dark/light toggle.
NO isolate mode - removed per user request. Chart always shows all filtered GPUs.

## Final Behavior (V4)
- Filters: Game, Resolution, Form Factor [All, Desktop, Laptop, Handheld, iGPU] - multi-select chips
- Toggles: [x] Avg FPS, [x] 1% Low - actually hide/show series
- Table checkboxes: selecting moves GPU to top of chart + table
- Comparison card when 2+ selected: shows % difference for handheld vs laptop vs desktop
- Dark/light toggle persisted

## PresentMon Format (from screenshot)
Duration, Total Frames, Average FPS, Minimum FPS, 1st Percentile FPS, 5th Percentile FPS, Maximum FPS, AnimationErrorPerSecond, AnimationErrorPerFrame
Keep: avg + 1st percentile (p1_low) for chart. Store p5_low, duration, anim_error optionally.
Ignore for chart: min, max (outliers)

parse.py already handles all 3 formats.

## Folder Structure - Hybrid (User Decision)
```
/data/
  gpus.yaml (with form_factor)
  official/
    cyberpunk_2077/
      summary.yaml (source of truth)
      raw/
        rtx_4090/
          run1.csv (full dump)
        rog_ally/
          run1.csv
  community/
    pending/ (PRs land here)
    approved/
```
Build logic: summary.yaml first, if missing scan raw/ and generate.

## PR Workflow
Required: gpu_id, game, resolution, settings, results.avg_fps, results.p1_low, proof.raw_log
Optional (do NOT block): driver, os, p5_low, anim_error
Validation: p1 <= avg, delta vs official <15% warn <30% error

## Files Copilot Needs to Finish
- scripts/build.py - implement raw/ fallback scan
- site/ - migrate single HTML to Vite + React if needed, or keep HTML
- .github/workflows - already stubbed

Context window was 80% full, so starting fresh with this zip is recommended.
