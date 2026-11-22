import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect, chooseGame, type Dashboard } from "../helpers";

// Every other spec runs on the synthetic fixtures. This one opens the published
// data/ (serve_fixtures.py builds it into .site/real) at every game and
// resolution and expands every row, so a new data batch (a new game, a new
// upscaler label, an odd system field) can't ship a view that throws, logs an
// error, or draws nothing. The problems collector in helpers.ts fails the test
// on any console error, exception, failed request, or HTTP error.

const here = dirname(fileURLToPath(import.meta.url));
const real = JSON.parse(readFileSync(join(here, "..", ".site", "real", "api", "v1", "dashboard.json"), "utf-8")) as Dashboard;

test("every published game and resolution renders, and every row's details open", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("real/");
  await expect(page.locator("#build-version"), "the dashboard never finished loading the published data").not.toHaveText(/Loading/);
  await expect(page.locator("#error-notice")).toBeHidden();
  for (const game of real.games) {
    const resolutions = [...new Set(real.records.filter((record) => record.game_id === game.id).map((record) => record.resolution))];
    expect(resolutions.length, `games.yaml lists ${game.id} but no run uses it, so the picker offers an empty game`)
      .toBeGreaterThan(0);
    await chooseGame(page, game.id);
    for (const resolution of resolutions) {
      const view = `${game.id} at ${resolution}`;
      await page.locator("#resolution-select").selectOption(resolution);
      const rows = page.locator("#results-body tr.expandable");
      await expect(rows.first(), `${view}: the table is empty although data/ has runs for it; a filter or a ` +
        "grouping key probably drops them").toBeVisible();
      await expect(page.locator("#chart canvas"), `${view}: no chart was drawn`).toHaveCount(1);
      // Open and close each row inside the page (hundreds of rows; a Playwright click each takes ~40 s).
      const unopened = await page.evaluate(() => {
        const expanders = () => [...document.querySelectorAll<HTMLButtonElement>("#results-body tr.expandable .expander")];
        const failed: number[] = [];
        for (let index = 0; index < expanders().length; index++) {
          expanders()[index].click();
          if (document.querySelectorAll("#results-body tr.detail-row").length !== 1) failed.push(index + 1);
          expanders()[index].click();
        }
        return failed;
      });
      expect(unopened, `${view}: these rows' details didn't open (the problems list above names any exception)`)
        .toEqual([]);
    }
  }
});
