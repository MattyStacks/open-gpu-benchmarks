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

## Branching

Always create a new branch from an up-to-date `main` (`git checkout main && git pull`, then
`git checkout -b <type>/<name>`). Never stack a branch on another unmerged
feature branch, unless the user explicitly asks for it. The usual workflow:
commit everything, push, and open a PR into `main`; one topic per branch.

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
`p1_low`; on an in-game benchmark a missing one is only an `info` note. Community results are anonymous by default: `submitted_by` is
optional and the file name is `result_YYYYMMDD_<game>.yaml`. A result someone
else measured adds a `credit` block with an https `source_url` (where it was
found) or, for unpublished numbers, a `permission` block; example credits use
made-up names, never a real creator. Upscaling is off unless the preset turns
it on (`upscaling` plus `preset_upscaling: true`), and it is a grouping key. A
community average more than 25% from the official average fails
`community-outlier`. Official runs are maintainer-verified by definition
("Verified" on the dashboard) and may credit someone by `name` alone.
Cyberpunk 2077 built-in benchmark runs come in through
`scripts/import_cyberpunk.py` (guide: `docs/CYBERPUNK_BENCHMARK.md`): one
`result_YYYYMMDD_cyberpunk_2077.yaml` per day and setup, one `result` item per
run, each naming its run folder in `benchmark_run`; keep its preset and
upscaler labels stable, because changing one splits dashboard groups.

Hosting: the canonical site is <https://opengpubenchmarks.com> (Cloudflare
Pages). GitHub Pages is a mirror. Only the canonical/SEO URLs are absolute,
robots.txt allows AI crawlers, and Cloudflare PR previews run only for the
owner's own PRs (`preview.yml`).

Blog: `/blog/` is an Astro project in `blog/` that renders
`content/posts/<slug>/index.md(x)` into `site/blog/` (gitignored). It builds
after `build.py`, because charts read `site/api/v1/`. `build.py` lists
non-draft posts in the sitemap and `llms.txt`. Rules are in
`blog/src/content.config.ts` and `blog/src/lib/posts.ts`.
- `BLOG_BASE` is `/blog` for Cloudflare and `/open-gpu-benchmarks/blog` for
  the GitHub Pages mirror. Build links from `import.meta.env.BASE_URL`.
- `blog/src/styles/tokens.css` is a verbatim copy of the dashboard's `:root`
  tokens, and `test_build.py` checks they match.
- The author writes the content. AI may clean up wording and insert
  affiliate links, noted in `ai_assistance`. A post AI wrote sets
  `ai_generated: true`. Never type benchmark numbers; use `<BenchChart>`. Store links go only through `<AffiliateLink>` with
  `affiliate: true`. See [content/README.md](content/README.md).

Licenses: code is MIT (`LICENSE`), and benchmark data (`data/` and the API
built from it) is CC0 (`data/LICENSE`). Submitting a result releases it
under CC0; the plain-English terms are in `docs/COMMUNITY_SUBMISSIONS.md`
("Your results become public data"). Blog writing in `content/` is the
author's. `build.DATA_LICENSE`, the `index.html` JSON-LD, and the license
files must agree (`test_build.check_licenses()`).

Featured picks: `data/picks.yaml` feeds the dashboard's three GPU cards.
- Slots are `amd`, `nvidia`, and `intel`. A pick needs a `note`, plus a
  `name` or a catalog `gpu_id` matching the slot's vendor.
- Affiliate `links` go to `amazon`, `newegg`, or `bestbuy`, never with
  prices.
- The `pick-*` rules live in `checks.load_picks()`.

Versions: `MAJOR.MINOR.DATA.POST`, always four parts. MAJOR is a breaking
data or API change, MINOR is any code change, DATA is newly published runs,
and POST is a new or updated post. A bump resets the parts to its right.
`RELEASE_VERSION` must equal the newest `CHANGELOG.md` release.

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
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\import_cyberpunk.py scripts\test_build.py
npm --prefix blog ci                     # Node 22.12+; once, or after the lockfile changes
npm --prefix blog run build              # after build.py; writes site/blog/
git diff --check
```

Don't commit generated `site/api/` or `site/blog/` files, `blog/node_modules/`, or `.venv/`. Create Git tags only
when asked.

## Clean up before finishing

Before you report a task complete, stop every server or background process
you started (for example the `python -m http.server 8000 --directory site`
preview or `npm --prefix blog run dev`), then run `deactivate` to leave the `.venv` virtual environment.
