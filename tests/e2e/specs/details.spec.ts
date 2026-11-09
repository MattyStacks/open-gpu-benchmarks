import { test, expect, fixtureData, openDashboard, chooseGame } from "../helpers";

// The expanded detail row: per-run machine details and who to credit.

async function openRecord(page, predicate: (record) => boolean, why: string) {
  const record = fixtureData().dashboard.records.find(predicate);
  expect(record, `the fixtures need a record that ${why}; add one to tests/fixtures/data`).toBeTruthy();
  await openDashboard(page);
  await chooseGame(page, record.game_id);
  await page.locator("#resolution-select").selectOption(record.resolution);
  await page.locator("#search").fill(record.gpu_id);
  const row = page.locator("#results-body tr.expandable", { hasText: record.gpu_id })
    .filter({ hasText: record.avg_fps.toFixed(1) }).first();
  await row.locator(".expander").click();
  const detail = page.locator("#results-body tr.detail-row");
  await expect(detail).toHaveCount(1);
  return { record, row, detail };
}

test("a run's system RAM shows in the run line, and the VRAM column keeps the card's VRAM", async ({ page }) => {
  // Regression for 1.10.0.0: system RAM leaked into the VRAM column.
  const { record, row, detail } = await openRecord(page,
    (r) => r.implementations.some((run) => run.memory_gb && run.memory_type && run.memory_channels === 2),
    "has a run with memory_gb, memory_type, and dual-channel memory");
  const run = record.implementations.find((item) => item.memory_gb)!;
  await expect(detail.locator(".run-list"), "formatSystemMemory() writes '<GB> GB <type> dual channel' in the run line")
    .toContainText(`${run.memory_gb} GB ${run.memory_type} dual channel`);
  const gpu = fixtureData().gpus.get(record.gpu_id)!;
  await expect(row.locator("td").nth(7), "the VRAM column (8th) shows the card's memory from gpus.json, never system RAM")
    .toHaveText(new RegExp(`^${gpu.memory.capacity_gb}GB`));
});

test("a found result credits its source with a link, plus the submitter", async ({ page }) => {
  const { record, detail } = await openRecord(page, (r) => r.credits?.length > 0, "has a credit block");
  const credit = record.credits[0];
  const run = record.implementations.find((item) => item.credit_name === credit.name)!;
  const link = detail.locator(".result-meta a", { hasText: credit.name });
  await expect(link, "the 'By' line links the credit name to credit.url (or source_url)").toHaveAttribute("href", credit.url || credit.source_url);
  if (run.submitted_by) {
    await expect(detail.locator(".result-meta"), "found results show 'Name (via @user)'").toContainText(`(via @${run.submitted_by})`);
  }
});

test("an anonymous community run says Anonymous", async ({ page }) => {
  const { detail } = await openRecord(page,
    (r) => r.source === "community" && !r.credits?.length && r.implementations.every((run) => !run.submitted_by),
    "is a community run with no credit and no submitted_by");
  await expect(detail.locator(".result-meta")).toContainText("By Anonymous");
});

test("spec sources only link https URLs", async ({ page }) => {
  const { detail } = await openRecord(page, (r) => (fixtureData().gpus.get(r.gpu_id)?.sources || []).length > 0, "has spec sources");
  const hrefs = await detail.locator("a").evaluateAll((links) => links.map((link) => link.getAttribute("href") || ""));
  for (const href of hrefs.filter((value) => /^[a-z]+:/i.test(value))) {
    expect(href, "detail links must be https:// (safeHttpsUrl); a javascript: or http: link is an XSS or mixed-content bug")
      .toMatch(/^https:\/\//);
  }
});
