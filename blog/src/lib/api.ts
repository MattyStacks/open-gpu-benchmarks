// Build-time access to the API that scripts/build.py writes. The blog never
// computes benchmark numbers itself; it only reads the published summaries.
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const API_DIR = resolve(process.cwd(), "..", "site", "api", "v1");

export type SummaryRecord = {
  id: string;
  source: "official" | "community";
  gpu_id: string;
  gpu_name: string;
  gpu_vendor: string;
  // The registry ID from data/games.yaml; game is its display name.
  game_id: string;
  game: string;
  game_type: "game" | "synthetic" | "engine_demo";
  game_year: number | null;
  resolution: string;
  graphics_preset: string;
  upscaling: string;
  os: string;
  // Official desktop runs only; "" otherwise. One GPU on two benches is two summaries.
  testbench_id: string;
  // The bench's memory type ("DDR5") and label ("DDR5 Bench").
  testbench_memory: string;
  testbench_label: string;
  avg_fps: number;
  p1_low: number | null;
  run_count: number;
};

export type DashboardGame = { id: string; name: string; type: SummaryRecord["game_type"]; year: number };

export type Dashboard = {
  metadata: { release_version: string; schema_version: string; generated_at: string };
  games: DashboardGame[];
  records: SummaryRecord[];
};

export type CatalogGpu = {
  id: string;
  identity: { name: string; gpu_vendor: string; board_partner?: string; codename?: string };
  classification: { form_factor: string; architecture?: string };
  memory: { capacity_gb: number; type?: string; bus_width_bits?: number; bandwidth_gbs?: number };
  silicon?: { shader_cores?: number; rt_cores?: number; process?: string };
  clocks?: { base_mhz?: number; boost_mhz?: number };
  power?: { tdp_w?: number };
  release?: { date?: string; msrp_usd?: number };
};

const cache = new Map<string, unknown>();

function readApi<T>(name: string): T {
  if (!cache.has(name)) {
    const path = join(API_DIR, name);
    if (!existsSync(path)) {
      throw new Error(`${path} is missing. Run "python scripts/build.py" before building the blog.`);
    }
    cache.set(name, JSON.parse(readFileSync(path, "utf8")));
  }
  return cache.get(name) as T;
}

export const dashboard = () => readApi<Dashboard>("dashboard.json");

export function catalogGpu(id: string): CatalogGpu {
  const gpu = readApi<{ gpus: CatalogGpu[] }>("gpus.json").gpus.find((item) => item.id === id);
  if (!gpu) throw new Error(`GPU "${id}" is not in site/api/v1/gpus.json.`);
  return gpu;
}

// "cyberpunk_2077", "Cyberpunk 2077", and "cyberpunk-2077" all match.
export const normalize = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, "");
