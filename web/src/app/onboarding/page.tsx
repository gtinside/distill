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
import {
  Button,
  Card,
  Field,
  IconClose,
  IconPlus,
  Input,
  Logo,
} from "@/components/ui";

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
      if (res.ok) router.push("/");
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
          <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-faint">
            Step {step} of 2
          </span>
        </div>
        <div
          className="mb-6 flex gap-1.5"
          role="progressbar"
          aria-valuenow={step}
          aria-valuemin={1}
          aria-valuemax={2}
          aria-label={`Onboarding step ${step} of 2`}
        >
          {[1, 2].map((s) => (
            <span
              key={s}
              className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                s <= step ? "bg-accent" : "bg-border-strong"
              }`}
            />
          ))}
        </div>

        {step === 1 ? (
          <Card>
            <h1 className="font-display text-2xl font-medium tracking-[-0.01em]">
              What do you want to stay on top of?
            </h1>
            <p className="mt-1 text-sm text-muted">
              Add up to {TOPIC_LIMIT} topics. Be specific — “EU AI regulation”
              beats “tech”.
            </p>

            <form
              className="mt-5 flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                addTopic(draft);
              }}
            >
              <Input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                maxLength={TOPIC_MAX}
                placeholder="Type a topic…"
                disabled={atLimit}
                aria-label="Add a topic"
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
                    className="inline-flex cursor-pointer items-center gap-1 rounded-full border border-border bg-background px-3 py-1 text-xs text-muted transition-colors duration-150 hover:border-accent hover:text-foreground active:scale-[0.97]"
                  >
                    <IconPlus size={12} />
                    {ex}
                  </button>
                ))}
              </div>
            )}

            {topics.length > 0 && (
              <ul className="mt-5 space-y-2">
                {topics.map((t, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2.5 text-sm"
                  >
                    <span>{t}</span>
                    <button
                      onClick={() => setTopics(topics.filter((_, j) => j !== i))}
                      className="grid h-7 w-7 shrink-0 cursor-pointer place-items-center rounded-md text-muted transition-colors hover:bg-danger-soft hover:text-danger active:scale-95"
                      aria-label={`Remove ${t}`}
                    >
                      <IconClose size={15} />
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
            <h1 className="font-display text-2xl font-medium tracking-[-0.01em]">
              When should your Digest arrive?
            </h1>
            <p className="mt-1 text-sm text-muted">
              We’ll email your Digest each day at this time.
            </p>

            <div className="mt-5">
              <Field
                label="Delivery time"
                htmlFor="time"
                hint={
                  <>
                    Timezone detected: <strong>{timezone}</strong>
                  </>
                }
              >
                <Input
                  id="time"
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="w-auto"
                />
              </Field>
            </div>

            {error && (
              <p role="alert" className="mt-4 text-sm text-danger">
                {error}
              </p>
            )}

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
