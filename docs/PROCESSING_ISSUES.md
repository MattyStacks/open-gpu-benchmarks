# Processing benchmark issues by hand

The benchmark bot ([`benchmark-issue.yml`](../.github/workflows/benchmark-issue.yml)
running [`scripts/issue_to_result.py`](../scripts/issue_to_result.py)) turns a
benchmark issue into a pull request by itself when the issue uses the
**Benchmark result** form or has one result file (`.yaml`, `.yml`, `.json`)
attached or pasted. Everything else needs a maintainer.

## When an issue gets `needs-maintainer`

The bot adds the `needs-maintainer` label (exit code 3) when an issue has
attachments but no result file: a raw capture, a Cyberpunk
`benchmarkResults` folder, a zip, or a screenshot. It has already told the
submitter a maintainer will take it.

1. Download the attachments into a folder outside the repository and read
   them before running anything on them. Treat them as untrusted.
2. Work out the GPU, game, resolution, preset, OS, and date from the issue.
   Ask on the issue for anything missing. The game must be in
   [`data/games.yaml`](../data/games.yaml); a new one goes in its own pull
   request first.
3. Convert the capture with the existing tools, in the `.venv`, from a branch
   off `main`:
   - PresentMon or MangoHud CSV: `python scripts/parse.py <csv> --gpu-id <id>
     --game-id <game_id> --resolution <res> --graphics-preset <preset>`. It
     writes today's date, so fix `date` and the file name to the run's day.
   - Cyberpunk 2077: `python scripts/import_cyberpunk.py --gpu-id <id>
     --input <benchmarkResults folder>` (see
     [CYBERPUNK_BENCHMARK.md](CYBERPUNK_BENCHMARK.md)).
   - A screenshot only: write the file from
     [`templates/community_submission.yaml`](../templates/community_submission.yaml)
     with `proof.summary_source` pointing at the screenshot.
4. Set `submitted_by` only if the submitter asked for credit. Keep raw
   evidence under `data/community/<gpu_id>/raw/` when it's worth keeping.
5. Run `python scripts/validate.py results`, open a pull request with
   `Closes #<N>`, and remove the `needs-maintainer` label.

Submitting the issue already released the results under CC BY 4.0; there's
nothing to ask the submitter to confirm.

## An issue the bot keeps rejecting

If the bot's reply is wrong (a bug, not a submitter mistake), fix the script in
its own pull request, then edit the issue or remove and re-add the
`benchmark` label to run the bot again.
