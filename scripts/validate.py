"""Check catalog entries and benchmark result files before a pull request.

    python scripts/validate.py            # everything
    python scripts/validate.py catalog    # data/gpus/** only
    python scripts/validate.py results    # data/official/** and data/community/**

Every rule lives in scripts/checks.py; build.py runs the same checks.
"""
import argparse
import sys

try:
    import yaml  # noqa: F401
except ImportError:
    print("pip install pyyaml")
    sys.exit(1)

import checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", nargs="?", default="all", choices=("all", "catalog", "results"))
    args = parser.parse_args(argv)

    catalog, catalog_issues = checks.load_catalog()
    failed = False
    if args.target in ("all", "catalog"):
        failed |= checks.report(catalog_issues, f"Catalog ({len(catalog)} entries)")
    if args.target in ("all", "results"):
        # Catalog problems are reported by the catalog check; results only need the IDs.
        runs, result_issues = checks.load_results(catalog)
        count = sum(len(items) for items in runs.values())
        failed |= checks.report(result_issues, f"Results ({count} files)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
