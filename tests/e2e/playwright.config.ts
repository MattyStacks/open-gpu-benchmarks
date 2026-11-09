import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

// Browser regression tests for the dashboard, against the synthetic fixtures
// (tests/fixtures/data). serve_fixtures.py builds them into tests/e2e/.site.
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const venvPython = process.platform === "win32" ? join(root, ".venv", "Scripts", "python.exe") : join(root, ".venv", "bin", "python");
const python = process.env.PYTHON || (existsSync(venvPython) ? venvPython : process.platform === "win32" ? "python" : "python3");
const port = Number(process.env.E2E_PORT || 4173);

export default defineConfig({
  testDir: "./specs",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["line"], ["html", { open: "never" }]] : [["line"]],
  timeout: 30_000,
  use: {
    baseURL: `http://127.0.0.1:${port}/`,
    trace: "retain-on-failure",
    browserName: "chromium",
  },
  projects: [
    // Every spec runs on a dark desktop; the @responsive ones also run in the
    // light theme and at phone width.
    { name: "desktop", use: { viewport: { width: 1280, height: 900 }, colorScheme: "dark" } },
    { name: "desktop-light", grep: /@responsive/, use: { viewport: { width: 1280, height: 900 }, colorScheme: "light" } },
    { name: "phone", grep: /@responsive/, use: { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, colorScheme: "dark" } },
  ],
  webServer: {
    command: `"${python}" serve_fixtures.py ${port}`,
    cwd: here,
    url: `http://127.0.0.1:${port}/api/v1/dashboard.json`,
    reuseExistingServer: false,
    timeout: 60_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});
