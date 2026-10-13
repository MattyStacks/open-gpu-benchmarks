# Community benchmark submissions

Community source data is organized by catalog product. Find the exact ID in
[`data/gpus/`](../data/gpus/README.md): it is the file name of the product's
catalog entry, `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. Then add one
result file to its folder:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml
```

For example:

```text
data/community/rtx_4090_24gb_fe/result_20261003_cyberpunk.yaml
```

The ID names one exact product, including its memory size. An 8 GB and a 16 GB
card are separate IDs, and so are two board partners' versions of the same GPU.
Use the one you actually tested. If your product isn't in the catalog yet, add
its catalog entry first or in the same pull request (see
[`data/gpus/README.md`](../data/gpus/README.md)). Results can't point at an ID
that doesn't exist.

For a second file with the same date and game, add a number:
`result_20261003_cyberpunk_2.yaml`.

## Anonymous by default

You only have to share the result itself. A community run needs the product
(`gpu_id`), the `game`, the `result` numbers, `system.os`, and `proof.method`
(see [Comparable game runs](#comparable-game-runs)). Everything else, including
your name, CPU, driver, and raw captures, is optional. Add what you're happy to
share; more detail makes a run easier to review and compare.

- `submitted_by` is optional. Set it to your GitHub username if you want the
  dashboard to show "@you". Leave it out and the run shows as "Anonymous". If
  you set it, it must be a valid GitHub username.
- The file name doesn't include a username. Older files that end in one are
  still accepted.
- The data is anonymous, but a pull request isn't: GitHub shows the account
  that opened it, and each commit records an author name and email. To keep
  your email private, use GitHub's
  [noreply address](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address).
- Raw captures can contain your PC name, Windows username, or file paths.
  Check a log before you commit it.
- A run with no evidence (no `proof.raw_log`, `proof.summary_source`, or
  `credit.source_url`) is accepted, but the dashboard labels it "Unverified".

The folder name and `gpu_id` in the YAML must match. On a merged pull request,
the build includes that run in
`site/api/v1/community/<gpu_id>/summary.json` and in the GPU-rooted master
API. There is no separate approved or pending source tree.

## Comparable game runs

Game records use `benchmark_type: game` (the default when omitted) and require:

- `game`;
- a non-empty `result` list, where every entry has `resolution`,
  `graphics_preset`, and `avg_fps`. `p1_low` (1% low) is optional, but
  recommended; see [Capture methods](#capture-methods);
- frame generation off: `frame_generation: false`, which is the default when
  the field is left out;
- upscaling off, also the default, unless the preset turns it on (see
  [Upscaling](#upscaling));
- `proof.method`, the capture tool you used (see
  [Capture methods](#capture-methods));
- `system.os`, either `windows` or `linux` (lowercase). See
  [Operating system](#operating-system).

`result` is a YAML list, so every profile must start with `-`. The dash is
required: YAML would overwrite duplicate `result:` keys rather than retain two
profiles. This shape allows one captured machine run to submit multiple
resolution/preset combinations:

```yaml
gpu_id: arc_a770_16gb_le
game: Helldivers 2
system:
  os: windows
proof:
  method: presentmon
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
FPS values, disabled frame generation, upscaling, and a matching
official-baseline outlier. The build expands each entry into an independent
run, then groups only matching product ID (which already separates memory sizes
and board partners) and form factor, known laptop TGP/GPU power, game,
resolution, `graphics_preset`, upscaling, and OS. Matching entries from multiple files are
averaged; different profiles remain separate. Game version, distro, kernel, and
Proton version remain exact-run metadata rather than grouping keys. Desktop and
laptop GPUs never share a group, and neither do Windows and Linux runs.

## Upscaling

Benchmark with upscaling (DLSS, FSR, XeSS) **off**. That's the default: leave
`upscaling` out, or write `off`, `none`, or `native`. An upscaled run renders
fewer pixels than its resolution says, so its FPS isn't comparable with native
runs.

The one exception is a graphics preset that turns upscaling on by itself. Then
record the upscaler on that result item and say the preset set it:

```yaml
result:
  - resolution: 1440p
    graphics_preset: Example RT Preset
    upscaling: DLSS Quality
    preset_upscaling: true
    avg_fps: 79.1
```

`upscaling` without `preset_upscaling: true` is the `result-upscaling` error.
Upscaling is a grouping key, so an upscaled run is never averaged with native
runs of the same preset, and it's only outlier-checked against official runs
with the same upscaling.

## Capture methods

**`proof.method` is required on every game run.** It records which tool the
numbers came from. **PresentMon is the recommended way to capture a game run**:
it's free, and its raw CSV can go in `raw/` as evidence. Any of the tools below
is accepted, so use whichever you already have:

| `proof.method` | Tool | `p1_low` |
| -------------- | ---- | -------- |
| `presentmon` | PresentMon (recommended) | Required |
| `capframex` | CapFrameX | Required |
| `frameview` | NVIDIA FrameView | Required |
| `msi_afterburner` | MSI Afterburner / RivaTuner (RTSS) benchmark | Required |
| `mangohud` | MangoHud (Linux) | Required |
| `ocat` | OCAT | Required |
| `amd_adrenalin` | AMD Software: Adrenalin Edition performance metrics | Optional |
| `in_game_benchmark` | The game's built-in benchmark tool | Optional |
| `synthetic_benchmark` | 3DMark and similar | Optional |
| `other` | Anything else; name the tool in the pull request | Optional |

The tools marked Required record every frame, so they always give a 1% low,
and we want it. The others may report only an average.

The method is run detail, not a grouping key, so runs from different tools for
the same product, game, resolution, preset, upscaling, and OS are averaged together.
Built-in benchmark scenes are often lighter or heavier than real gameplay, so
say which scene you used in the pull request. A tool that isn't listed but
should be is a one-line change to `PROOF_METHODS` in `scripts/checks.py`.

A run with no `p1_low` still counts toward the average FPS. Its summary averages
the 1% low over only the runs that have one, and shows no 1% low when none do.
Leaving `p1_low` out of a Required tool's run is the `result-p1-low-required`
error. Leaving it out of an `amd_adrenalin`, `in_game_benchmark`, or `other`
run raises the `result-no-p1-low` warning, which is fine to ignore if your tool
didn't report one. `synthetic_benchmark` runs never warn.

## Submitting a result you found

The result doesn't have to be yours. If a YouTube video, review, or forum post
shows a benchmark, you can add it. You don't need the creator's permission, but
you do need to say where you found it, so a reviewer can check the numbers.
Start from
[`templates/community_found_result.yaml`](../templates/community_found_result.yaml)
and add a `credit` block:

```yaml
credit:
  source_url: https://example.com/example-creator/gpu-review
  name: Example Creator
  url: https://example.com/example-creator
```

The names and links above are placeholders.

- `source_url` is required: an `https://` link to the video, review, or post
  with the numbers. Link to the exact video or article, not just a channel.
- `name` (who measured them) and `url` (their channel or profile) are optional.
  Without a name, the dashboard shows the site, such as "example.com".
- `submitted_by` stays optional, the same as for your own runs.

Copy only what the source states. Use the product ID, resolution, and preset
it tested, and leave out details it doesn't give rather than guessing. Set
`proof.method` to the tool the source used, `in_game_benchmark` for a game's
built-in benchmark, or `other` when it doesn't say.

**Numbers that aren't published anywhere**, such as a friend's run, have no
`source_url`. Show that they agreed instead, with a `permission` block holding
at least one of:

```yaml
credit:
  name: Example Friend
  permission:
    note: Describe how and when they said yes
    screenshot: raw/permission_example_friend.png
    url: https://example.com/permission
```

- `note`: a short description of how and when they agreed;
- `screenshot`: an image (for example a message), saved in the same GPU folder,
  such as `data/community/<gpu_id>/raw/permission_example_friend.png`;
- `url`: an `https://` link showing permission.

A maintainer checks the source or the permission before merging. The dashboard
credits the source first and links it: "Example Creator (via @you)", or just
"Example Creator" when you leave out `submitted_by`. The API carries
`credit_name`, `credit_url`, and `credit_source_url` on every run, and a
`credits` list (`name`, `url`, `source_url`) on each summary. Any permission
proof stays in Git, like raw captures.

**Official runs** can carry a `credit` block too, when the maintainer enters a
run on someone else's behalf. Official runs are verified by the maintainer, so
an official credit only needs `name` (who ran it); `source_url` and
`permission` are optional.

**3DMark.** Name the benchmark in `game` (for example `3DMark Steel Nomad`), put
its version in `version`, and use the fixed resolution and preset it runs at.
Steel Nomad has one graphics test, so its score is the graphics-test FPS times
100 (a score of 8603 is 86.03 FPS). Copy `avg_fps` from the "Graphics test" box on
the results page, and add `score` if you like. For a benchmark with more than one
graphics test, such as Time Spy, enter the graphics-test FPS from the results
page, never the overall score divided by 100. Use the link to your 3DMark result
page as `proof.summary_source`. 3DMark lists every GPU in the machine, so make
sure the `gpu_id` is the card that ran the test. Start from
[`templates/community_steel_nomad.yaml`](../templates/community_steel_nomad.yaml).

## Operating system

Every game run sets `system.os` to `windows` or `linux`, in lowercase. The OS is
a grouping key: a Windows run and a Linux run of the same product, game,
resolution, and preset are two separate chart bars, never one average. The
distro is **not** a grouping key, so SteamOS, Bazzite, and CachyOS runs of the
same profile average together into one Linux bar.

Put the full OS name in `os_detail`, not in `os`. These optional fields go under
`system:` too. They are shown in the run details and carried on every run in the
JSON API:

| Applies to | Field | Type | Example |
| ---------- | ----- | ---- | ------- |
| both | `os_detail` | text | `Windows 11 Pro 24H2`, `SteamOS 3.6.19` |
| both | `os_build` | text | `"26100.2033"` |
| both | `driver` | text | `"566.36"`, `Mesa 24.2.3` |
| both | `resizable_bar` | true/false | `true` |
| both | `graphics_api` | text | `DX12`, `Vulkan` |
| windows | `game_mode` | true/false | `true` |
| windows | `hags` | true/false | hardware-accelerated GPU scheduling |
| windows | `memory_integrity` | true/false | VBS/HVCI core isolation |
| windows | `power_plan` | text | `Balanced` |
| linux | `distro` | text | `SteamOS`, `Bazzite`, `CachyOS` |
| linux | `distro_version` | text | `"3.6.19"` |
| linux | `kernel` | text | `"6.11.2-cachyos"` |
| linux | `mesa` | text | `"24.2.3"` |
| linux | `runtime` | `native`, `proton`, or `wine` | `proton` |
| linux | `proton` | text | `GE-Proton9-20` |
| linux | `dxvk` | text | `"2.4"` |
| linux | `vkd3d_proton` | text | `"2.13"` |
| linux | `launcher` | text | `Steam`, `Heroic`, `Lutris` |
| linux | `session` | text | `gamescope`, `KDE Wayland`, `X11` |
| linux | `gamemode` | true/false | Feral GameMode |

Quote version numbers so YAML keeps them as text. A Linux-only field on a
`windows` run, or a Windows-only field on a `linux` run, is an error: it's almost
always a copy-paste mistake.

```yaml
system:
  os: linux
  os_detail: SteamOS 3.6.19
  distro: SteamOS
  distro_version: "3.6.19"
  kernel: "6.5.0-valve22"
  driver: Mesa 24.1.0
  runtime: proton
  proton: GE-Proton9-20
  session: gamescope
```

**Comparing distros, kernels, or Proton versions.** The dashboard deliberately
shows one bar per OS, never one per distro. To chart distros yourself, download
`api/v1/community.json`, `api/v1/official.json`, or a per-product
`api/v1/<source>/<gpu_id>/summary.json`. Every run record, and every entry in a
summary's `implementations` list, carries `os`, `os_detail`, `distro`, `kernel`,
`mesa`, `proton`, and the other fields above.

## Machine details and evidence

Everything in this section is optional. Device or board name, GPU power,
overclock status, CPU, memory, power mode, display/MUX mode, driver, and the OS
details above all help a reviewer, so add whatever you know and are happy to
share. Laptop GPU power is the one worth adding: laptop runs are grouped by it.

A raw PresentMon capture is the best evidence. Put it under the same GPU
folder, for example:

```text
data/community/rtx_4090_24gb_fe/raw/cyberpunk_1440p.csv
```

Reference it with `proof.raw_log: raw/cyberpunk_1440p.csv`. Without a raw log,
link a screenshot or published summary in `proof.summary_source`, or the page
you found the result on in `credit.source_url`. The dashboard's evidence column
shows "Raw log", "Summary only", or, for a community run with no evidence at
all, "Unverified". The API carries the same as `proof_level`: `raw-log`,
`summary-only`, or `none`. Official runs are verified by the maintainer, so an
official run with no linked evidence is `maintainer-verified` and shows as
"Verified", never "Unverified".
Raw captures remain in Git but outside browser-facing JSON.

## Review and validation

`python scripts/validate.py results` checks every `result_*.yaml` and
`result_*.yml` file in both `data/official/` and `data/community/`, and every
`result` list entry. It verifies:

- folder and catalog identity
- the community file name format, and `submitted_by` when it's given
- the `credit` block, when it's given
- list shape
- comparable game settings
- frame-generation status
- impossible FPS values
- `proof.method`
- `system.os` and the OS detail fields

When a matching official baseline exists (same product, game, resolution,
preset, upscaling, and OS), a community average more than 25% different is a validation
error. Correct it, explain a materially different
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
it without telling you. Rename it to `result_YYYYMMDD_<game>.yaml` (community)
or `result_YYYYMMDD_<benchmark>.yaml` (official).

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
- a `result` item is missing `resolution`, `graphics_preset`, or `avg_fps`
- `avg_fps`, `p1_low`, or `score` isn't a number

Use `graphics_preset`, never `settings`.

#### `result-impossible`

`p1_low` is higher than `avg_fps`. Check that the two values aren't swapped.

#### `result-proof-method`

`proof.method` is missing, or isn't one of the listed capture tools
(`presentmon`, `capframex`, `frameview`, `msi_afterburner`, `amd_adrenalin`,
`mangohud`, `ocat`, `in_game_benchmark`, `synthetic_benchmark`, or `other`).
Add it under `proof:` and pick the tool you used; see
[Capture methods](#capture-methods).

#### `result-p1-low-required`

A result entry has no `p1_low`, but its `proof.method` is a tool that always
reports a 1% low (`presentmon`, `capframex`, `frameview`, `msi_afterburner`,
`mangohud`, or `ocat`). Add the 1% low from the tool's summary. If the numbers
actually came from somewhere else, such as the game's own benchmark, fix
`proof.method` instead. See [Capture methods](#capture-methods).

#### `result-no-p1-low`

Warning only. A result entry has no `p1_low`, and its `proof.method` is
`amd_adrenalin`, `in_game_benchmark`, or `other`. That's fine if your tool
didn't report a 1% low; add it when it does. It isn't raised for
`synthetic_benchmark` runs, which never report one.

#### `result-frame-generation`

Frame generation is on. Re-run with it off.

#### `result-upscaling`

A result entry has `upscaling` set (such as `DLSS Quality`) without
`preset_upscaling: true`. Upscaling is off by default, so re-run with it off, or
remove the field if it was off. If the graphics preset turns upscaling on by
itself, keep `upscaling` and add `preset_upscaling: true`, which must be `true`
or `false`. See [Upscaling](#upscaling).

#### `result-os`

`system.os` is missing or isn't `windows` or `linux`. Set it under `system:`, in
lowercase. Put a full name such as `Windows 11` or `SteamOS 3.6` in
`system.os_detail` instead. Files made by an older `parse.py` have a top-level
`os:`; move it under `system:`. Other operating systems aren't supported yet.

#### `result-os-field`

An OS detail field under `system:` is wrong. One of these happened:

- A Linux-only field such as `proton`, `kernel`, or `distro` is on a `windows`
  run.
- A Windows-only field such as `hags` or `game_mode` is on a `linux` run.
- A true/false field such as `hags` or `resizable_bar` has text like `"yes"`.
- A text field such as `kernel` has an unquoted number. Quote it: `"6.8"`.
- `runtime` isn't `native`, `proton`, or `wine`.

See [Operating system](#operating-system) for the fields.

#### `result-system-field`

Warning only. A key under `system:` isn't a known field. Check the spelling
against [Operating system](#operating-system) and the template. The known
machine fields are `cpu`, `memory`, `power_mode`, `display_mode`, `driver`,
`device_name`, and `gpu_power_w`.

#### `community-submitter`

`submitted_by` is set, but it isn't a valid GitHub username. Fix it, or remove
the line: `submitted_by` is optional, and runs without it show as "Anonymous".

#### `community-filename`

The file name isn't `result_YYYYMMDD_<game>.yaml`: an eight-digit date, then the
game, in letters, numbers, `_`, or `-`. For repeats on the same day and game,
add `_2`, `_3`, and so on. Older files that also end in a username are fine.

#### `community-credit`

The `credit` block is wrong. One of these happened:

- `credit` isn't a section with indented fields.
- `credit` has neither `source_url` nor `permission`. Add `source_url`: the
  link where you found the results. Only unpublished numbers, such as a
  friend's, use `permission` instead.
- `credit.name` is set but empty, or isn't text.
- `credit.url` or `credit.source_url` isn't an `https://` link.
- An official run's `credit` has neither `name` nor `source_url`. Official runs
  are maintainer-verified, so the name of whoever ran it is enough.

See [Submitting a result you found](#submitting-a-result-you-found).

#### `community-permission`

`credit.permission` is set, but it's wrong. It needs at least one of `url` (an
`https://` link), `screenshot` (an image file inside this GPU folder, such as
`raw/permission.png`), or `note`. A screenshot path must exist and can't point
outside the folder. Permission is optional when `credit.source_url` says where
the results were published.

#### `community-outlier`

The average FPS is more than 25% away from the matching official result (the gap is measured
against the official average). Re-check
the settings, explain the profile difference in the pull request, or remove the
entry.

#### `result-no-baseline`

Warning only. No official result has the same product, game, resolution,
preset, upscaling, and OS to compare against, so a maintainer reviews it by hand.

#### `result-no-proof`

Warning only. The run points at no evidence, so the dashboard labels it
"Unverified". Add `proof.raw_log` (preferred), `proof.summary_source`, or, for a
result you found, `credit.source_url`.

#### `result-laptop-tgp`

Warning only. Laptop results are grouped by GPU power, so add `gpu_power_w`: the
TGP the laptop actually ran at.
