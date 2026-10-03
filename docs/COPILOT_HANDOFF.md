# Open GPU Benchmarks - Project Handoff

This document is the current source of truth for picking up the project on
another computer or in another coding session.

## Project identity

- Repository: `MattyStacks/open-gpu-benchmarks`
- Local project folder used previously: `C:\Users\matt\repos\open-gpu-benchmarks`
- Default branch: `main`
- Public site: <https://mattystacks.github.io/open-gpu-benchmarks/>
- Public dashboard data: <https://mattystacks.github.io/open-gpu-benchmarks/api/v1/dashboard.json>
- First release tag: `v0.1.0`
- Release commit: `8c9922f`
- Latest `main` commit: `7dcd85e` (this handoff)

The repository is already connected to:

```text
https://github.com/MattyStacks/open-gpu-benchmarks.git
```

The working tree was clean at the time this handoff was written.

## Current product state

The site is a static GitHub Pages dashboard named **Open GPU Benchmarks**.
The current data is intentionally synthetic scaffolding. The page visibly
warns users that the data is not published benchmark evidence yet.

The dashboard preserves the original visual direction and interactions:

- dark/light theme toggle, persisted in local storage;
- game selector;
- resolution selector;
- All / Official / Community source filters;
- Desktop / Laptop / Handheld / iGPU form-factor filters;
- Avg FPS and 1% Low metric toggles;
- GPU search;
- table checkboxes that pin selected GPUs to the top;
- up to six selected GPUs;
- selected comparison summary;
- chart and table loaded from generated JSON rather than hard-coded benchmark rows;
- evidence label for `Raw log` versus `Summary only`.

The frontend is deliberately a single static `site/index.html` file. It is
not a Vite, React, or npm project at this time. ECharts is loaded from the
jsDelivr CDN.

## Data flow

```text
data/gpus.yaml
data/official/**/summary.yaml
data/community/pending/*.yaml
data/community/approved/*.yaml
data/community/approved/raw/**          optional raw captures
                 |
                 v
python scripts/build.py
                 |
                 v
site/api/v1/gpus.json
site/api/v1/official.json
site/api/v1/community.json
site/api/v1/dashboard.json
                 |
                 v
site/index.html fetches ./api/v1/dashboard.json
                 |
                 v
GitHub Pages publishes the entire site/ directory
```

`site/api/` is generated and ignored by Git. It is created locally by the
build script and recreated by GitHub Actions on every Pages deployment.

The browser payload contains summary metrics only. Raw CSV/frame-time files
are retained in Git for reproducibility but are not downloaded by every site
visitor.

## Official versus community data

Official and public/community results are intentionally separate:

- `data/official/<game>/summary.yaml`
  - curated official benchmark summaries;
  - one file may contain multiple `runs`;
  - source is published to `official.json`.
- `data/community/pending/*.yaml`
  - incoming contributor submissions;
  - validated by the pull-request workflow.
- `data/community/approved/*.yaml`
  - approved public submissions;
  - published as averaged records in `community.json`;
  - also included in the combined `dashboard.json`.
- `data/community/approved/raw/**`
  - optional approved raw benchmark captures;
  - use `proof.raw_log` as a relative reference.

Community submissions can provide either:

```yaml
proof:
  raw_log: raw/rog_ally_z1_extreme/cyberpunk_1440p.csv
```

or, when raw data is unavailable:

```yaml
proof:
  summary_source: Screenshot or manually recorded benchmark summary
```

Raw evidence is encouraged. Summary-only records are accepted by the current
scaffold and are labeled **Summary only** in the dashboard.

## Build and validation

Install the only Python dependencies:

```powershell
python -m pip install pyyaml numpy
```

Build generated API files:

```powershell
python scripts/build.py
```

Validate pending community YAML:

```powershell
python scripts/validate.py
```

Run the local Pages-style preview. Use a local HTTP server rather than opening
`index.html` directly so `fetch("./api/v1/dashboard.json")` works:

```powershell
python -m http.server 8000 --directory site
```

Open <http://localhost:8000/>.

Useful checks:

```powershell
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

## Versioning and deployment

Git commits version all source YAML, raw evidence, build logic, workflows,
documentation, and the dashboard together. Git tags identify named releases.

- `v0.1.0` is the first synthetic data-driven dashboard release.
- Do not create `index-v1.html` or similar files.
- Keep `site/index.html` as the stable entry point.

The workflow is [.github/workflows/build.yml](../.github/workflows/build.yml).
It:

1. checks out `main`;
2. installs Python 3.11, PyYAML, and NumPy;
3. runs `scripts/build.py`;
4. uploads `site/` as the Pages artifact;
5. deploys it with the official Pages deployment action.

Repository Pages must use **Settings > Pages > Source: GitHub Actions**.
Do not select a branch folder. The published root is the contents of `site/`,
so `site/index.html` becomes the public site root.

The current GitHub Pages URL is:

```text
https://mattystacks.github.io/open-gpu-benchmarks/
```

If a browser shows the old README after a deployment, check Pages source mode
first, then force refresh or use a temporary query string to bypass CDN/browser
cache.

## Existing synthetic fixtures

The current synthetic dataset includes four games:

- Alan Wake 2
- Baldur's Gate 3
- Cyberpunk 2077
- Helldivers 2

The build currently produces:

- 11 GPU catalog entries;
- 12 official records;
- 8 approved community summary records;
- 20 combined dashboard records.

All current fixture records contain `synthetic: true`. Replace or remove that
marker when real reviewed data is introduced.

## Current limitations

These are known, intentional next steps:

1. `scripts/build.py` reads prepared YAML summaries. Its old raw CSV fallback
   is not implemented.
2. `scripts/parse.py` converts PresentMon/MangoHud CSV data into community YAML,
   but it does not automatically add files to an approved raw-capture folder.
3. Validation checks required fields and `p1_low <= avg_fps`, but does not yet
   compare community results against official results.
4. The frontend currently loads one combined dashboard JSON file. If the
   dataset grows significantly, add a manifest plus per-game files.
5. The ECharts CDN dependency is external. Consider pinning/self-hosting it if
   offline or supply-chain resilience becomes important.
6. The current frontend is hand-maintained static JavaScript. Introduce a
   build tool only when the dashboard complexity justifies it.

## Recommended next work

1. Decide and document the final official benchmark methodology.
2. Replace synthetic official fixtures with reviewed real summaries.
3. Add real raw captures under the approved raw-data folders where available.
4. Tighten the community schema and PR review rules.
5. Add official-vs-community comparison warnings.
6. Split generated dashboard data by game if payload size becomes noticeable.
7. Add metadata such as source commit, generation time, and methodology version
   to the visible UI and release notes.

## Resume checklist

On another computer:

```powershell
git clone https://github.com/MattyStacks/open-gpu-benchmarks.git
Set-Location open-gpu-benchmarks
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

Then open <http://localhost:8000/> and read this file before changing the data
schema or deployment workflow.
