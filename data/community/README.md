# Community GPU result folders

Each community submission lives in the folder whose name exactly matches its
`gpu_id`. The ID is the file name of a catalog entry under
[`data/gpus/`](../gpus/README.md). It names one exact product, including its
memory size, such as `rtx_4090_24gb_fe` or `steam_deck_oled_16gb`:

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
- `python scripts/validate.py results` checks all `result_*.yaml` and
  `result_*.yml` files here. It also rejects any other YAML file in a GPU
  folder, so files can't be skipped silently. The build creates
  `site/api/v1/community/<gpu_id>/summary.json`.
- If the product isn't in the catalog yet, add its entry under `data/gpus/`
  first or in the same pull request.
- Use block-style YAML only: one `-` line per list item, and no inline `[ ]` or
  `{ }`.
- Each file uses one non-empty `result` list. Keep the leading `-` for every
  resolution/preset profile: it is required YAML list syntax, prevents
  duplicate-key data loss, and lets the validator check each profile
  independently. Matching profiles from this or another file are averaged into
  one generated summary; different resolutions or presets remain separate.
- Keep optional raw captures in the same GPU folder, such as
  `data/community/rtx_4090_24gb_fe/raw/capture.csv`, and reference them from
  `proof.raw_log`. Raw captures are not included in the generated browser API.
