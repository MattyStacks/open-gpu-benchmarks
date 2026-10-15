// Affiliate retailers. Keep the keys in step with checks.PICK_RETAILERS
// (the dashboard's featured picks). Programs aren't chosen yet, so no IDs are set and links
// are used exactly as written. Fill in an ID here once a program approves you.
//
// - Amazon Associates adds a `tag` query parameter to product URLs and
//   requires the exact sentence in `disclosure` wherever its links appear.
// - Newegg and Best Buy run through affiliate networks (for example Impact or
//   CJ) that hand you a full tracking URL per product. Paste that URL as the
//   href; there is no parameter to add.
export type Retailer = {
  name: string;
  queryParam?: string;
  id?: string;
  disclosure?: string;
};

export const RETAILERS = {
  amazon: {
    name: "Amazon",
    queryParam: "tag",
    id: "",
    disclosure: "As an Amazon Associate I earn from qualifying purchases.",
  },
  newegg: { name: "Newegg" },
  bestbuy: { name: "Best Buy" },
} satisfies Record<string, Retailer>;

export type RetailerKey = keyof typeof RETAILERS;

export function affiliateHref(retailer: RetailerKey, href: string): string {
  const info: Retailer = RETAILERS[retailer];
  if (!info) throw new Error(`Unknown retailer "${retailer}". Use one of: ${Object.keys(RETAILERS).join(", ")}.`);
  const url = new URL(href);
  if (url.protocol !== "https:") throw new Error(`Affiliate link must be https: ${href}`);
  if (info.queryParam && info.id && !url.searchParams.has(info.queryParam)) {
    url.searchParams.set(info.queryParam, info.id);
  }
  return url.toString();
}
