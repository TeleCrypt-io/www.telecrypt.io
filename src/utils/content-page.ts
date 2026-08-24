import { getEntry, render } from "astro:content";
import { siteConfig } from "@/site-config";

type ContentPageSlug = "about" | "privacy" | "technology";

export async function loadPage(
	slug: ContentPageSlug,
	fallbackDescription = siteConfig.description,
) {
	const entry = await getEntry("page", slug);
	if (!entry) throw new Error(`Missing src/content/page/${slug}.md`);

	const { Content } = await render(entry);
	return {
		Content,
		meta: {
			description: entry.data.description ?? fallbackDescription,
			title: entry.data.title,
		},
	};
}
