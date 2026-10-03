
# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive graph.

The site is a static GitHub Pages dashboard. Benchmark source data lives in
`data/`, and the build script publishes browser-ready JSON to `site/api/`.

## Data flow

Official and community results stay separate from review through publication:

```text
data/official/**/summary.yaml              reviewed official summaries
data/community/pending/*.yaml              incoming community PR submissions
data/community/approved/*.yaml             approved community summaries
data/community/approved/raw/**             optional raw capture evidence
                    ↓
python scripts/build.py
                    ↓
site/api/v1/official.json                  official dashboard records
site/api/v1/community.json                 averaged community records
site/api/v1/dashboard.json                 combined dashboard dataset
```

Raw captures are retained in Git for reproducibility but are deliberately
excluded from the browser payload. Community summaries without raw captures
are accepted for review when they provide `proof.summary_source`; the site
labels them as **Summary only**. This initial `v0.1.0` dataset is synthetic
scaffolding and is visibly marked as such in the dashboard.

## Site
`site/index.html` is the dashboard entry point.

## Local development

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000>.

## GitHub Pages deployment

The workflow in `.github/workflows/build.yml` builds the data API and deploys
`site/` with the official GitHub Pages actions whenever `main` is updated.

After creating the repository:

1. Push this project to the repository's `main` branch.
2. In **Settings > Pages**, set **Source** to **GitHub Actions**.
3. Wait for the **Build and Deploy Open GPU Benchmarks** workflow to finish.

The site will be available at
`https://<github-user>.github.io/open-gpu-benchmarks/`.

## Quick Start
For the complete architecture and resume instructions, see
[docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md). Contributor setup and PR
requirements are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Parse PresentMon
python scripts/parse.py your.csv --gpu-id rog_ally_z1_extreme --game "Cyberpunk 2077" --form-factor handheld

Supports summary CSV from screenshot + detailed + MangoHud.

## Versioning

The repository uses Git tags for named public releases. `v0.1.0` is the first
synthetic, data-driven Pages scaffold. Each tagged commit versions the site,
source YAML, raw evidence, and build logic together.

## License
MIT Code, CC0 Data
