# AGENTS.md

Entry point for any AI coding agent working in this repository (Claude,
Copilot, Muse, Cursor, Codex, or others). Tool-specific files say the same
thing: [CLAUDE.md](CLAUDE.md) and
[.github/copilot-instructions.md](.github/copilot-instructions.md).

## Every change: update the changelog and the backlog

These two steps are required for every PR:

1. **[CHANGELOG.md](CHANGELOG.md)**: add a line under `Unreleased` for any
   change to behavior, the data contract, the API schema, the dashboard, the
   checks, the templates, or the contributor workflow. Data-only result
   submissions are the only exception.
2. **[docs/TODO.md](docs/TODO.md)** (the backlog): remove items you
   completed, and add anything you deferred, found broken, or were asked to
   do later. Don't start backlog items unless asked.

## Read before changing anything

- [.github/copilot-instructions.md](.github/copilot-instructions.md): the
  binding data rules and the release checklist.
- [docs/COPILOT_HANDOFF.md](docs/COPILOT_HANDOFF.md): architecture, data
  contract, and the published and fixture counts.
- [data/gpus/README.md](data/gpus/README.md): the catalog layout, ID rules, and
  every check rule.
- [CONTRIBUTING.md](CONTRIBUTING.md) and
  [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md): the
  submission rules.

When a rule changes, change it in every file that states it.

Data: `data/` holds only real data, because it's what deploys. Synthetic test
runs live in `tests/fixtures/data/` (same layout, its own catalog snapshot),
and `test_build.py` fails if a `synthetic: true` run appears in `data/`.
Preview them with `python scripts/build.py --data-dir tests/fixtures/data`.

Results: game runs require `system.os`: `windows` or `linux`, lowercase. The OS is a
grouping key, so Windows and Linux runs are never averaged together; the
distro, kernel, Mesa, and Proton are per-run detail fields, never grouping
keys or extra chart bars. Linux-only fields on a windows run (or the
reverse) are errors. Per-distro comparisons are DIY from the JSON.

`avg_fps` is required; `p1_low` is optional (3DMark and in-game benchmarks
report none). `proof.method` is required on every game run and names the
capture tool (`checks.PROOF_METHODS`); PresentMon is the recommended default,
and the method is never a grouping key. Frame-time tools must include
`p1_low`. Community results are anonymous by default: `submitted_by` is
optional and the file name is `result_YYYYMMDD_<game>.yaml`. A result someone
else measured adds a `credit` block with an https `source_url` (where it was
found) or, for unpublished numbers, a `permission` block; example credits use
made-up names, never a real creator. Upscaling is off unless the preset turns
it on (`upscaling` plus `preset_upscaling: true`), and it is a grouping key. A
community average more than 25% from the official average fails
`community-outlier`. Official runs are maintainer-verified by definition
("Verified" on the dashboard) and may credit someone by `name` alone.

Hosting: the canonical site is <https://opengpubenchmarks.com> (Cloudflare
Pages). GitHub Pages is a mirror. Only the canonical/SEO URLs are absolute,
robots.txt allows AI crawlers, and Cloudflare PR previews run only for the
owner's own PRs (`preview.yml`).

Catalog data must be accurate. Cite real pages in `sources`, list in
`covers` only the sections a page backs, and leave a value out rather than
guess it.

## Checks to run before finishing

Run the checks inside the project's virtual environment, never the global
Python. Create it once with `python -m venv .venv`; after that, only activate it.

```powershell
.venv\Scripts\Activate.ps1               # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
git diff --check
```

Don't commit generated `site/api/` files or `.venv/`. Create Git tags only
when asked.

## Clean up before finishing

Before you report a task complete, stop every server or background process
you started (for example the `python -m http.server 8000 --directory site`
preview), then run `deactivate` to leave the `.venv` virtual environment.
