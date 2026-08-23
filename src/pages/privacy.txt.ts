import { getEntry } from "astro:content";

export async function GET() {
	const entry = await getEntry("page", "privacy");
	if (!entry) return new Response("Not found\n", { status: 404 });
	return new Response(entry.body, {
		headers: { "Content-Type": "text/plain; charset=utf-8" },
	});
}
