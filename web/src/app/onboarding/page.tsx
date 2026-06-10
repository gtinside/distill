"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  EXAMPLE_TOPICS,
  TOPIC_LIMIT,
  TOPIC_MAX,
  TOPIC_MIN,
} from "@/lib/types";
import { completeOnboardingAction } from "@/lib/actions";
import { Button, Card, Logo } from "@/components/ui";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [topics, setTopics] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [time, setTime] = useState("07:00");
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const timezone = useMemo(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    []
  );

  const draftValid =
    draft.trim().length >= TOPIC_MIN && draft.trim().length <= TOPIC_MAX;
  const atLimit = topics.length >= TOPIC_LIMIT;

  function addTopic(phrase: string) {
    const t = phrase.trim();
    if (t.length < TOPIC_MIN || t.length > TOPIC_MAX) return;
    if (atLimit) return;
    if (topics.some((x) => x.toLowerCase() === t.toLowerCase())) return;
    setTopics((prev) => [...prev, t]);
    setDraft("");
  }

  function finish() {
    setError(null);
    startTransition(async () => {
      const res = await completeOnboardingAction(topics, time, timezone);
      if (res.ok) router.push("/digest");
      else setError(res.error);
    });
  }

  const remainingExamples = EXAMPLE_TOPICS.filter(
    (e) => !topics.some((t) => t.toLowerCase() === e.toLowerCase())
  );

  return (
    <main className="flex flex-1 items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-6 flex items-center justify-between">
          <Logo />
          <span className="text-xs text-muted">Step {step} of 2</span>
        </div>

        {step === 1 ? (
          <Card>
            <h1 className="text-xl font-semibold">What do you want to stay on top of?</h1>
            <p className="mt-1 text-sm text-muted">
              Add up to {TOPIC_LIMIT} topics. Be specific — “EU AI regulation”
              beats “tech”.
            </p>

            <form
              className="mt-4 flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                addTopic(draft);
              }}
            >
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                maxLength={TOPIC_MAX}
                placeholder="Type a topic…"
                disabled={atLimit}
                className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent disabled:opacity-50"
              />
              <Button type="submit" disabled={!draftValid || atLimit}>
                Add
              </Button>
            </form>

            {remainingExamples.length > 0 && !atLimit && (
              <div className="mt-3 flex flex-wrap gap-2">
                {remainingExamples.slice(0, 6).map((ex) => (
                  <button
                    key={ex}
                    onClick={() => addTopic(ex)}
                    className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted transition hover:border-accent hover:text-foreground"
                  >
                    + {ex}
                  </button>
                ))}
              </div>
            )}

            {topics.length > 0 && (
              <ul className="mt-4 space-y-2">
                {topics.map((t, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-sm"
                  >
                    <span>{t}</span>
                    <button
                      onClick={() => setTopics(topics.filter((_, j) => j !== i))}
                      className="text-muted hover:text-danger"
                      aria-label={`Remove ${t}`}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-6 flex justify-end">
              <Button disabled={topics.length === 0} onClick={() => setStep(2)}>
                Continue
              </Button>
            </div>
          </Card>
        ) : (
          <Card>
            <h1 className="text-xl font-semibold">When should your Digest arrive?</h1>
            <p className="mt-1 text-sm text-muted">
              We’ll email your Digest each day at this time.
            </p>

            <div className="mt-5 space-y-4">
              <div>
                <label htmlFor="time" className="mb-1 block text-sm font-medium">
                  Delivery time
                </label>
                <input
                  id="time"
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </div>
              <p className="text-xs text-muted">
                Timezone detected: <strong>{timezone}</strong>
              </p>
            </div>

            {error && <p className="mt-4 text-sm text-danger">{error}</p>}

            <div className="mt-6 flex items-center justify-between">
              <Button variant="ghost" onClick={() => setStep(1)} disabled={pending}>
                Back
              </Button>
              <Button onClick={finish} disabled={pending}>
                {pending ? "Building your first Digest…" : "Finish"}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </main>
  );
}
