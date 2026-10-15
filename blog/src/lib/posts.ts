import { getCollection, type CollectionEntry } from "astro:content";
import { POST_TYPES } from "../config";

export type Post = CollectionEntry<"posts">;

// Page paths a post slug can't take, because list pages live there.
const RESERVED_SLUGS = new Set(["tags", "_assets", "rss.xml", ...Object.values(POST_TYPES).map((t) => t.path)]);

// Published posts, newest first. Drafts show only on the dev server (`npm run
// dev`) and never build. Also enforces the rules that need the post body, not
// just its frontmatter.
export async function publishedPosts(): Promise<Post[]> {
  const posts = await getCollection("posts", (post: Post) => import.meta.env.DEV || !post.data.draft);
  for (const post of posts) {
    if (RESERVED_SLUGS.has(post.id)) {
      throw new Error(`content/posts/${post.id}/: "${post.id}" is a reserved blog path; rename the folder.`);
    }
    if (/<AffiliateLink\b/.test(post.body ?? "") && !post.data.affiliate) {
      throw new Error(
        `content/posts/${post.id}/: uses <AffiliateLink> without "affiliate: true", so the disclosure banner would be missing.`,
      );
    }
  }
  return posts.sort((a: Post, b: Post) => b.data.date.valueOf() - a.data.date.valueOf());
}

// The dashboard root for this build: "/" on Cloudflare, "/open-gpu-benchmarks/"
// on the GitHub Pages mirror. BLOG_BASE always ends in /blog.
export const siteRoot = () => import.meta.env.BASE_URL.replace(/blog\/?$/, "");

export const allTags =(posts: Post[]) => [...new Set(posts.flatMap((post) => post.data.tags))].sort();

export const postUrl =(post: Post) => `${import.meta.env.BASE_URL}${post.id}/`;

export const formatDate = (date: Date) =>
  date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });

export const isoDate = (date: Date) => date.toISOString().slice(0, 10);
