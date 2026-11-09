# Test fixtures

`tests/fixtures/data/` is the synthetic test data. It has the same layout as the real
[`data/`](../../data/) folder: a catalog snapshot under `gpus/`, plus
`official/`, `community/`, and `reviews.yaml`. Every run is marked
`synthetic: true`. The runs are made up, but the catalog specs are real.

- **Never deployed.** The site builds from the real `data/` folder only.
  `scripts/test_build.py` builds these fixtures into a temporary folder and
  checks the numbers they produce, and it fails if a synthetic run shows up in
  the real `data/`.
- **Preview them** with `python scripts/build.py --data-dir tests/fixtures/data`,
  then serve `site/` as usual. Run `python scripts/build.py` again to go back to
  the real data. `validate.py` takes the same flag.
- **The catalog is a snapshot.** It doesn't follow changes to the real
  catalog, so renaming or adding a real GPU doesn't break the tests. Change it
  only when a test needs to.
- **Changing a fixture** changes the numbers asserted in
  `check_fixture_build()` and `check_catalog_specs()` in `scripts/test_build.py`,
  and the fixture counts in `README.md` and `docs/COPILOT_HANDOFF.md`.
  `check_docs_in_sync()` fails until the `docs/COPILOT_HANDOFF.md` counts
  match.
- **`api_shape.json`** lists every key the fixture build writes, per payload.
  `check_api_shape()` fails when a key is added or removed. If the change is
  intended, bump `SCHEMA_VERSION` in `scripts/build.py` and run
  `python scripts/test_build.py --update-shape`. A fixture that adds a new
  optional field changes it too.
- **One credited run.** `community/rog_ally_z1_extreme_16gb/result_20261003_helldivers_mattystacks.yaml`
  has a `credit` block (made-up name, `example.com` URLs), so the API's
  `credits` and the dashboard's "Name (via @user)" line are tested.
- **The browser tests use them too.** `tests/e2e/serve_fixtures.py` builds
  these fixtures into `tests/e2e/.site` for the Playwright suite.
