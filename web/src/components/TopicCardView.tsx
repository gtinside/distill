"use client";

import { useState, useTransition } from "react";
import type { Topic, TopicCard } from "@/lib/types";
import { refreshCardAction } from "@/lib/actions";
import { Button, Card } from "./ui";

function timeAgo(iso?: string | null): string | null {
  if (!iso) return null;
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  return `${hrs}h ago`;
}

export function TopicCardView({
  card,
  topic,
}: {
  card: TopicCard;
  topic?: Topic;
}) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const title = topic?.phrase ?? "Topic";

  function refresh() {
    setError(null);
    startTransition(async () => {
      const res = await refreshCardAction(card.topic_id);
      if (!res.ok) setError(res.error);
    });
  }

  const refreshed = timeAgo(card.last_refreshed_at);

  return (
    <Card className={pending ? "opacity-60 transition" : "transition"}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs font-medium uppercase tracking-wide text-muted">
          {title}
        </span>
        <div className="flex items-center gap-2">
          {refreshed && (
            <span className="text-xs text-muted">Updated {refreshed}</span>
          )}
          <Button
            variant="ghost"
            onClick={refresh}
            disabled={pending}
            className="px-2 py-1 text-xs"
            aria-label={`Refresh ${title}`}
          >
            {pending ? "Refreshing…" : "↻ Refresh"}
          </Button>
        </div>
      </div>

      {card.status === "error" ? (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-danger">
          <p className="font-medium">This Topic Card couldn’t be generated.</p>
          <p className="mt-1 text-danger/80">
            The rest of your Digest is unaffected. Try again in a moment.
          </p>
          <Button
            variant="secondary"
            onClick={refresh}
            disabled={pending}
            className="mt-3"
          >
            Retry
          </Button>
        </div>
      ) : (
        <>
          <h2 className="text-lg font-semibold leading-snug">{card.tldr}</h2>
          <ul className="mt-3 space-y-2">
            {card.bullets?.map((b, i) => (
              <li key={i} className="flex gap-2 text-sm leading-relaxed">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
          {card.sources && card.sources.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="mb-1 text-xs font-medium text-muted">Sources</p>
              <ul className="space-y-1">
                {card.sources.map((s, i) => (
                  <li key={i}>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-accent hover:underline"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
    </Card>
  );
}
