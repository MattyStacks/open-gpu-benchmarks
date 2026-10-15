// The /blog/ section only. scripts/build.py owns the dashboard, the API, the
// sitemap, and the llms files; run it first so site/api/v1/ exists for charts.
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// Cloudflare (canonical) serves the blog at /blog/. The GitHub Pages mirror
// lives under /open-gpu-benchmarks/, so CI rebuilds with
// BLOG_BASE=/open-gpu-benchmarks/blog for that artifact.
const base = (process.env.BLOG_BASE || "/blog").replace(/\/+$/, "");

export default defineConfig({
  site: "https://opengpubenchmarks.com",
  base,
  trailingSlash: "always",
  outDir: "../site/blog",
  build: { format: "directory", assets: "_assets" },
  integrations: [mdx()],
});
