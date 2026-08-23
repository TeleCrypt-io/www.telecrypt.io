import { unified } from "@astrojs/markdown-remark";
import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";
import rehypeExternalLinks from "rehype-external-links";

export default defineConfig({
	site: "https://www.telecrypt.io",
	output: "static",
	compressHTML: true,
	build: {
		inlineStylesheets: "always",
	},
	integrations: [sitemap()],
	markdown: {
		processor: unified({
			rehypePlugins: [
				[
					rehypeExternalLinks,
					{
						rel: ["nofollow", "noopener", "noreferrer"],
						target: "_blank",
					},
				],
			],
		}),
	},
	// https://docs.astro.build/en/guides/prefetch/
	prefetch: true,
});
