import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test, expect, fixtureData } from "../helpers";

// The other pages: crawler tables, the license page, and (when built) the blog.

const site = join(dirname(fileURLToPath(import.meta.url)), "..", ".site");

test("benchmarks/ lists every summary without JavaScript @responsive", async ({ page }) => {
  await page.goto("./benchmarks/");
  expect(await page.locator("script").count(), "benchmarks/ is for crawlers that don't run JS: no <script> allowed").toBe(0);
  const rows = await page.locator("tbody tr").count();
  expect(rows, "one table row per dashboard summary").toBe(fixtureData().dashboard.records.length);
});

test("the license page loads @responsive", async ({ page }) => {
  await page.goto("./license/");
  await expect(page.locator("body")).toContainText("CC BY 4.0");
});

test("the blog index and first post load without errors", async ({ page }) => {
  test.skip(!existsSync(join(site, "blog", "index.html")), "site/blog isn't built; preflight builds it when blog/ or content/ change");
  await page.goto("./blog/");
  const first = page.locator("main a[href*='/blog/']").first();
  await expect(first).toBeVisible();
});
