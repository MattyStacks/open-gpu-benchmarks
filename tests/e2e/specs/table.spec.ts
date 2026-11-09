import { test, expect, fixtureData, openDashboard, tableRows, chooseGame, type DashboardRecord, type Gpu } from "../helpers";

// The summaries table: every column shows the field it's labeled with.
// Expected values are computed here from gpus.json/dashboard.json, independently
// of the dashboard's own format functions, so a mix-up in index.html shows up.

const MISSING = "—";
const spec = (gpu: Gpu | undefined, ...path: string[]) => path.reduce((value: any, key) => (value == null ? null : value[key] ?? null), gpu);
const number = (value: number) => Number(value).toLocaleString("en-US");

// {column header: expected cell text}. Keep in step with tableColumns in site/index.html.
function expectedCells(record: DashboardRecord, gpu: Gpu | undefined): Record<string, string> {
  const capacity = spec(gpu, "memory", "capacity_gb");
  const type = spec(gpu, "memory", "type");
  const bus = spec(gpu, "memory", "bus_width_bits");
  const bandwidth = spec(gpu, "memory", "bandwidth_gbs");
  const msrp = spec(gpu, "release", "msrp_usd");
  return {
    VRAM: capacity === null ? MISSING : `${capacity}GB${type ? ` ${type}` : ""}${spec(gpu, "memory", "shared") ? " (shared)" : ""}`,
    Bus: bus === null ? MISSING : `${bus}-bit`,
    Bandwidth: bandwidth === null ? MISSING : `${number(bandwidth)} GB/s`,
    TDP: record.tdp_w === null ? MISSING : `${record.tdp_w}W`,
    MSRP: msrp === null ? MISSING : `$${number(msrp)}`,
    Release: spec(gpu, "release", "date") || MISSING,
    "Avg FPS": record.avg_fps.toFixed(1),
    "1% low": record.p1_low === null ? MISSING : record.p1_low.toFixed(1),
    Samples: String(record.run_count || 1),
  };
}

test("every column shows its own field, for every game and resolution", async ({ page }) => {
  // Regression: 1.10.0.0 fixed the VRAM column showing the test system's RAM,
  // because two functions were both named formatMemory. If a cell here is wrong,
  // look for the format function that column calls in renderTable().
  const { dashboard, gpus } = fixtureData();
  await openDashboard(page);
  let checked = 0;
  for (const game of dashboard.games) {
    const resolutions = [...new Set(dashboard.records.filter((r) => r.game_id === game.id).map((r) => r.resolution))];
    if (!resolutions.length) continue;
    await chooseGame(page, game.id);
    for (const resolution of resolutions) {
      await page.locator("#resolution-select").selectOption(resolution);
      const rows = await tableRows(page);
      const expected = dashboard.records.filter((r) => r.game_id === game.id && r.resolution === resolution);
      expect(rows.length, `${game.id} ${resolution}: the table shows ${rows.length} rows, dashboard.json has ` +
        `${expected.length}; with every chip on, no record may be filtered out`).toBe(expected.length);
      for (const row of rows) {
        expect(row.cellCount, "a row has a different number of cells than the header has columns: tableColumns and " +
          "the <td> template in renderTable() (site/index.html) must change together").toBe(row.headerCount);
        const record = expected.find((r) => r.gpu_id === row.gpuId && r.avg_fps.toFixed(1) === row.cells["Avg FPS"])!;
        expect(record, `no record matches the row ${row.gpuId} ${row.cells["Avg FPS"]}`).toBeTruthy();
        expect(row.name, "the GPU column shows gpu_name").toBe(record.gpu_name);
        for (const [header, value] of Object.entries(expectedCells(record, gpus.get(record.gpu_id)))) {
          expect(row.cells[header], `${record.gpu_id} (${game.id} ${resolution}): the ${header} column shows the wrong ` +
            `value; check the function renderTable() calls for ${header}`).toBe(value);
        }
        checked += 1;
      }
    }
  }
  expect(checked).toBe(dashboard.records.length);
});

test("sorting: a column click sorts numerically, a second click reverses, missing values last", async ({ page }) => {
  await openDashboard(page);
  const fps = async () => (await tableRows(page)).map((row) => Number(row.cells["Avg FPS"]));
  const initial = await fps();
  expect(initial, "the table starts sorted by Avg FPS, fastest first").toEqual([...initial].sort((a, b) => b - a));
  await page.getByRole("button", { name: "Sort by Avg FPS" }).click();
  expect(await fps(), "a second click on the active column flips the direction").toEqual([...initial].sort((a, b) => a - b));

  await page.getByRole("button", { name: "Sort by VRAM" }).click();
  const vram = (await tableRows(page)).map((row) => row.cells.VRAM);
  const numbers = vram.filter((cell) => cell !== MISSING).map((cell) => parseFloat(cell));
  expect(numbers, "VRAM sorts by the number, largest first (a text sort would put 8GB above 24GB)")
    .toEqual([...numbers].sort((a, b) => b - a));
  expect(vram.slice(numbers.length).every((cell) => cell === MISSING), "rows without a value sort last").toBe(true);
});
