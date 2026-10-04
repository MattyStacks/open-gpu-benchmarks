# Community GPU result folders

Place each community submission in the folder whose name exactly matches its
`gpu_id` in `data/gpus.yaml`:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
```

For example, use
`data/community/rtx_4090/result_20261003_cyberpunk_mattystacks.yaml`.
Every community file sets `submitted_by` to the GitHub username of the person
opening the pull request, and the file name ends with that username
(compared case-insensitively; lowercase is conventional). For a second file
with the same date and game, add a number before the username, such as
`result_20261003_cyberpunk_2_mattystacks.yaml`.
The validator checks
all `result_*.yaml` and `result_*.yml` files in these folders. The build
creates the corresponding generated summary at
`site/api/v1/community/<gpu_id>/summary.json`.

Each source file must use one non-empty `result` list. Keep the leading `-`
for every resolution/preset profile: it is required YAML list syntax, prevents
duplicate-key data loss, and lets the validator check each profile
independently. Matching profiles from this or another result file are averaged
into one generated summary; different resolutions or presets remain separate.
Start from [`templates/community_submission.yaml`](../../templates/community_submission.yaml).

Keep optional raw capture files in the same GPU folder, for example
`data/community/rtx_4090/raw/capture.csv`, and reference them from
`proof.raw_log`. Raw captures are not included in the generated browser API.
