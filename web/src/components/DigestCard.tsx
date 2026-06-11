import type { ReactNode } from "react";
import type { TopicCard } from "@/lib/types";
import { Eyebrow } from "./ui";

// Presentational Topic Card — used for both the personal Digest and Trending.
// `action` is the top-right control (Refresh for personal, Follow for trending).
export function DigestCard({
  label,
  card,
  index = 0,
  action,
}: {
  label: string;
  card: Pick<TopicCard, "status" | "tldr" | "bullets" | "sources">;
  index?: number;
  action?: ReactNode;
}) {
  return (
    <article
      className="animate-rise rounded-2xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(0,0,0,0.4)] transition-colors hover:border-border-strong"
      style={{ animationDelay: `${Math.min(index, 8) * 60}ms` }}
    >
      <div className="mb-2.5 flex items-center justify-between gap-3">
        <Eyebrow>{label}</Eyebrow>
        {action}
      </div>

      {card.status === "error" || !card.tldr ? (
        <div className="rounded-lg bg-danger-soft px-4 py-3 text-sm text-danger">
          <p className="font-medium">This Topic Card couldn’t be generated.</p>
          <p className="mt-1 opacity-80">
            The rest of the Digest is unaffected — try refreshing in a moment.
          </p>
        </div>
      ) : (
        <>
          <h2 className="font-display text-[22px] font-medium leading-snug tracking-[-0.01em] text-foreground">
            {card.tldr}
          </h2>
          <ul className="mt-3.5 space-y-2">
            {card.bullets?.map((b, i) => (
              <li key={i} className="flex gap-2.5 text-[15px] leading-relaxed text-foreground/90">
                <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-accent" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
          {card.sources && card.sources.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <Eyebrow className="text-faint">Sources</Eyebrow>
              <ul className="mt-1.5 space-y-1">
                {card.sources.map((s, i) => (
                  <li key={i}>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-accent/90 underline-offset-2 hover:text-accent hover:underline"
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
    </article>
  );
}
