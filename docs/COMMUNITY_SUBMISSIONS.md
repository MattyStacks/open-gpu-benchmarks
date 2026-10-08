# Community benchmark submissions

Community source data is organized by catalog product. Find the exact ID in
[`data/gpus/`](../data/gpus/README.md): it is the file name of the product's
catalog entry, `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. Then add one
result file to its folder:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
```

For example:

```text
data/community/rtx_4090_24gb_fe/result_20261003_cyberpunk_mattystacks.yaml
```

The ID names one exact product, including its memory size. An 8 GB and a 16 GB
card are separate IDs, and so are two board partners' versions of the same GPU.
Use the one you actually tested. If your product isn't in the catalog yet, add
its catalog entry first or in the same pull request (see
[`data/gpus/README.md`](../data/gpus/README.md)). Results can't point at an ID
that doesn't exist.

Every community file sets `submitted_by` to the GitHub username of the person
opening the pull request, and the file name ends with that username
(compared case-insensitively; lowercase is conventional). For a second file
with the same date and game, add a number before the username, such as
`result_20261003_cyberpunk_2_mattystacks.yaml`.

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
gpu_id: arc_a770_16gb_le
submitted_by: MattyStacks
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
only matching product ID (which already separates memory sizes and board
partners) and form factor, known laptop TGP/GPU power, game, resolution, and
`graphics_preset`. Matching entries from multiple files are
averaged; different profiles remain separate. Game version remains exact-run
metadata rather than a grouping key. Desktop and laptop GPUs never share a
group.

## Machine details and evidence

Include device or board name, GPU power, overclock status, CPU, memory, power
mode, display/MUX mode, driver, and operating system whenever known.

PresentMon or another raw capture is strongly preferred. Put optional evidence
under the same GPU folder, for example:

```text
data/community/rtx_4090_24gb_fe/raw/cyberpunk_1440p.csv
```

Reference it with `proof.raw_log: raw/cyberpunk_1440p.csv`. Summary-only
submissions must provide `proof.summary_source`; the dashboard labels them
accordingly. Raw captures remain in Git but outside browser-facing JSON.

## Review and validation

`python scripts/validate.py results` checks every `result_*.yaml` and
`result_*.yml` file in both `data/official/` and `data/community/`, and every
`result` list entry. It verifies:

- folder and catalog identity
- that `submitted_by` is a valid GitHub username matching the end of the file
  name (community only)
- list shape
- comparable game settings
- frame-generation status
- impossible FPS values

When a matching official baseline exists, a community average more than 50%
different is a validation error. Correct it, explain a materially different
profile, or remove it.

Result files use block-style YAML only: every list item on its own `-` line,
with no inline `[ ]` or `{ }`.

On a pull request, GitHub runs three separate checks, so you can see which part
failed:

| Check | Runs | Covers |
| ----- | ---- | ------ |
| **Catalog entries** | `python scripts/validate.py catalog` | `data/gpus/**` (rules in [`data/gpus/README.md`](../data/gpus/README.md#what-the-checks-mean)) |
| **Benchmark results** | `python scripts/validate.py results` | `data/official/**`, `data/community/**` (rules below) |
| **Build and tests** | `build.py`, `test_build.py` | the generated API and the regression tests |

Every problem is reported at once, each starting with its rule name in
brackets. Errors block the merge. Warnings are suggestions.

## Submission workflow

The step-by-step contributor walkthrough, with examples, lives in
[CONTRIBUTING.md](../CONTRIBUTING.md). In short: fork, add one result file (and
optional raw evidence) under `data/community/<gpu_id>/`, run `validate.py`,
`build.py`, and `test_build.py`, then open a pull request. A maintainer
reviews the evidence and the generated per-GPU community summary before
merging.

## What the checks mean

#### `yaml-invalid`

The file isn't valid YAML. Check the indentation (two spaces, no tabs), and quote
text that contains `: `.

#### `yaml-inline`

The file uses inline `[ ]` or `{ }`. Write each list item on its own `-` line,
and leave out empty fields instead of writing `{}` or `[]`.

#### `result-not-mapping`

The file is empty, or it starts with `-`. Fields such as `gpu_id` and `game`
start at the left margin. Only the items under `result:` start with `-`.

#### `result-filename`

A YAML file in a GPU folder doesn't start with `result_`, so the build would skip
it without telling you. Rename it to `result_YYYYMMDD_<game>_<github_user>.yaml`
(community) or `result_YYYYMMDD_<benchmark>.yaml` (official).

#### `result-folder`

`gpu_id` in the file doesn't match the folder name. Move the file to
`data/<official or community>/<gpu_id>/`, or correct `gpu_id`.

#### `result-unknown-gpu`

`gpu_id` isn't a catalog ID. Copy the exact file name, without `.yaml`, of the
product's entry under `data/gpus/`, or add the entry first. Product IDs such as
`rtx_4090_24gb_fe` replaced the old model-level IDs such as `rtx_4090`.

#### `result-reference-id`

`gpu_id` names a reference file under `data/gpus/reference/`, which holds a
GPU's shared specs, not a product. Use the ID of the exact card, laptop, or
handheld you tested, such as `rtx_4090_24gb_fe` rather than `rtx_4090_24gb`.

#### `result-form-factor`

`form_factor` in the result disagrees with the catalog entry. Remove the field so
the catalog value is used, or fix it.

#### `result-list`

`result` is missing, empty, or not a list. Use one `result:` key with one `-`
item per resolution/preset profile.

#### `result-field`

One of these is wrong:

- the result is missing `game`
- a `result` item is missing `resolution`, `graphics_preset`, `avg_fps`, or
  `p1_low`
- an FPS value isn't a number

Use `graphics_preset`, never `settings`.

#### `result-impossible`

`p1_low` is higher than `avg_fps`. Check that the two values aren't swapped.

#### `result-frame-generation`

Frame generation is on. Re-run with it off. Upscaling is fine; record it in
`upscaling`.

#### `community-submitter`

`submitted_by` is missing or isn't a valid GitHub username. Set it to the GitHub
username that opens the pull request.

#### `community-filename`

The file name doesn't end with the `submitted_by` username. Rename it to
`result_YYYYMMDD_<game>_<github_user>.yaml`. For repeats on the same day and
game, add `_2`, `_3`, and so on before the username.

#### `community-outlier`

The average FPS is more than 50% away from the matching official result. Re-check
the settings, explain the profile difference in the pull request, or remove the
entry.

#### `result-no-baseline`

Warning only. No official result has the same product, game, resolution, and
preset to compare against, so a maintainer reviews it by hand.

#### `result-no-driver`

Warning only. Add `system.driver` when you know it.

#### `result-no-proof`

Warning only. Add `proof.raw_log` (preferred), or at least `proof.summary_source`.

#### `result-laptop-tgp`

Warning only. Laptop results are grouped by GPU power, so add `gpu_power_w`: the
TGP the laptop actually ran at.
