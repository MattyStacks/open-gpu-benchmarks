import { test, expect, fixtureData, openDashboard } from "../helpers";

// Pages the fixtures don't show on their own: no runs yet, an API outage, and
// the picks and theme toggle.

test("with no published runs the dashboard says so instead of empty filters", async ({ page }) => {
  // Real data can be a catalog with no runs (a fresh deploy): showNoBenchmarks().
  const dashboard = { ...fixtureData().dashboard, records: [] };
  await page.route("**/api/v1/dashboard.json", (route) => route.fulfill({ json: dashboard }));
  await page.goto("./");
  await expect(page.locator("#chart-empty")).toContainText("No benchmarks published yet");
  await expect(page.locator(".toolbar")).toBeHidden();
  await expect(page.locator("#error-notice")).toBeHidden();
});

test("an API failure shows the error notice", async ({ page }, testInfo) => {
  testInfo.annotations.push({ type: "expected-errors", description: "the 500 below is the point of the test" });
  await page.route("**/api/v1/dashboard.json", (route) => route.fulfill({ status: 500, body: "down" }));
  await page.goto("./");
  await expect(page.locator("#error-notice"), "initialize() must catch the failed fetch and say what to run")
    .toContainText("Unable to load benchmark data: HTTP 500");
  await expect(page.locator("#build-version")).toHaveText("Data unavailable");
});

test("featured picks: one card per maker, empty slots say coming soon, disclosure shown", async ({ page }) => {
  await openDashboard(page);
  const picks = fixtureData().dashboard.picks as { slot: string; name: string }[];
  await expect(page.locator("#pick-grid .pick")).toHaveCount(3);
  for (const slot of ["amd", "nvidia", "intel"]) {
    const pick = picks.find((item) => item.slot === slot);
    const card = page.locator(`#pick-grid .pick-${slot}`);
    if (pick) await expect(card.locator("h3")).toHaveText(pick.name);
    else await expect(card).toContainText("coming soon");
  }
  await expect(page.locator("#pick-disclosure"), "store links are affiliate links, so the disclosure must show with any pick")
    .toBeVisible();
});

test("the theme toggle flips the theme, remembers it, and recolors the favicon @responsive", async ({ page }) => {
  await openDashboard(page);
  const before = await page.evaluate(() => document.documentElement.dataset.theme);
  await page.locator("#theme-toggle").click();
  const after = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(after).not.toBe(before);
  expect(await page.evaluate(() => localStorage.getItem("open-gpu-benchmarks-theme"))).toBe(after);
  await expect(page.locator("#favicon")).toHaveAttribute("href", /^data:image\/svg\+xml,/);
  await page.reload();
  await expect(page.locator("#build-version")).not.toHaveText(/Loading/);
  expect(await page.evaluate(() => document.documentElement.dataset.theme), "the choice survives a reload").toBe(after);
});
