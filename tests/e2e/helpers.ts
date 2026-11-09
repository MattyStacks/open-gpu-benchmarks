import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test as base, expect, type Page } from "@playwright/test";

// Shared setup for every spec. Each failure message says WHY the check exists
// and HOW to fix it, so whoever hits it (a person or an AI session) can fix the
// code instead of rediscovering the rule.

const here = dirname(fileURLToPath(import.meta.url));
// The dashboard loads ECharts from jsDelivr; tests serve the same pinned file
// from node_modules so they work offline and never flake on the CDN.
const ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js";
const echartsSource = readFileSync(join(here, "node_modules", "echarts", "dist", "echarts.min.js"), "utf-8");

type Problems = { list: string[] };

export const test = base.extend<{ problems: Problems }>({
  // Collects console errors, uncaught exceptions, failed requests, and calls to
  // other hosts; every test fails if any happened (see the afterEach below).
  problems: [async ({ page }, use) => {
    const problems: Problems = { list: [] };
    await page.route("**/*", (route) => {
      const url = route.request().url();
      if (url === ECHARTS_URL) return route.fulfill({ body: echartsSource, contentType: "application/javascript" });
      if (url.startsWith("http://127.0.0.1") || url.startsWith("data:")) return route.continue();
      problems.list.push(`request to another host: ${url} (the dashboard may only load ECharts from jsDelivr; ` +
        "add a new external script to ECHARTS-style routing in tests/e2e/helpers.ts only if it's intended)");
      return route.abort();
    });
    page.on("console", (message) => {
      if (message.type() === "error") problems.list.push(`console error: ${message.text()}`);
    });
    page.on("pageerror", (error) => problems.list.push(`uncaught exception: ${error.message}`));
    page.on("requestfailed", (request) => {
      if (!request.url().startsWith("http://127.0.0.1")) return;
      problems.list.push(`failed request: ${request.url()} (${request.failure()?.errorText})`);
    });
    page.on("response", (response) => {
      if (response.status() >= 400 && !response.url().endsWith("/favicon.ico")) {
        problems.list.push(`HTTP ${response.status()} for ${response.url()}`);
      }
    });
    await use(problems);
  }, { auto: true }],
});

test.afterEach(async ({ problems }, testInfo) => {
  if (testInfo.annotations.some((note) => note.type === "expected-errors")) return;
  expect(problems.list, "The page logged errors or made failing/external requests. A JS exception usually means a " +
    "renamed function or API field; read the first message, fix site/index.html (or build.py), and rerun " +
    "`npm --prefix tests/e2e test`.").toEqual([]);
});

export { expect };

// --- Fixture data -------------------------------------------------------------

export type Run = Record<string, unknown> & { memory_gb?: number; memory_type?: string; memory_channels?: number; os?: string };
export type DashboardRecord = {
  id: string; gpu_id: string; gpu_name: string; game_id: string; resolution: string; graphics_preset: string;
  source: string; os: string; upscaling: string; form_factor: string; testbench_memory: string; testbench_id: string;
  avg_fps: number; p1_low: number | null; run_count: number; tdp_w: number | null; proof_level: string;
  implementations: Run[]; credits: { name: string; url: string; source_url: string }[];
};
export type Dashboard = { records: DashboardRecord[]; games: { id: string; name: string; type: string; featured: boolean }[];
  graphics_presets: string[]; picks: unknown[]; metadata: Record<string, unknown> };
export type Gpu = Record<string, any> & { id: string };

let cached: { dashboard: Dashboard; gpus: Map<string, Gpu> } | undefined;

/** The fixture API, read straight from the built .site folder. */
export function fixtureData() {
  if (!cached) {
    const api = join(here, ".site", "api", "v1");
    const dashboard = JSON.parse(readFileSync(join(api, "dashboard.json"), "utf-8")) as Dashboard;
    const gpus = JSON.parse(readFileSync(join(api, "gpus.json"), "utf-8")).gpus as Gpu[];
    cached = { dashboard, gpus: new Map(gpus.map((gpu) => [gpu.id, gpu])) };
  }
  return cached;
}

/** Open the dashboard and wait until the first render finished. */
export async function openDashboard(page: Page) {
  await page.goto("./");
  await expect(page.locator("#build-version"), "the dashboard never finished loading its data").not.toHaveText(/Loading/);
  await expect(page.locator("#results-body tr").first()).toBeVisible();
}

/** The rows the table shows right now, as {header: cell text} (detail rows skipped). */
export async function tableRows(page: Page) {
  return page.evaluate(() => {
    const headers = [...document.querySelectorAll("#results-head th")].map((cell) => cell.textContent!.replace(/[▲▼↕]/g, "").trim());
    return [...document.querySelectorAll("#results-body tr.expandable")].map((row) => {
      const cells = [...row.querySelectorAll(":scope > td")];
      return { cellCount: cells.length, headerCount: headers.length,
        cells: Object.fromEntries(headers.map((header, index) => [header, (cells[index]?.textContent || "").trim()])),
        gpuId: row.querySelector(".gpu-cell .detail")?.textContent?.trim() || "",
        name: row.querySelector(".gpu-cell .name")?.textContent?.trim() || "" };
    });
  });
}

/** Pick a benchmark the way a person does: open the searchable list and click its option. */
export async function chooseGame(page: Page, gameId: string) {
  await page.locator("#game-search").click();
  await page.locator(`#game-list [role=option][data-game="${gameId}"]`).click();
}

/** The default view: the featured game (else the first "game" type entry), its first resolution, every chip on. */
export function defaultView() {
  const { dashboard } = fixtureData();
  const game = (dashboard.games.find((entry) => entry.featured) ?? dashboard.games.find((entry) => entry.type === "game"))!.id;
  const resolution = dashboard.records.find((record) => record.game_id === game)!.resolution;
  return { game, resolution };
}
