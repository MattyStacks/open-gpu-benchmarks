// Site-wide blog settings. The site version is RELEASE_VERSION in
// scripts/build.py (read from the generated API), not blog/package.json.
export const BLOG_TITLE = "Open GPU Benchmarks Blog";
export const BLOG_DESCRIPTION =
  "Posts, guides, and reviews from Open GPU Benchmarks: how the numbers are measured, what they show, and how to add your own.";
export const DEFAULT_AUTHOR = "Matt";
export const SITE_URL = "https://opengpubenchmarks.com/";
export const GITHUB_URL = "https://github.com/MattyStacks/open-gpu-benchmarks";

export const POST_TYPES = {
  post: { label: "Post", plural: "Posts", path: "posts" },
  guide: { label: "Guide", plural: "Guides", path: "guides" },
  review: { label: "Review", plural: "Reviews", path: "reviews" },
} as const;

export type PostType = keyof typeof POST_TYPES;
