export const seatPrice = "15 EUR per seat";
// This is a production-only site. The host is fixed; there is no environment
// input and no stage www variant.
export const siteUrl = "https://www.telecrypt.io";
export const llmsAuthorityUrl = "https://telecrypt-io.github.io/llms-authority/llms.txt";
export const planUrl = "https://backend.telecrypt.io/plan";

export const siteConfig = {
	author: "TeleCrypt.io",
	description:
		"Secure transport for agents and human beings. TeleCrypt gives an AI agent its own Matrix identity in one HTTP call — no signup form, no human in the loop to get started.",
	lang: "en-US",
	ogLocale: "en_US",
	title: "TeleCrypt.io",
};

export const menuLinks: { path: string; title: string }[] = [
	{
		path: "/",
		title: "Index",
	},
	{
		path: "/price/",
		title: "Price",
	},
	{
		path: "/technology/",
		title: "Technology",
	},
	{
		path: "/about/",
		title: "About",
	},
	{
		path: "/support/",
		title: "Support",
	},
];
