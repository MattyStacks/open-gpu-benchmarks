import { test, expect, fixtureData, openDashboard } from "../helpers";

// The page loads without errors and shows what the API says. Tagged @responsive:
// runs on desktop dark, desktop light, and phone.

test("dashboard loads with no errors and shows the build version @responsive", async ({ page }) => {
  const { metadata } = fixtureData().dashboard;
  await openDashboard(page);
  await expect(page.locator("#build-version"), "the header shows v<release_version> · <commit> from dashboard.json metadata")
    .toHaveText(`v${metadata.release_version} · ${metadata.commit}`);
  await expect(page.locator("#schema-version")).toHaveText(`schema v${metadata.schema_version}`);
  await expect(page.locator("#synthetic-note"), "fixture data is synthetic, so the 'Synthetic scaffold data' note must show")
    .toBeVisible();
  await expect(page.locator("#error-notice")).toBeHidden();
  await expect(page.locator("#chart canvas"), "ECharts draws into a <canvas>; none means renderChart() failed").toHaveCount(1);
});

test("no horizontal scrolling with every panel open @responsive", async ({ page }) => {
  // Regression: 1.2.0.0 fixed code blocks and grids spilling past the phone
  // screen (grid tracks need minmax(0,1fr), children min-width:0). A wider
  // page means a new element doesn't shrink: give it min-width:0 or let it
  // scroll inside its own box (overflow-x:auto).
  await openDashboard(page);
  await page.locator(".submission-toggle").click();
  await page.locator("#results-body tr.expandable .expander").first().click();
  await expect(page.locator("#results-body tr.detail-row")).toHaveCount(1);
  const widths = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  expect(widths.page, `the page is ${widths.page}px wide in a ${widths.viewport}px viewport; find the overflowing ` +
    "element with DevTools and give it min-width:0 / overflow-x:auto").toBeLessThanOrEqual(widths.viewport);
  // A panel with overflow:hidden hides the spill from scrollWidth, so also check
  // that nothing sticks out of its panel unless it's inside its own scroll box.
  const spills = await page.evaluate(() => {
    const scrolls = (element: Element) => ["auto", "scroll"].includes(getComputedStyle(element).overflowX);
    const found: string[] = [];
    document.querySelectorAll(".panel").forEach((panel) => {
      const edge = Math.min(panel.getBoundingClientRect().right, window.innerWidth) + 1;
      panel.querySelectorAll("*").forEach((element) => {
        const rect = element.getBoundingClientRect();
        if (!rect.width || rect.right <= edge) return;
        for (let parent = element.parentElement; parent && parent !== panel; parent = parent.parentElement) {
          if (scrolls(parent)) return;
        }
        if (scrolls(element)) return;
        found.push(`${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ""}.${[...element.classList].join(".")} ` +
          `ends at ${Math.round(rect.right)}px, past its panel/screen edge at ${Math.round(edge)}px`);
      });
    });
    return found.slice(0, 10);
  });
  expect(spills, "these elements spill out of their panel; give the element (or its grid track) min-width:0 / " +
    "minmax(0,1fr), or wrap it in a box with overflow-x:auto").toEqual([]);
});
