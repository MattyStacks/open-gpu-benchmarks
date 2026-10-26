# Community benchmark submissions

The easiest way to submit a result is a GitHub issue; see
[Submit through an issue](#submit-through-an-issue). A pull request is for
bulk or scripted uploads, and everything below describes the file either path
produces.

## Submit through an issue

Open a [**Benchmark result** issue](https://github.com/MattyStacks/open-gpu-benchmarks/issues/new?template=benchmark.yml)
and fill in the form. You don't need to fork, install anything, or write YAML.

1. The form applies the `benchmark` label. A bot
   ([`benchmark-issue.yml`](../.github/workflows/benchmark-issue.yml) running
   [`scripts/issue_to_result.py`](../scripts/issue_to_result.py)) writes
   `data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml` from your answers and
   runs the same checks as a pull request.
2. If something is wrong, such as an unknown GPU or a 1% low missing for a tool
   that reports one, the bot replies on the issue saying what to fix. Edit the
   issue and it checks again.
3. If everything passes, the bot opens a pull request from a
   `benchmark/issue-<N>` branch and links it on the issue. A maintainer (a
   [code owner](../.github/CODEOWNERS)) reviews and approves it; merging closes
   the issue. Editing the issue later rebuilds the same pull request.

The **Results** box takes one run per line: resolution, preset, average FPS,
and optionally the 1% low, separated by commas, such as
`1440p, Ultra, 79.1, 65.0`. The **GPU** box takes the catalog ID or the
product's exact name. The **Game** box takes the game's ID or exact name from
[`data/games.yaml`](../data/games.yaml); only listed games are accepted. A new
game is added first by its own pull request (see
[Adding a game or benchmark](#adding-a-game-or-benchmark)), then you edit the
issue and it checks again. Preset names that differ only in case from ones
already on the dashboard are rewritten to match, so groups don't split.
You stay anonymous unless you tick **Credit me as my GitHub username**, and the
license box (CC BY 4.0) is required (see [below](#your-results-become-public-data)).

The form covers one game and one day per issue, up to 20 runs, Windows or
Linux, with an optional proof link. It doesn't yet take raw capture uploads,
Linux-only system fields, per-run times, or `permission` credits. For those,
or for many results at once (for example the
[Cyberpunk 2077 importer](CYBERPUNK_BENCHMARK.md)), open a pull request as
[CONTRIBUTING.md](../CONTRIBUTING.md) describes.

## The result file

Community source data is organized by catalog product. Find the exact ID in
[`data/gpus/`](../data/gpus/README.md): it is the file name of the product's
catalog entry, `data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`. Then add one
result file to its folder:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game_id>.yaml
```

For example:

```text
data/community/rtx_5080_16gb_fe/result_20261003_cyberpunk_2077.yaml
```

Ran Cyberpunk 2077's built-in benchmark? `scripts/import_cyberpunk.py` writes
these files from the game's own results, one per day; see
[CYBERPUNK_BENCHMARK.md](CYBERPUNK_BENCHMARK.md).

The ID names one exact product, including its memory size. An 8 GB and a 16 GB
card are separate IDs, and so are two board partners' versions of the same GPU.
Use the one you actually tested. If your product isn't in the catalog yet, add
its catalog entry first or in the same pull request (see
[`data/gpus/README.md`](../data/gpus/README.md)). Results can't point at an ID
that doesn't exist. The same goes for the game: `game_id` must be in
[`data/games.yaml`](../data/games.yaml), and a new game is added there in the
same pull request (see [Adding a game or benchmark](#adding-a-game-or-benchmark)).

For a second file with the same date and game, add a number:
`result_20261003_cyberpunk_2077_2.yaml`.

## Adding a game or benchmark

Every result names its game with `game_id`, an ID from
[`data/games.yaml`](../data/games.yaml), never with free text. The dashboard
shows the registry's name, so `cyberpunk`, `CP2077`, and `Cyberpunk 2077` can't
end up as three different games.

**If your game or benchmark isn't in `data/games.yaml` yet, add it in the same
pull request as your results.** Copy an entry and fill in four lines:

```yaml
  - id: elden_ring
    name: Elden Ring
    type: game
    year: 2022
    steam_appid: 1245620
```

| Field | Required | What it is |
| --- | --- | --- |
| `id` | yes | Lowercase letters, digits, and single underscores. Results use it, so never change it later. |
| `name` | yes | The name the game or store shows. |
| `type` | yes | `game`, `synthetic` (3DMark and similar), or `engine_demo`. |
| `year` | yes | The year this edition or test came out, such as `2022`. |
| `steam_appid` | no | The number in the game's `store.steampowered.com/app/` link. |
| `igdb_id` | no | The game's numeric IGDB ID. |
| `url` | no | An https link to the game's official or store page. |
| `notes` | no | Anything that tells it apart from a similar entry. |

The store IDs and `url` are optional because not every game is on Steam or has
a page. **If the game has one, add it**: it pins down exactly which game the
entry means. Leave out what doesn't exist or what you can't check, and never
guess an ID.

**One entry per edition or test.** A remaster, a new edition (Special,
Anniversary, Enhanced, Next-Gen, VR), or a different test (3DMark Steel Nomad
and Steel Nomad Light) performs differently, so it gets its own ID, such as
`skyrim_special_edition` and `skyrim_anniversary_edition`. A patch or a game
update does not: put that in the result file's `version` field. Version is
recorded on each run, but it never splits a group.

The `game-*` rules under [What the checks mean](#what-the-checks-mean) explain
each registry error.

## Anonymous by default

You only have to share the result itself. A community run needs the product
(`gpu_id`), the `game_id`, the `date` (see [Date and time](#date-and-time)), the
`result` numbers, `system.os`, and `proof.method` (see
[Comparable game runs](#comparable-game-runs)). Everything else, including
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

## Your results become public data

Everything in this repository's `data/` folder is licensed under
[CC BY 4.0](../data/LICENSE) with reasonable attribution. So is everything the
site publishes from it: the dashboard, the JSON API, and the plain-text
tables. The [license page](https://opengpubenchmarks.com/license/) explains
what counts as reasonable attribution.

**When you submit a result (through a benchmark issue or a pull request), you
agree to release what you submit under CC BY 4.0.** In plain English:

- **Anyone can use your numbers for anything.** They can copy them, share
  them, change them, put them in their own charts, videos, articles, apps,
  or datasets, use them in something they sell, or train AI on them.
- **Sites have to say where the data came from.** A site, app, or article
  that uses the data must credit Open GPU Benchmarks and link back, so its
  readers can find the source, report problems, and contribute their own
  runs. In a chart image or a video, a text credit ("Source:
  opengpubenchmarks.com") counts. AI models credit the data in their model
  card or documentation, not in every answer.
- **You get credit here.** Your `submitted_by` username, or the `credit` for
  a result you found, is recorded with the result on this site, in the API,
  and in the Git history. Reusers credit Open GPU Benchmarks, not each
  submitter, but your name stays attached to your runs here.
- **You can't take it back.** You can ask for a result to be removed from the
  site (see [Fixing or removing a result](../CONTRIBUTING.md#fixing-or-removing-a-result)).
  Copies other people already made, and the Git history, stay public.
- **It covers everything in your submission.** That means the numbers, any
  machine details you include (CPU, driver, OS, and so on), and any raw
  captures or screenshots you add under `raw/`. Leave out anything you don't
  want public.
- **Only submit what you're allowed to share:**
  - **Your own runs**: yes.
  - **A result you found** in a video, review, or post: you submit the numbers
    and a link to where you found them, and that's what becomes CC BY 4.0.
    Don't upload the creator's screenshots, video frames, or text; the link is
    enough. Their video or article itself stays theirs.
  - **A friend's unpublished numbers**: they must agree to their numbers being
    published under these terms, and your `permission` note should say so.
- **No promises.** The data is shared as it is, with no guarantee that it's
  accurate (CC BY 4.0 section 5). Reviews and checks catch a lot, not
  everything.

This applies to official runs too. Data published before the switch to
CC BY 4.0 was released under CC0 1.0, and copies made under those terms keep
them. The code is separate and uses the [MIT license](../LICENSE). Blog posts
are separate too: their text stays the author's copyright, all rights
reserved, unless the post is marked AI-generated.

## Date and time

Every result file, official or community and of any benchmark type, needs a
`date`: the day you ran it, as a quoted `'YYYY-MM-DD'`. It must be the same day
as the `YYYYMMDD` in the file name. Each file holds one day of runs, so one
date covers the whole file. For a
[result you found](#submitting-a-result-you-found), use the day the video,
review, or post was published.

Each `result` item can also add a `time`: the local 24-hour time you ran it,
quoted, as `'HH:MM'` or `'HH:MM:SS'`. It's optional and has no time zone, so
treat it as the order of runs within the day, not an exact moment.

```yaml
gpu_id: rtx_5080_16gb_fe
game_id: cyberpunk_2077
date: '2026-10-13'
result:
  - time: '18:44'
    resolution: 1440p
    graphics_preset: High
    avg_fps: 151.2
```

Neither field groups runs: two runs of the same profile on different days are
averaged together like any others. The API puts `date` and `time` (`""` when
not set) on every run, so you can filter runs by age yourself.
`scripts/parse.py` and `scripts/import_cyberpunk.py` fill both in for you.

## Comparable game runs

Game records use `benchmark_type: game` (the default when omitted) and require:

- `game_id`, an ID from `data/games.yaml` (see
  [Adding a game or benchmark](#adding-a-game-or-benchmark));
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
gpu_id: rtx_5080_16gb_fe
game_id: helldivers_2
date: '2026-10-03'
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
and board partners) and form factor, known laptop TGP/GPU power, `game_id`,
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
error. Leaving it out of an `amd_adrenalin` or `other` run raises the
`result-no-p1-low` warning, which is fine to ignore if your tool didn't report
one. An `in_game_benchmark` file gets a single `info` note instead, because a
game's built-in benchmark often logs no frame times, or the log wasn't kept.
`synthetic_benchmark` runs say nothing.

## Submitting a result you found

The result doesn't have to be yours. If a YouTube video, review, or forum post
shows a benchmark, you can add it. You don't need the creator's permission, but
you do need to say where you found it, so a reviewer can check the numbers.
Submit only the numbers and the link, not the creator's screenshots or text,
because what you submit becomes public data (see
[Your results become public data](#your-results-become-public-data)).
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

Copy only what the source states. Set `date`, and the file name's date, to
the day the source was published. Use the product ID, resolution, and preset
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

- `note`: a short description of how and when they agreed, including that
  they're fine with the numbers being public data anyone can use (see
  [Your results become public data](#your-results-become-public-data));
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

**3DMark.** Set `game_id` to the test's registry ID (for example
`3dmark_steel_nomad`, a `synthetic` entry; add the test to `data/games.yaml`
first if it isn't there), put its version in `version`, and use the fixed
resolution and preset it runs at (Steel Nomad renders at 4K, Steel Nomad Light
at 1440p).
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

### System memory

Three optional fields describe the system RAM. Leave out any you don't know;
a missing one is never a warning. None of them group runs or appear on the
charts. They're in the API, so people using the data can filter by them.

```yaml
system:
  memory_gb: 32          # a number of GB, not "32 GB"
  memory_type: DDR5-6000 # type and speed (MT/s), if you know them
  memory_channels: 2     # 1 single, 2 dual, 4 quad, 8 on some server boards
```

`memory_gb` and `memory_channels` are numbers in the API (`null` when missing),
and `memory_type` is text (`""` when missing). The old free-text `memory:` key
is now `memory_gb`.

### Test benches (official runs only)

The maintainer tests desktop GPUs on more than one system, so a reader can see
what the same card does in a DDR5, DDR4, or DDR3 PC. The systems are listed in
[`data/testbenches.yaml`](../data/testbenches.yaml), and the dashboard names
each by its memory type:

| Dashboard label | Bench | Memory |
| --- | --- | --- |
| DDR5 Bench (primary) | Ryzen 7 9800X3D | DDR5-6000 |
| DDR4 Bench | Ryzen 5 5600X3D | DDR4-3200 |
| DDR3 Bench (planned) | Core i7-4790 | DDR3 |

The label comes from the part of `memory_type` before the dash, so a DDR6
system becomes "DDR6 Bench" with no code change.

Every official desktop run names its bench with a top-level `testbench_id`:

```yaml
gpu_id: rtx_5080_16gb_fe
testbench_id: am5_9800x3d_ddr5
```

The bench is a grouping key, so the same GPU on two benches is two summaries
and two bars on the chart, never one average. Laptops, handhelds, and iGPUs are
their own platforms and leave `testbench_id` out. A bench with
`counts_as: <other bench>` joins that bench's summaries (its runs keep their
own CPU in the run detail), which is how an interim machine's runs can be
folded into the primary bench's average.

**Community runs never use `testbench_id`.** Describe your machine under
`system:` (`cpu`, `memory_gb`, `memory_type`, `memory_channels`) instead. The
`community-outlier` check compares community runs with official runs on the
primary bench only.

A raw PresentMon capture is the best evidence. Put it under the same GPU
folder, for example:

```text
data/community/rtx_5080_16gb_fe/raw/cyberpunk_1440p.csv
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

On a pull request, GitHub runs four separate checks, so you can see which part
failed:

| Check | Runs | Covers |
| ----- | ---- | ------ |
| **Catalog entries** | `python scripts/validate.py catalog` | `data/gpus/**` (rules in [`data/gpus/README.md`](../data/gpus/README.md#what-the-checks-mean)) |
| **Benchmark results** | `python scripts/validate.py results` | `data/official/**`, `data/community/**` (rules below) |
| **Build and tests** | `build.py`, `test_build.py` | the generated API and the regression tests |
| **Blog** | `npm --prefix blog run build` | blog posts in `content/` (rules in [`content/README.md`](../content/README.md)) |

Every problem is reported at once, each starting with its rule name in
brackets. Errors block the merge. Warnings are suggestions.

## Submission workflow

Most results come in through a [Benchmark result issue](#submit-through-an-issue),
which the bot turns into a pull request. For bulk or scripted uploads, the
step-by-step pull request walkthrough, with examples, lives in
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

The file is empty, or it starts with `-`. Fields such as `gpu_id` and `game_id`
start at the left margin. Only the items under `result:` start with `-`.

#### `result-filename`

A YAML file in a GPU folder doesn't start with `result_`, so the build would skip
it without telling you. Rename it to `result_YYYYMMDD_<game_id>.yaml`.

#### `result-date`

The file has no `date`, or it isn't a quoted `'YYYY-MM-DD'` day that has
already happened. Add `date: '2026-10-03'` near the top, with the quotes;
without them, YAML reads it as a date object instead of text. For a result you
found, use the source's publish date. See [Date and time](#date-and-time).

#### `result-date-filename`

`date` and the `YYYYMMDD` at the start of the file name are different days. Fix
whichever one is wrong. If the file really holds runs from two days, split it
into one file per day.

#### `result-time`

A `result` item's `time` isn't a quoted 24-hour `'HH:MM'` or `'HH:MM:SS'`, such
as `'09:05'` or `'21:40:12'`. Quote it: unquoted, YAML reads `14:30` as the
number 870. `time` is optional, so you can also remove it.

#### `result-folder`

`gpu_id` in the file doesn't match the folder name. Move the file to
`data/<official or community>/<gpu_id>/`, or correct `gpu_id`.

#### `result-unknown-gpu`

`gpu_id` isn't a catalog ID. Copy the exact file name, without `.yaml`, of the
product's entry under `data/gpus/`, or add the entry first. Product IDs such as
`rtx_5080_16gb_fe` replaced the old model-level IDs such as `rtx_5080`.

#### `result-reference-id`

`gpu_id` names a reference file under `data/gpus/reference/`, which holds a
GPU's shared specs, not a product. Use the ID of the exact card, laptop, or
handheld you tested, such as `rtx_5080_16gb_fe` rather than `rtx_5080_16gb`.

#### `result-game-id`

The file has no `game_id`, or it still uses the old free-text `game` key.
Replace `game: Cyberpunk 2077` with `game_id: cyberpunk_2077`; the message
names the ID when the old name matches a registry entry. If the game isn't
registered yet, add it to `data/games.yaml` in the same pull request (see
[Adding a game or benchmark](#adding-a-game-or-benchmark)).
`scripts/import_cyberpunk.py` upgrades its own older files when you run it
again.

#### `result-unknown-game`

`game_id` isn't an ID in `data/games.yaml`. Check the spelling against the
file. If it's a new game or benchmark, add its entry in the same pull request:
the message prints a stub with `id`, `name`, `type`, and `year` to fill in,
plus `steam_appid` or `url` when the game has one.

#### `game-registry`

`data/games.yaml` is missing, or it doesn't hold a `games:` list. Every result
needs it. Restore the file, and keep one `- id: ...` item per game under
`games:`.

#### `game-field`

A `data/games.yaml` entry is wrong. One of these happened:

- `id`, `name`, `type`, or `year` is missing
- `type` isn't `game`, `synthetic`, or `engine_demo`
- `year` isn't a release year written as a plain number, such as `2022`
- `steam_appid` or `igdb_id` isn't a whole number without quotes
- `url` isn't an https:// link
- a field isn't one of `id`, `name`, `type`, `year`, `steam_appid`, `igdb_id`,
  `url`, or `notes`

#### `game-id-format`

A game `id` may only use lowercase letters, digits, and single underscores,
such as `cyberpunk_2077` or `3dmark_steel_nomad`.

#### `game-duplicate`

Two entries share an `id`, or two share a `name` (ignoring case). Each edition
or test gets one entry with its own ID and its own name, such as
`Skyrim Special Edition` and `Skyrim Anniversary Edition`.

#### `testbench-registry`

`data/testbenches.yaml` doesn't hold a `testbenches:` list. Keep one
`- id: ...` item per bench under `testbenches:`. See
[Test benches](#test-benches-official-runs-only).

#### `testbench-field`

A `data/testbenches.yaml` entry is wrong. One of these happened:

- `id`, `name`, `status`, `cpu`, or `memory_type` is missing or isn't text
- `status` isn't `active`, `planned`, `interim`, or `retired`
- `primary` isn't `true` or `false`
- `memory_type` isn't a DDR type and speed, such as `DDR5-6000` (it names
  the bench: "DDR5 Bench"). A planned bench may write just the type, such as
  `DDR3`, until its speed is known.
- `memory_gb` or `memory_channels` is missing on a bench that isn't
  `planned`, or isn't a whole number (`64`, `2`).
- a field isn't one of the fields listed at the top of the file

#### `testbench-id-format`

A bench `id` may only use lowercase letters, digits, and single underscores,
such as `am5_9800x3d_ddr5`.

#### `testbench-duplicate`

Two entries share an `id`. Give each bench its own.

#### `testbench-primary`

Exactly one bench needs `primary: true`, and it must be `active` (or
`interim`) and can't use `counts_as`. Community runs are compared with the
primary bench's official runs.

#### `testbench-counts-as`

`counts_as` must name another bench in the file, with the same DDR type, that
doesn't itself use `counts_as`.

#### `result-testbench-id`

An official desktop run has no `testbench_id`, or a laptop, handheld, or iGPU
run has one. Official desktop runs name the bench they ran on, an ID from
`data/testbenches.yaml`; other form factors are their own platform and leave it
out.

#### `result-unknown-testbench`

`testbench_id` isn't an ID in `data/testbenches.yaml`. Fix the spelling, or add
the bench to the registry in the same pull request.

#### `result-testbench-community`

A community file sets `testbench_id`. Benches are the maintainer's machines;
remove the line and describe your system under `system:` instead.

#### `result-testbench-mismatch`

Warning only. The run's `system.cpu`, `memory_gb`, `memory_type`, or
`memory_channels` disagrees with its bench in `data/testbenches.yaml`, which
usually means the run is tagged with the wrong bench. The CPU matches when
either name contains the other, so `AMD Ryzen 7 9800X3D 8-Core Processor`
matches `AMD Ryzen 7 9800X3D`. On a planned bench only the memory type is
compared, not its speed.

#### `result-form-factor`

`form_factor` in the result disagrees with the catalog entry. Remove the field so
the catalog value is used, or fix it.

#### `result-list`

`result` is missing, empty, or not a list. Use one `result:` key with one `-`
item per resolution/preset profile.

#### `result-field`

One of these is wrong:

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

Never an error. A result entry has no `p1_low`, so the dashboard charts only
its average.

- `amd_adrenalin` or `other`: a warning for each entry. That's fine if your
  tool didn't report a 1% low; add it when it does.
- `in_game_benchmark`: one `info` note per file, counting the entries without
  one. Built-in benchmarks often have no 1% low, or their frame log (such as
  Cyberpunk 2077's `frames.csv`) wasn't kept. Info notes never fail a check.
- `synthetic_benchmark`: nothing, since 3DMark never reports one.

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
machine fields are `cpu`, `memory_gb`, `memory_type`, `memory_channels`,
`power_mode`, `display_mode`, `driver`, `device_name`, and `gpu_power_w`.
`display_mode` may also go on a single `result` item, when it differs between
the profiles in one file; the item's value wins.

#### `result-system-memory`

A system memory field is wrong. Each of these fields is optional, and leaving
one out is never reported. One of these happened:

- `memory_gb` isn't a number from 1 to 65536. Write just the number of GB:
  `memory_gb: 32`, not `memory_gb: 32 GB`.
- The file uses the old `memory:` or `ram:` key. Rename it to `memory_gb` and
  keep only the number.
- `memory_channels` isn't a whole number from 1 to 32. Write `2` for dual
  channel, not `dual`.
- `memory_type` is a number instead of text.
- Warning only: `memory_type` doesn't look like `DDR5-6400` or `LPDDR5X-7500`,
  which is the type, a dash, and the speed in MT/s.

See [System memory](#system-memory).

#### `community-submitter`

`submitted_by` is set, but it isn't a valid GitHub username. Fix it, or remove
the line: `submitted_by` is optional, and runs without it show as "Anonymous".

#### `community-filename`

The file name isn't `result_YYYYMMDD_<game_id>.yaml`: an eight-digit date, then
the game ID, in letters, numbers, `_`, or `-`. For repeats on the same day and game,
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
against the official average). For desktop GPUs, only official runs on the
primary test bench count as the baseline. Re-check
the settings, explain the profile difference in the pull request, or remove the
entry.

#### `result-no-baseline`

Warning only. No official result has the same product, game, resolution,
preset, upscaling, and OS (on the primary test bench, for desktop GPUs) to
compare against, so a maintainer reviews it by hand.

#### `result-no-proof`

Warning only. The run points at no evidence, so the dashboard labels it
"Unverified". Add `proof.raw_log` (preferred), `proof.summary_source`, or, for a
result you found, `credit.source_url`.

#### `result-laptop-tgp`

Warning only. Laptop results are grouped by GPU power, so add `gpu_power_w`: the
TGP the laptop actually ran at.
