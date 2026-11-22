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

test("swapping in the recolored favicon mid-load isn't reported as a failed request", async ({ page }) => {
  // Regression for a flake seen 2026-11-22: syncFavicon() replaces the <link id="favicon"> href while
  // the browser is still loading favicons/favicon.svg, so Chromium cancels that load (net::ERR_ABORTED).
  // Hold the link's load (never syncFavicon()'s own fetch) until the swap, so the race happens every run.
  let swapped: () => void;
  const swap = new Promise<void>((resolve) => { swapped = resolve; });
  await page.route("**/favicons/favicon.svg", async (route) => {
    if (route.request().resourceType() !== "fetch") await Promise.race([swap, new Promise((r) => setTimeout(r, 5_000))]);
    await route.fallback().catch(() => { /* the browser already cancelled it */ });
  });
  await openDashboard(page);
  await expect(page.locator("#favicon")).toHaveAttribute("href", /^data:image\/svg\+xml,/);
  swapped!();
  // Let the cancelled load report back before the afterEach checks the collected problems.
  await page.waitForTimeout(500);
});

test("a missing favicon is still reported", async ({ page, problems }, testInfo) => {
  // The rule above forgives a cancelled favicon load, never a broken one.
  testInfo.annotations.push({ type: "expected-errors", description: "the 404 below is the point of the test" });
  await page.route("**/favicons/favicon.svg", (route) => route.fulfill({ status: 404, body: "gone" }));
  await openDashboard(page);
  await expect.poll(() => problems.list.join("\n"), "a favicon 404 must fail the test like any other broken asset")
    .toMatch(/HTTP 404 for .*\/favicons\/favicon\.svg/);
});
