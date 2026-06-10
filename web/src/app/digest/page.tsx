import Link from "next/link";
import { getDigest, getTopics } from "@/lib/api";
import { NavBar, Button, Card } from "@/components/ui";
import { TopicCardView } from "@/components/TopicCardView";

export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

export default async function DigestPage() {
  const [digest, topics] = await Promise.all([getDigest(), getTopics()]);
  const topicById = new Map(topics.map((t) => [t.id, t]));

  return (
    <>
      <NavBar active="digest" />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Today’s Digest</h1>
          {digest && (
            <p className="mt-1 text-sm text-muted">{formatDate(digest.generated_at)}</p>
          )}
        </div>

        {!digest || digest.topic_cards.length === 0 ? (
          <Card className="text-center">
            <p className="text-sm text-muted">
              No Digest yet. Add some Topics and we’ll synthesize your first one.
            </p>
            <Link href="/topics" className="mt-4 inline-block">
              <Button>Manage Topics</Button>
            </Link>
          </Card>
        ) : (
          <div className="space-y-4">
            {digest.topic_cards.map((card) => (
              <TopicCardView
                key={card.topic_id}
                card={card}
                topic={topicById.get(card.topic_id)}
              />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
