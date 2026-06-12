"use client";

import { useState, useTransition } from "react";
import { followTopicAction } from "@/lib/actions";
import { Button } from "./ui";

export function FollowButton({ phrase }: { phrase: string }) {
  const [pending, start] = useTransition();
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (done) {
    return (
      <span className="font-mono text-[11px] uppercase tracking-wider text-accent">
        ✓ Following
      </span>
    );
  }

  return (
    <span className="flex items-center gap-2">
      {error && <span className="font-mono text-[11px] text-danger">{error}</span>}
      <Button
        variant="secondary"
        className="px-3 py-1 text-xs"
        disabled={pending}
        onClick={() => {
          setError(null);
          start(async () => {
            const r = await followTopicAction(phrase);
            if (r.ok) setDone(true);
            else setError(r.error);
          });
        }}
      >
        {pending ? "Following…" : "+ Follow"}
      </Button>
    </span>
  );
}
