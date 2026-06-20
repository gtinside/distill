import type { ReactNode } from "react";
import type { TopicCard } from "@/lib/types";
import { Eyebrow, IconArrowUpRight } from "./ui";

// Guard against javascript:/data: URLs from external (Exa) source content.
function isSafeUrl(url: string): boolean {
  return /^https?:\/\//i.test((url || "").trim());
}

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
      className="animate-rise rounded-2xl border border-border bg-surface bg-[image:var(--card-grad)] p-5 shadow-[var(--shadow-card)] transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-px hover:border-border-strong hover:shadow-[var(--shadow-card-hover)] sm:p-6"
      style={{ animationDelay: `${Math.min(index, 8) * 60}ms` }}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <Eyebrow className="text-accent">{label}</Eyebrow>
        {action}
      </div>

      {card.status === "error" || !card.tldr ? (
        <div className="rounded-lg border border-danger-soft bg-danger-soft px-4 py-3 text-sm text-danger">
          <p className="font-medium">This Topic Card couldn’t be generated.</p>
          <p className="mt-1 opacity-80">
            The rest of the Digest is unaffected — try refreshing in a moment.
          </p>
        </div>
      ) : (
        <>
          <h2 className="font-display text-[1.4rem] font-medium leading-[1.3] tracking-[-0.01em] text-foreground text-balance">
            {card.tldr}
          </h2>
          <ul className="mt-4 space-y-2.5">
            {card.bullets?.map((b, i) => (
              <li
                key={i}
                className="flex gap-3 text-[15px] leading-relaxed text-foreground/90"
              >
                <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-accent" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
          {card.sources && card.sources.length > 0 && (
            <div className="mt-5 border-t border-border pt-4">
              <Eyebrow className="text-faint">Sources</Eyebrow>
              <ul className="mt-2.5 flex flex-wrap gap-2">
                {card.sources.map((s, i) => (
                  <li key={i}>
                    {isSafeUrl(s.url) ? (
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group inline-flex max-w-[18rem] items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-[13px] text-muted transition-colors duration-150 hover:border-border-strong hover:bg-surface-2 hover:text-foreground"
                      >
                        <span className="truncate">{s.title}</span>
                        <IconArrowUpRight
                          size={13}
                          className="shrink-0 text-faint transition-colors group-hover:text-accent"
                        />
                      </a>
                    ) : (
                      <span className="inline-flex max-w-[18rem] items-center rounded-full border border-border bg-background px-3 py-1.5 text-[13px] text-muted">
                        <span className="truncate">{s.title}</span>
                      </span>
                    )}
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
