import { redirect } from "next/navigation";

// Master-prompt §4.5: /research is no longer the research page itself — it
// redirects to the genuinely separate Experimental Research experience.
export default async function ResearchRedirectPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      for (const item of value) query.append(key, item);
    } else if (value !== undefined) {
      query.append(key, value);
    }
  }
  const suffix = query.toString();
  redirect(`/research/experimental${suffix ? `?${suffix}` : ""}`);
}
