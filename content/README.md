# Blog content

Posts, guides, and reviews for <https://opengpubenchmarks.com/blog/>. Each
entry is one folder:

```text
content/posts/<slug>/index.md     plain Markdown
content/posts/<slug>/index.mdx    Markdown plus components (charts, callouts, affiliate links)
content/posts/<slug>/*.png|jpg    images used by that post
```

The folder name is the URL: `content/posts/rtx-5080-review/` is
`/blog/rtx-5080-review/`. Use lowercase words joined by hyphens. `tags`,
`posts`, `guides`, and `reviews` are reserved.

Astro (in `blog/`) builds the pages. See [Previewing](#previewing).

## Frontmatter

Block-style YAML, with every date quoted:

```yaml
---
title: "RTX 5080 Founders Edition review"
description: "One or two sentences for the post list, search results, and social cards."
date: "2026-10-20"
updated: "2026-11-02"          # optional; set it when you change a published post
type: review                   # post, guide, or review
tags:
  - rtx-5080
  - cyberpunk-2077
gpu_ids:                       # catalog IDs (file names under data/gpus/); required for reviews
  - rtx_5080_16gb_fe
ai_assistance: "Grammar and flow cleanup"   # optional: what AI helped with, shown in the footer
ai_generated: false            # true only when AI wrote the post; adds an "AI-generated" pill
affiliate: false               # true adds the disclosure banner; required for <AffiliateLink>
draft: true                    # only the dev server shows drafts; they never build or reach the sitemap
hero: ./hero.jpg               # optional image at the top, optimized at build
hero_alt: "The card on a test bench"
verdict: "..."                 # reviews only
pros:
  - "..."
cons:
  - "..."
---
```

Required: `title`, `description`, `date`, and `type`. Tags are
lowercase-kebab-case. An unknown field, an unquoted date, or a `gpu_ids`
entry that isn't a catalog product fails the build, and the error names the
field.

## Images

Put images next to `index.md` and reference them relatively:
`![Alt text](./capture.png)`. The build resizes them, converts them to WebP,
and sets their width and height. Always write alt text. Strip personal data
(PC names, usernames, file paths) from screenshots.

## Components (`.mdx` only)

Rename the file to `index.mdx` to use these. You don't import them.

**`<BenchChart>`** draws a chart from the published benchmark summaries, so
the numbers always match the dashboard:

```mdx
<BenchChart gpu="rtx_5080_16gb_fe" game="cyberpunk_2077" resolution="1440p" />
<BenchChart gpu={["rtx_5080_16gb_fe", "rtx_4090_24gb_fe"]} game="cyberpunk_2077" resolution="4K" preset="Ray Tracing: Ultra" />
```

- `gpu` is one catalog ID or a list.
- `game` is the game's exact ID in `data/games.yaml`, such as
  `cyberpunk_2077`. The display name comes from there too.
- The optional filters are `resolution`, `preset`, and `os` (`windows` or
  `linux`), plus `source`: `official` (the default), `community`, or `all`.
- `title` overrides the heading.

The build fails if nothing matches, so a typo can't publish an empty chart.

**`<Callout>`** is a banner:

```mdx
<Callout type="warning" title="Driver note">Results before driver 617 used a different preset.</Callout>
```

The types are `note` (the default), `tip`, and `warning`.

**`<AffiliateLink>`** is a store link:

```mdx
<AffiliateLink retailer="amazon" href="https://www.amazon.com/dp/...">RTX 5080 Founders Edition</AffiliateLink>
```

- `retailer` is `amazon`, `newegg`, or `bestbuy`.
- The link gets `rel="sponsored nofollow"` and an "affiliate" badge.
- A post that uses it must set `affiliate: true`. That adds the disclosure
  banner at the top, and the build fails without it.
- Retailer IDs live in `blog/src/data/retailers.ts`. For Newegg and Best Buy,
  paste the network's full tracking URL as `href`.

## Writing and AI cleanup

The author writes every post, review, and guide. AI may clean up wording and
insert affiliate links. Say what it did in `ai_assistance`, such as
"Grammar and flow cleanup". A post AI wrote (rare, for example a simple
tutorial) sets `ai_generated: true`, and the page says so.

The author keeps the copyright to their writing, all rights reserved, the same
as anything they publish elsewhere. Posts aren't under the data's CC BY 4.0 or
the code's MIT license. Every post ends with "Text © <year> <author>. All
rights reserved." A post with `ai_generated: true` instead says no copyright is
claimed in its text, because fully AI-written text has no human author. The
benchmark charts in a post come from the CC BY 4.0 data either way.

Rules for anyone (person or AI) editing a post:

- Keep the author's voice, opinions, and claims. Fix grammar, clarity, and
  structure. Don't add opinions or experiences.
- Never type benchmark numbers by hand. Use `<BenchChart>`, or link the
  dashboard, so numbers always come from published data.
- Add store links only with `<AffiliateLink>`, and set `affiliate: true`.
- Example names and links use made-up names and `example.com`, never a real
  creator or channel.

## Publishing

1. Set `draft: false`.
2. Bump the POST part of `RELEASE_VERSION` in `scripts/build.py`, for example
   `1.1.0.0` to `1.1.0.1`.
3. Add a `CHANGELOG.md` release such as `## 1.1.0.1 - <date>` with
   "New post: <title>".
4. Open a pull request. The **Blog** check builds the site.

Small fixes such as typos don't need a version bump. A material update
(new section, new data, changed verdict) sets `updated` and bumps POST.

## Previewing

From the repo root, with the `.venv` active:

```powershell
python scripts/build.py              # writes site/api/v1, which charts read
npm --prefix blog ci                 # once, or after blog/package-lock.json changes
npm --prefix blog run dev            # http://localhost:4321/blog/, live reload, drafts shown
npm --prefix blog run build          # writes site/blog/
python -m http.server 8000 --directory site   # http://localhost:8000/blog/
```
