# Community GPU result folders

Each community submission lives in the folder whose name exactly matches its
`gpu_id`. The ID is the file name of a catalog entry under
[`data/gpus/`](../gpus/README.md). It names one exact product, including its
memory size, such as `rtx_4090_24gb_fe` or `steam_deck_oled_16gb`:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game>.yaml
data/community/<gpu_id>/raw/<capture>.csv          (optional evidence)
data/community/<gpu_id>/raw/permission_<name>.png  (optional permission proof, unpublished third-party results)
```

**New here? Follow the step-by-step guide with examples in
[CONTRIBUTING.md](../../CONTRIBUTING.md).** Start from
[`templates/community_submission.yaml`](../../templates/community_submission.yaml),
or [`templates/community_found_result.yaml`](../../templates/community_found_result.yaml)
for a result you found in a video or review.

Folder rules:

- Files are anonymous by default and named `result_YYYYMMDD_<game>.yaml`. For
  a second file with the same date and game, add a number, such as
  `result_20261003_cyberpunk_2.yaml`. `submitted_by` (your GitHub username) is
  optional; see
  [Anonymous by default](../../docs/COMMUNITY_SUBMISSIONS.md#anonymous-by-default).
- Found a result in a video, review, or post? Add it with a `credit` block whose
  `source_url` links where you found it. No permission is needed. Only
  unpublished numbers, such as a friend's, use `credit.permission` instead; a
  permission screenshot lives in this folder, such as
  `raw/permission_example_friend.png`. See
  [Submitting a result you found](../../docs/COMMUNITY_SUBMISSIONS.md#submitting-a-result-you-found).
- Benchmark with upscaling off. Set `upscaling` only with
  `preset_upscaling: true`, when the graphics preset turns it on (see
  [Upscaling](../../docs/COMMUNITY_SUBMISSIONS.md#upscaling)).
- Set `proof.method` to the capture tool you used. PresentMon is recommended;
  tools that record every frame must include `p1_low` (see
  [Capture methods](../../docs/COMMUNITY_SUBMISSIONS.md#capture-methods)).
- `python scripts/validate.py results` checks all `result_*.yaml` and
  `result_*.yml` files here. It also rejects any other YAML file in a GPU
  folder, so files can't be skipped silently. The build creates
  `site/api/v1/community/<gpu_id>/summary.json`.
- If the product isn't in the catalog yet, add its entry under `data/gpus/`
  first or in the same pull request.
- Use block-style YAML only: one `-` line per list item, and no inline `[ ]` or
  `{ }`.
- Set `system.os` to `windows` or `linux` (lowercase). Windows and Linux runs
  are never averaged together, but distros are: put the distro, kernel, Mesa,
  and Proton details in their own `system` fields (see
  [Operating system](../../docs/COMMUNITY_SUBMISSIONS.md#operating-system)).
  Linux-only fields on a Windows run, or the reverse, fail the checks.
- Each file uses one non-empty `result` list. Keep the leading `-` for every
  resolution/preset profile: it is required YAML list syntax, prevents
  duplicate-key data loss, and lets the validator check each profile
  independently. Matching profiles from this or another file are averaged into
  one generated summary; different resolutions or presets remain separate.
- Keep optional raw captures in the same GPU folder, such as
  `data/community/rtx_4090_24gb_fe/raw/capture.csv`, and reference them from
  `proof.raw_log`. Raw captures are not included in the generated browser API.
