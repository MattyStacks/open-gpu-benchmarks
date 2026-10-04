# Community GPU result folders

Each community submission lives in the folder whose name exactly matches its
`gpu_id` in `data/gpus.yaml`:

```text
data/community/<gpu_id>/result_YYYYMMDD_<game>_<github_user>.yaml
data/community/<gpu_id>/raw/<capture>.csv          (optional evidence)
```

**New here? Follow the step-by-step guide with examples in
[CONTRIBUTING.md](../../CONTRIBUTING.md).** Start from
[`templates/community_submission.yaml`](../../templates/community_submission.yaml).

Folder rules:

- Every file sets `submitted_by` to the GitHub username of the person opening
  the pull request, and the file name ends with that username (compared
  case-insensitively; lowercase is conventional). For a second file with the
  same date and game, add a number before the username, such as
  `result_20261003_cyberpunk_2_mattystacks.yaml`.
- The validator checks all `result_*.yaml` and `result_*.yml` files here. The
  build creates `site/api/v1/community/<gpu_id>/summary.json`.
- Each file uses one non-empty `result` list. Keep the leading `-` for every
  resolution/preset profile: it is required YAML list syntax, prevents
  duplicate-key data loss, and lets the validator check each profile
  independently. Matching profiles from this or another file are averaged into
  one generated summary; different resolutions or presets remain separate.
- Keep optional raw captures in the same GPU folder, such as
  `data/community/rtx_4090/raw/capture.csv`, and reference them from
  `proof.raw_log`. Raw captures are not included in the generated browser API.
