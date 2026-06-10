import { redirect } from "next/navigation";
import { getTopics } from "@/lib/api";

// Entry point: route the user to onboarding (no topics yet) or their Digest.
// Unauthenticated users are bounced to /signin by middleware before reaching here.
export default async function Home() {
  const topics = await getTopics();
  if (topics.length === 0) redirect("/onboarding");
  redirect("/digest");
}
