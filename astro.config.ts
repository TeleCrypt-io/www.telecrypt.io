import { unified } from "@astrojs/markdown-remark";
import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";
import rehypeExternalLinks from "rehype-external-links";
import { siteUrl } from "./src/site.config";

export default defineConfig({
	site: siteUrl,
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
});
