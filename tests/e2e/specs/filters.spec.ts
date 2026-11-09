import { test, expect, fixtureData, openDashboard, defaultView, type DashboardRecord } from "../helpers";

// Filters: each chip, button, and the search box shows exactly the records a
// plain filter over dashboard.json gives. The model below is the spec; if a test
// fails, filteredRecords() in site/index.html no longer matches it.

type View = { game: string; resolution: string; source?: string; hideOs?: string; hidePlatform?: string;
  hideUpscaling?: "native" | "upscaled"; search?: string };

const platformKey = (record: DashboardRecord) => record.form_factor !== "Desktop" ? record.form_factor
  : record.testbench_memory ? `desktop:${record.testbench_memory}` : "desktop:community";

function expectedCount(view: View) {
  return fixtureData().dashboard.records.filter((record) =>
    record.game_id === view.game && record.resolution === view.resolution
    && (!view.source || record.source === view.source)
    && record.os !== view.hideOs
    && platformKey(record) !== view.hidePlatform
    && (view.hideUpscaling !== (record.upscaling ? "upscaled" : "native"))
    && (!view.search || [record.gpu_name, record.gpu_id].some((text) => text.toLowerCase().includes(view.search!.toLowerCase())))
  ).length;
}

async function shown(page) {
  return Number(await page.locator("#result-count").textContent());
}

test("every OS, platform, and upscaling chip hides exactly its own records", async ({ page }) => {
  const view = defaultView();
  await openDashboard(page);
  expect(await shown(page), "with every chip on, the count is every record for the game and resolution").toBe(expectedCount(view));

  for (const [label, os] of [["Windows", "windows"], ["Linux", "linux"]]) {
    const chip = page.locator("#os-filters .chip", { hasText: label });
    await chip.click();
    await expect(chip).toHaveAttribute("aria-pressed", "false");
    expect(await shown(page), `turning ${label} off must hide only ${os} records (Windows and Linux never mix)`)
      .toBe(expectedCount({ ...view, hideOs: os }));
    await chip.click();
  }
  for (const [label, kind] of [["Native", "native"], ["Upscaled", "upscaled"]] as const) {
    const chip = page.locator("#upscaling-filters .chip", { hasText: label });
    await chip.click();
    expect(await shown(page), `turning ${label} off must hide only ${kind} records`).toBe(expectedCount({ ...view, hideUpscaling: kind }));
    await chip.click();
  }
  const records = fixtureData().dashboard.records;
  const platforms = [...new Set(records.map(platformKey))];
  const chips = page.locator("#factor-filters .chip");
  expect(await chips.count(), "one Platform chip per platform with records (DDR benches, community desktop, laptop, " +
    "handheld, iGPU)").toBe(platforms.length);
  for (let index = 0; index < platforms.length; index += 1) {
    const chip = chips.nth(index);
    const label = (await chip.textContent())!.trim();
    const key = platforms.find((platform) => label === ({ "desktop:community": "Desktop · community", Igpu: "iGPU" }[platform]
      ?? (platform.startsWith("desktop:") ? `${platform.slice(8)} Bench` : platform)));
    expect(key, `chip "${label}" doesn't match any platform in dashboard.json`).toBeTruthy();
    await chip.click();
    expect(await shown(page), `turning "${label}" off must hide only its records`).toBe(expectedCount({ ...view, hidePlatform: key }));
    await chip.click();
  }
});

test("the featured baseline benchmark is listed first and opens by default", async ({ page }) => {
  const featured = fixtureData().dashboard.games.filter((game) => game.featured);
  expect(featured.length, "the fixtures need exactly one featured game (featured: true in tests/fixtures/data/games.yaml) to test the default").toBe(1);
  await openDashboard(page);
  const select = page.locator("#game-select");
  await expect(select, "the baseline benchmark run on every system must be what the dashboard opens on").toHaveValue(featured[0].id);
  expect(await select.locator("option").first().getAttribute("value"), "the baseline benchmark must be the first entry in the picker")
    .toBe(featured[0].id);
  expect(await select.locator("optgroup").first().getAttribute("label"), "the baseline benchmark gets its own group at the top")
    .toBe("Baseline benchmark");
});

test("source buttons, search, game, and resolution", async ({ page }) => {
  const view = defaultView();
  await openDashboard(page);
  for (const source of ["official", "community"]) {
    await page.locator(`[data-source="${source}"]`).click();
    expect(await shown(page), `the ${source} button shows only ${source} records`).toBe(expectedCount({ ...view, source }));
  }
  await page.locator('[data-source="all"]').click();
  const target = fixtureData().dashboard.records.find((record) => record.game_id === view.game && record.resolution === view.resolution)!;
  const search = target.gpu_id.split("_")[0];
  await page.locator("#search").fill(search);
  expect(await shown(page), `searching "${search}" matches GPU names and IDs`).toBe(expectedCount({ ...view, search }));
  await page.locator("#search").fill("");

  for (const game of fixtureData().dashboard.games) {
    const resolutions = [...new Set(fixtureData().dashboard.records.filter((r) => r.game_id === game.id).map((r) => r.resolution))];
    if (!resolutions.length) continue;
    await page.locator("#game-select").selectOption(game.id);
    const options = await page.locator("#resolution-select option").allTextContents();
    expect(options, `${game.id}: the resolution menu lists exactly the resolutions that game has`).toEqual(resolutions);
    expect(await shown(page)).toBe(expectedCount({ game: game.id, resolution: resolutions[0] }));
  }
});
