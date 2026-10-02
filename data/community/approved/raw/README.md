# Community raw captures

Place approved raw benchmark captures in GPU-specific folders here, for
example:

```text
raw/
  rog_ally_z1_extreme/
    cyberpunk_2077_1440p.csv
```

Keep the corresponding reviewed YAML summary in the parent `approved/` folder
and set `proof.raw_log` to the relative path of the capture.

Raw logs are versioned with the repository for reproducibility but are not
included in the browser-facing JSON generated for GitHub Pages. Contributors
who only have a benchmark summary may submit it with `proof.summary_source`;
the dashboard labels those records as **Summary only**.
