# Community benchmark submissions

Community submissions are exact benchmark runs. The dashboard stores their
machine details, but charts use grouped summaries so comparisons remain easy
to read.

## Comparable runs

Runs are grouped only when they match on:

- GPU identity and form factor;
- laptop GPU power/TGP when it is known;
- game;
- resolution;
- graphics preset in `graphics_preset`.

Game version is retained as metadata but is not a grouping key. Frame
generation must always be disabled. Use a clear graphics preset such as
`Low`, `Medium`, `High`, `Ultra`, or a game-specific preset such as
`Steam Deck`. Add ray tracing and upscaling details where applicable.

Desktop and laptop GPUs never share a group. Laptop TGP is optional because
it is not always discoverable, but contributors are strongly encouraged to
provide it.

## Exact machine details

Include the device or board name, GPU power, overclock status, CPU, memory,
power mode, display/MUX mode, driver, and operating system whenever known.
These fields make the long-term dataset useful for hardware analysis and
future reviews.

Factory-overclocked implementations may receive separate catalog entries when
the performance difference is meaningful. Otherwise, retain the overclock
status as metadata.

## Evidence and review

PresentMon or another raw capture is strongly preferred. Summary-only
submissions are accepted when a clear source is provided, but are labeled on
the dashboard.

The pull-request validator compares a community average FPS value with a
matching official baseline when one exists. A difference greater than 50% is a
validation error that must be corrected, explained by changing the comparison
profile, or removed by a maintainer. This is a review guardrail, not proof
that every valid result must match one exact number.

Maintainers may edit or delete approved entries when a submission is found to
be incorrect, duplicated, or no longer supportable. Corrections should
preserve the raw evidence and explain the change in the pull request.

## Submission workflow

1. Fork and clone the repository.
2. Add a YAML file under `data/community/pending/`.
3. Attach or reference the raw capture under `data/community/approved/raw/`
   when approved.
4. Run `python scripts/build.py` and `python scripts/validate.py`.
5. Open a pull request with the benchmark profile and hardware details.
6. A maintainer reviews the evidence, corrects or rejects outliers, and moves
   accepted data to `data/community/approved/`.
7. The build regenerates grouped community summaries.
