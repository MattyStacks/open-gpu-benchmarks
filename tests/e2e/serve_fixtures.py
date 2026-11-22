"""Build the synthetic fixtures into tests/e2e/.site and serve it for the Playwright tests.

    python tests/e2e/serve_fixtures.py [port]     # Playwright's webServer runs this

The copy holds site/'s static files (the dashboard, license page, icons) plus an
API and text pages built from tests/fixtures/data, so the browser tests never
depend on the published data and never touch site/api. A built blog
(site/blog) is copied too when it exists, for the blog smoke test.

.site/real/ is a second copy built from the published data/, for the one spec
(real_data.spec.ts) that opens every real game and resolution, so a new data
batch can't ship something the dashboard chokes on.
"""
import contextlib
import functools
import http.server
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
OUT = Path(__file__).resolve().parent / ".site"
# site/ entries build.py or Astro generate; the fixture build writes its own.
GENERATED = {"api", "benchmarks", "blog", "llms.txt", "llms-full.txt", "sitemap.xml"}

sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402


def copy_static(dest):
    dest.mkdir(parents=True)
    for entry in SITE.iterdir():
        if entry.name in GENERATED:
            continue
        if entry.is_dir():
            shutil.copytree(entry, dest / entry.name)
        else:
            shutil.copy2(entry, dest / entry.name)


def build_into(data_dir, dest, what):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = build.main(data_dir, dest / "api" / "v1", dest)
    if status:
        print(output.getvalue())
        sys.exit(f"the {what} build failed; run python scripts/validate.py to see why")


def prepare():
    shutil.rmtree(OUT, ignore_errors=True)
    copy_static(OUT)
    if (SITE / "blog").is_dir():
        shutil.copytree(SITE / "blog", OUT / "blog")
    build_into(ROOT / "tests" / "fixtures" / "data", OUT, "fixture")
    copy_static(OUT / "real")
    build_into(ROOT / "data", OUT / "real", "published data")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4173
    prepare()
    handler = functools.partial(QuietHandler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving the fixture site at http://127.0.0.1:{port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
