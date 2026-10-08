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
  contract, and fixture counts.
- [data/gpus/README.md](data/gpus/README.md): the catalog layout, ID rules, and
  every check rule.
- [CONTRIBUTING.md](CONTRIBUTING.md) and
  [docs/COMMUNITY_SUBMISSIONS.md](docs/COMMUNITY_SUBMISSIONS.md): the
  submission rules.

When a rule changes, change it in every file that states it.

Results: game runs require `system.os`: `windows` or `linux`, lowercase. The OS is a
grouping key, so Windows and Linux runs are never averaged together; the
distro, kernel, Mesa, and Proton are per-run detail fields, never grouping
keys or extra chart bars. Linux-only fields on a windows run (or the
reverse) are errors. Per-distro comparisons are DIY from the JSON.

Catalog data must be accurate. Cite real pages in `sources`, list in
`covers` only the sections a page backs, and leave a value out rather than
guess it.

## Checks to run before finishing

```powershell
python -m pip install pyyaml numpy
python scripts/validate.py
python scripts/build.py
python scripts/test_build.py
python -m py_compile scripts\checks.py scripts\build.py scripts\validate.py scripts\parse.py scripts\test_build.py
git diff --check
```

Don't commit generated `site/api/` files. Create Git tags only when asked.
