# Community benchmark submissions

Community source data is organized by catalog GPU. Find the exact ID in
[`data/gpus.yaml`](../data/gpus.yaml), then add one result file to its folder:

```text
data/community/<gpu_id>/result_YYYYMMDD_<contributor>.yaml
```

For example:

```text
data/community/rtx_4090/result_20261003_matty.yaml
```

The folder name and `gpu_id` in the YAML must match. On a merged pull request,
the build includes that run in
`site/api/v1/community/<gpu_id>/summary.json` and in the GPU-rooted master
API. There is no separate approved or pending source tree.

## Comparable game runs

Game records use `benchmark_type: game` (the default when omitted) and require:

- `game`;
- a non-empty `result` list, where every entry has `resolution`,
  `graphics_preset`, `avg_fps`, and `p1_low`;
- `frame_generation: false`.

`result` is a YAML list, so every profile must start with `-`. The dash is
required: YAML would overwrite duplicate `result:` keys rather than retain two
profiles. This shape allows one captured machine run to submit multiple
resolution/preset combinations:

```yaml
gpu_id: arc_a770
game: Helldivers 2
benchmark_type: game
result:
  - resolution: 1080p
    graphics_preset: Ultra
    avg_fps: 72.0
    p1_low: 52.0
  - resolution: 1440p
    graphics_preset: Ultra
    avg_fps: 60.0
    p1_low: 42.3
```

The validator checks every list entry for required profile fields, impossible
FPS values, disabled frame generation, and a matching official-baseline
outlier. The build expands each entry into an independent run, then groups
only matching GPU identity and form factor, known laptop TGP/GPU power, game,
resolution, and `graphics_preset`. Matching entries from multiple files are
averaged; different profiles remain separate. Game version remains exact-run
metadata rather than a grouping key. Desktop and laptop GPUs never share a
group.

## Machine details and evidence

Include device or board name, GPU power, overclock status, CPU, memory, power
mode, display/MUX mode, driver, and operating system whenever known.

PresentMon or another raw capture is strongly preferred. Put optional evidence
under the same GPU folder, for example:

```text
data/community/rtx_4090/raw/cyberpunk_1440p.csv
```

Reference it with `proof.raw_log: raw/cyberpunk_1440p.csv`. Summary-only
submissions must provide `proof.summary_source`; the dashboard labels them
accordingly. Raw captures remain in Git but outside browser-facing JSON.

## Review and validation

The validator checks every `result_*.yaml` and `result_*.yml` community file
and every `result` list entry. It verifies folder/catalog identity, list
shape, comparable game settings, frame-generation status, and impossible FPS
values. When a matching official baseline exists, a community average more
than 50% different is a validation error. Correct it, explain a materially
different profile, or remove it.

## Submission workflow

1. Fork and clone the repository.
2. Copy the template to `data/community/<gpu_id>/result_YYYYMMDD_<name>.yaml`.
3. Add raw evidence in that GPU folder when available.
4. Run `python scripts/build.py` and `python scripts/validate.py`.
5. Open a pull request with the benchmark profile and hardware details.
6. A maintainer reviews the evidence and the generated per-GPU community
   summary before merging.
