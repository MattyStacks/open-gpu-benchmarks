import { test, expect, openDashboard } from "../helpers";

// The dashboard's pure helpers, called directly in the page (they're globals
// in site/index.html). Fast to run and precise about which function broke.

test("pure dashboard helpers", async ({ page }) => {
  await openDashboard(page);
  const results = await page.evaluate(() => {
    const g = globalThis as any;
    const record = (overrides) => ({ gpu_id: "x", gpu_name: "GPU X", os: "windows", graphics_preset: "High",
      upscaling: "", form_factor: "Desktop", testbench_memory: "DDR5", testbench_id: "bench", testbench_label: "DDR5 Bench",
      testbench_name: "Bench", ...overrides });
    return {
      formatSystemMemory: [
        g.formatSystemMemory({ memory_gb: 64, memory_type: "DDR5-6000", memory_channels: 2 }),
        g.formatSystemMemory({ memory_gb: 16, memory_channels: 8 }),
        g.formatSystemMemory({}),
      ],
      upscalerFamily: ["", "DLSS Quality", "DLAA", "FSR 2.1 Balanced", "XeSS (mode 1)", "Dynamic resolution"]
        .map((upscaling) => g.upscalerFamily({ upscaling })),
      safeHttpsUrl: ["https://example.com/a", "http://example.com", "javascript:alert(1)", "not a url"].map(g.safeHttpsUrl),
      escapeHtml: g.escapeHtml(`<a href="x">'&'</a>`),
      platformKey: [record({}), record({ testbench_memory: "" }), record({ form_factor: "Laptop" })].map(g.platformKey),
      platformLabel: ["desktop:DDR4", "desktop:community", "Igpu"].map(g.platformLabel),
      formatRange: [g.formatRange([70, 72], "FPS"), g.formatRange([60, 60], "FPS"), g.formatRange(null, "FPS")],
      displayName: (() => {
        const windows = record({});
        const linux = record({ os: "linux" });
        const other = record({ gpu_id: "y", gpu_name: "GPU Y", graphics_preset: "Ultra" });
        return [g.displayName(windows, [windows, linux]), g.displayName(linux, [windows, linux]), g.displayName(windows, [windows, other])];
      })(),
    };
  });
  expect(results.formatSystemMemory, "system RAM reads '<GB> GB <type> <channels>' and skips missing parts")
    .toEqual(["64 GB DDR5-6000 dual channel", "16 GB 8-channel", ""]);
  expect(results.upscalerFamily, "the pill color family follows the upscaler's maker")
    .toEqual(["native", "dlss", "dlss", "fsr", "xess", "upscaled"]);
  expect(results.safeHttpsUrl, "only https URLs may become links").toEqual(["https://example.com/a", null, null, null]);
  expect(results.escapeHtml).toBe("&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;");
  expect(results.platformKey).toEqual(["desktop:DDR5", "desktop:community", "Laptop"]);
  expect(results.platformLabel).toEqual(["DDR4 Bench", "Desktop · community", "iGPU"]);
  expect(results.formatRange).toEqual(["70.0–72.0 FPS", "60.0 FPS", "—"]);
  expect(results.displayName, "labels add the OS only when both OSes are shown, and the preset only when presets differ")
    .toEqual(["GPU X · Windows", "GPU X · Linux", "GPU X · High"]);
});
