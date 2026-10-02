
# Open GPU Benchmarks

Compare desktop, laptop, handheld, and integrated GPUs in one interactive graph.

The site is a static GitHub Pages dashboard. Benchmark source data lives in
`data/`, and the build script publishes browser-ready JSON to `site/api/`.

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
See docs/COPILOT_HANDOFF.md

## Parse PresentMon
python scripts/parse.py your.csv --gpu-id rog_ally_z1_extreme --game "Cyberpunk 2077" --form-factor handheld

Supports summary CSV from screenshot + detailed + MangoHud.

## License
MIT Code, CC0 Data
