import rss from "@astrojs/rss";
import { BLOG_DESCRIPTION, BLOG_TITLE, SITE_URL } from "../config";
import { publishedPosts } from "../lib/posts";

// Item links use the canonical origin so feed readers dedupe across hosts.
export async function GET() {
  const posts = await publishedPosts();
  return rss({
    title: BLOG_TITLE,
    description: BLOG_DESCRIPTION,
    site: `${SITE_URL}blog/`,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.date,
      link: `${SITE_URL}blog/${post.id}/`,
      categories: [post.data.type, ...post.data.tags],
    })),
  });
}
