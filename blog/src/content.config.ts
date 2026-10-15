// Every blog content rule lives here and in the components it names. A bad
// field fails `astro build` with the file and field in the message.
import { readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

// Astro runs from blog/, so the repo root is one level up.
const REPO_ROOT = resolve(process.cwd(), "..");

// Product IDs are catalog file names under data/gpus/<form_factor>/<vendor>/.
// data/gpus/reference/ holds shared chip specs, never products.
function catalogIds(): Set<string> {
  const ids = new Set<string>();
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!(dir.endsWith("gpus") && entry.name === "reference")) walk(path);
      } else if (entry.name.endsWith(".yaml")) {
        ids.add(entry.name.slice(0, -".yaml".length));
      }
    }
  };
  walk(join(REPO_ROOT, "data", "gpus"));
  return ids;
}

const GPU_IDS = catalogIds();

// YAML turns an unquoted date into a Date; the repo rule is to quote dates.
const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "quote the date as \"YYYY-MM-DD\"")
  .transform((value) => new Date(`${value}T00:00:00Z`));

const tag = z
  .string()
  .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "tags are lowercase-kebab-case");

const posts = defineCollection({
  loader: glob({
    // Relative to blog/; an absolute Windows path breaks the loader.
    base: "../content/posts",
    pattern: "*/index.{md,mdx}",
    // content/posts/<slug>/index.md -> <slug>
    generateId: ({ entry }) => entry.split("/")[0],
  }),
  schema: ({ image }) =>
    z
      .object({
        title: z.string().min(1),
        description: z.string().min(1),
        date: isoDate,
        updated: isoDate.optional(),
        type: z.enum(["post", "guide", "review"]),
        tags: z.array(tag).default([]),
        gpu_ids: z
          .array(
            z.string().refine((id) => GPU_IDS.has(id), {
              message: "not a catalog file name under data/gpus/ (reference IDs aren't products)",
            }),
          )
          .default([]),
        author: z.string().min(1).optional(),
        // true when AI wrote the post (marked in the header and footer).
        ai_generated: z.boolean().default(false),
        // What AI helped with on a human-written post, e.g. "Grammar and flow cleanup".
        ai_assistance: z.string().min(1).optional(),
        affiliate: z.boolean().default(false),
        draft: z.boolean().default(false),
        hero: image().optional(),
        hero_alt: z.string().min(1).optional(),
        // Reviews only.
        verdict: z.string().min(1).optional(),
        pros: z.array(z.string().min(1)).default([]),
        cons: z.array(z.string().min(1)).default([]),
      })
      .strict()
      .superRefine((data, ctx) => {
        if (data.hero && !data.hero_alt) {
          ctx.addIssue({ code: "custom", path: ["hero_alt"], message: "hero needs hero_alt text" });
        }
        if (data.type !== "review" && (data.verdict || data.pros.length || data.cons.length)) {
          ctx.addIssue({ code: "custom", path: ["verdict"], message: "verdict, pros, and cons are for type: review" });
        }
        if (data.type === "review" && !data.gpu_ids.length) {
          ctx.addIssue({ code: "custom", path: ["gpu_ids"], message: "a review names the reviewed product in gpu_ids" });
        }
        if (data.updated && data.updated < data.date) {
          ctx.addIssue({ code: "custom", path: ["updated"], message: "updated is before date" });
        }
      }),
});

export const collections = { posts };
