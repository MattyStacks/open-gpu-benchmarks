import { test, expect, fixtureData, openDashboard, defaultView, tableRows } from "../helpers";

// The chart and the comparison box agree with the table.

test("the chart has one bar per table row, in the same order", async ({ page }) => {
  await openDashboard(page);
  const rows = await tableRows(page);
  // `chart` is the dashboard's top-level `let` ECharts instance; globalThis.chart would be the #chart element.
  const bars = await page.evaluate(() => {
    const option = (0, eval)("chart").getOption();
    return { avg: option.series[0].data.map((item) => item.value), labels: option.yAxis[0].data.length };
  });
  expect(bars.labels, "one y-axis label per filtered record").toBe(rows.length);
  expect(bars.avg.map((value) => Number(value).toFixed(1)), "the Avg FPS bars follow the table's order")
    .toEqual(rows.map((row) => row.cells["Avg FPS"]));
});

test("turning off Avg FPS leaves only the 1% low series", async ({ page }) => {
  await openDashboard(page);
  await page.locator("#avg-toggle").uncheck();
  const names = await page.evaluate(() => (0, eval)("chart").getOption().series.map((series) => series.name));
  expect(names).toEqual(["1% Low"]);
});

test("selecting two GPUs shows the percentage comparison", async ({ page }) => {
  await openDashboard(page);
  // Compare within the default game's busiest resolution, so the test doesn't depend on how many rows its first one has.
  const { game } = defaultView();
  const counts = new Map<string, number>();
  for (const record of fixtureData().dashboard.records.filter((r) => r.game_id === game)) {
    counts.set(record.resolution, (counts.get(record.resolution) ?? 0) + 1);
  }
  const [resolution] = [...counts].sort((a, b) => b[1] - a[1])[0];
  await page.locator("#resolution-select").selectOption(resolution);
  const boxes = page.locator("#results-body tr.expandable input[type=checkbox]");
  expect(await boxes.count(), `the fixtures need at least two ${game} rows at ${resolution} to compare`).toBeGreaterThanOrEqual(2);
  await boxes.nth(0).check();
  await page.locator("#results-body tr.expandable input[type=checkbox]").nth(1).check();
  await expect(page.locator("#selection-count")).toHaveText("2");
  await expect(page.locator("#comparison")).toBeVisible();
  await expect(page.locator("#comparison-text"), "renderComparison() says '<A> is N% ahead of <B> (x vs y FPS).'")
    .toHaveText(/ is \d+% ahead of .+ \(\d+\.\d vs \d+\.\d FPS\)\.$/);
});
