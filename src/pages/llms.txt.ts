import { planUrl, seatPrice } from "@/site-config";
import llmsTemplate from "../content/llms.txt?raw";

export function GET() {
	const body = llmsTemplate
		.replaceAll("{{PLAN_URL}}", planUrl)
		.replaceAll("{{SEAT_PRICE}}", seatPrice);
	return new Response(body, {
		headers: { "Content-Type": "text/plain; charset=utf-8" },
	});
}
