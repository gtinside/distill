import Link from "next/link";
import { isSignedIn } from "@/lib/auth";
import { getDigest, getTopics, getTrending } from "@/lib/api";
import type { Topic, TopicCard, TrendingCard } from "@/lib/types";
import { Button, Eyebrow, Logo, NavBar } from "@/components/ui";
import { DigestCard } from "@/components/DigestCard";
import { RefreshButton } from "@/components/RefreshButton";
import { FollowButton } from "@/components/FollowButton";
import { GenerateDigestButton } from "@/components/GenerateDigestButton";

export const dynamic = "force-dynamic";

function todayLabel(): string {
  return new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

export default async function Home() {
  const signedIn = await isSignedIn();
  const trending = await getTrending();

  if (!signedIn) return <LoggedOut trending={trending} />;

  const [digest, topics] = await Promise.all([getDigest(), getTopics()]);
  const followed = new Set(topics.map((t) => t.phrase.toLowerCase()));
  const notFollowing = trending.filter(
    (t) => !followed.has(t.phrase.toLowerCase())
  );

  return (
    <SignedIn
      cards={digest?.topic_cards ?? []}
      topics={topics}
      notFollowing={notFollowing}
    />
  );
}

// ---------------------------------------------------------------- Logged out

function LoggedOut({ trending }: { trending: TrendingCard[] }) {
  return (
    <>
      <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3.5">
          <Logo />
          <Link href="/signin">
            <Button variant="secondary">Sign in</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
        <section className="mb-10">
          <Eyebrow>Trending now</Eyebrow>
          <h1 className="mt-2 font-display text-4xl font-medium leading-[1.1] tracking-[-0.02em] text-foreground">
            Today, distilled.
          </h1>
          <p className="mt-3 max-w-md text-[15px] leading-relaxed text-muted">
            What matters across the topics people are following right now —
            synthesized into a one-glance brief.{" "}
            <Link href="/signin" className="text-accent hover:underline">
              Sign in
            </Link>{" "}
            to follow topics and get your own daily digest by email.
          </p>
        </section>

        <div className="space-y-4">
          {trending.map((card, i) => (
            <DigestCard key={card.trending_topic_id} label={card.phrase} card={card} index={i} />
          ))}
        </div>

        <div className="mt-10 rounded-2xl border border-border bg-surface p-6 text-center">
          <p className="font-display text-lg text-foreground">
            Make it yours.
          </p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-muted">
            Follow these topics, add your own, and get a personalized digest in
            your inbox every morning.
          </p>
          <Link href="/signin" className="mt-4 inline-block">
            <Button>Get your daily digest</Button>
          </Link>
        </div>
      </main>
    </>
  );
}

// ---------------------------------------------------------------- Signed in

function SignedIn({
  cards,
  topics,
  notFollowing,
}: {
  cards: TopicCard[];
  topics: Topic[];
  notFollowing: TrendingCard[];
}) {
  const phraseById = new Map(topics.map((t) => [t.id, t.phrase]));

  return (
    <>
      <NavBar active="home" />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
        <section className="mb-8">
          <div className="mb-4 flex items-baseline justify-between">
            <h1 className="font-display text-3xl font-medium tracking-[-0.01em]">
              Your Digest
            </h1>
            <Eyebrow>{todayLabel()}</Eyebrow>
          </div>

          {cards.length > 0 ? (
            <div className="space-y-4">
              {cards.map((card, i) => (
                <DigestCard
                  key={card.topic_id}
                  label={phraseById.get(card.topic_id) ?? "Topic"}
                  card={card}
                  index={i}
                  action={<RefreshButton topicId={card.topic_id} />}
                />
              ))}
            </div>
          ) : topics.length > 0 ? (
            <div className="rounded-2xl border border-border bg-surface p-6">
              <p className="text-sm text-foreground">
                You’re following{" "}
                <strong>
                  {topics.length} topic{topics.length === 1 ? "" : "s"}
                </strong>
                , but today’s Digest hasn’t been built yet.
              </p>
              <ul className="mt-3 flex flex-wrap gap-2">
                {topics.map((t) => (
                  <li
                    key={t.id}
                    className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted"
                  >
                    {t.phrase}
                  </li>
                ))}
              </ul>
              <div className="mt-5">
                <GenerateDigestButton />
              </div>
              <p className="mt-3 text-xs text-faint">
                Your Digest is also built automatically each day at your delivery
                time — change it in{" "}
                <Link href="/topics" className="text-accent hover:underline">
                  Settings
                </Link>
                .
              </p>
            </div>
          ) : (
            <div className="rounded-2xl border border-border bg-surface p-6 text-center">
              <p className="text-sm text-muted">
                You’re not following any topics yet. Follow a few trending ones
                below — or{" "}
                <Link href="/topics" className="text-accent hover:underline">
                  add your own
                </Link>
                .
              </p>
            </div>
          )}
        </section>

        {notFollowing.length > 0 && (
          <section>
            <div className="mb-4 flex items-baseline gap-3">
              <h2 className="font-display text-xl font-medium tracking-[-0.01em]">
                Trending
              </h2>
              <Eyebrow>not following</Eyebrow>
            </div>
            <div className="space-y-4">
              {notFollowing.map((card, i) => (
                <DigestCard
                  key={card.trending_topic_id}
                  label={card.phrase}
                  card={card}
                  index={i}
                  action={<FollowButton phrase={card.phrase} />}
                />
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
