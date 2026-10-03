# Contributing to Open GPU Benchmarks

## Local setup

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000/> to preview the dashboard.

## Adding benchmark data

Community submissions begin in `data/community/pending/` and are reviewed
through a pull request. Use
[templates/community_submission.yaml](templates/community_submission.yaml) as
the starting point.

Required fields currently include:

- `gpu_id`
- `game`
- `resolution`
- `settings`
- `results.avg_fps`
- `results.p1_low`

Raw benchmark captures are strongly encouraged. Keep approved captures under
`data/community/approved/raw/` and reference them with `proof.raw_log`.
Summary-only submissions are allowed when raw data is unavailable, but they
must provide `proof.summary_source` and are labeled accordingly on the site.

Do not place raw capture files in the browser-facing `site/api/` directory.
That directory is generated and ignored by Git.

## Before opening a pull request

```powershell
python scripts/build.py
python scripts/validate.py
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

The Pages workflow rebuilds generated API files from the YAML source. Do not
commit generated `site/api/` output unless the repository policy changes.

See [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md) for the full architecture,
deployment details, current release state, and known limitations.
