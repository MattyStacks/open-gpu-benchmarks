# Contributing to Open GPU Benchmarks

## Local setup

```powershell
python -m pip install pyyaml numpy
python scripts/build.py
python scripts/validate.py
python scripts/test_build.py
python -m http.server 8000 --directory site
```

Open <http://localhost:8000/> to preview the dashboard.

## Adding benchmark data

`data/gpus.yaml` owns the accepted GPU IDs. Add each run under the matching
source and GPU folder:

```text
data/official/<gpu_id>/result_YYYYMMDD_<benchmark>.yaml
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
```

Use [templates/community_submission.yaml](templates/community_submission.yaml)
for community runs or [templates/official_result.yaml](templates/official_result.yaml)
for official runs. The parent folder and `gpu_id` must match exactly.

Every community file sets `submitted_by` to the GitHub username of the person
opening the pull request, and the file name ends with that username
(compared case-insensitively; lowercase is conventional). For a second file
with the same date and game, add a number before the username, such as
`result_20261003_cyberpunk_2_mattystacks.yaml`.

Game records require `game` and a non-empty `result` list. Each list entry
requires `resolution`, `graphics_preset`, `avg_fps`, and `p1_low`; frame
generation must be disabled.

The leading `-` is required YAML syntax for separate list entries. It is what
allows one source file to include multiple resolution/preset profiles without
duplicating a `result` key, which YAML would overwrite. The validator checks
every entry independently, and the build aggregates only entries that match on
GPU, form factor, known power profile, game, resolution, and graphics preset.
Matching entries from the same file or different files are averaged together;
different profiles remain separate dashboard rows.

Use `benchmark_type` for future card-specific result categories; those retain
their `result` entries in the GPU API but are not shown in the game-FPS
dashboard until support is added.

Include exact machine details whenever known: device or board name, GPU
power/TGP, overclock status, CPU, memory, power mode, display/MUX mode,
driver, and operating system. Desktop and laptop GPUs never share a group.

Raw captures are strongly encouraged. Keep them under the same GPU folder,
such as `data/community/rtx_4090/raw/capture.csv`, and use a relative
`proof.raw_log` reference. Summary-only submissions need
`proof.summary_source` and are labeled on the site.

## Before opening a pull request

Add a line under `Unreleased` in [CHANGELOG.md](CHANGELOG.md) for any change to
behavior, the data contract, the dashboard, or this workflow. Data-only
submissions can skip it.

```powershell
python scripts/build.py
python scripts/validate.py
python scripts/test_build.py
python -m py_compile scripts\build.py scripts\validate.py scripts\parse.py
git diff --check
```

The Pages workflow regenerates `site/api/` from YAML source. Do not commit the
generated files unless repository policy changes. See
[docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md) for detailed
review rules.
