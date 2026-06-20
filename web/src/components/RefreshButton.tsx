"use client";

import { useState, useTransition } from "react";
import { refreshCardAction } from "@/lib/actions";
import { Button, IconRefresh } from "./ui";

export function RefreshButton({ topicId }: { topicId: string }) {
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);

  return (
    <span className="flex items-center gap-2">
      {error && <span className="font-mono text-[11px] text-danger">{error}</span>}
      <Button
        variant="ghost"
        className="gap-1.5 px-2 py-1 font-mono text-[11px] uppercase tracking-wider"
        disabled={pending}
        aria-label="Refresh card"
        onClick={() => {
          setError(null);
          start(async () => {
            const r = await refreshCardAction(topicId);
            if (!r.ok) setError(r.error);
          });
        }}
      >
        <IconRefresh size={13} className={pending ? "animate-spin" : ""} />
        {pending ? "Refreshing…" : "Refresh"}
      </Button>
    </span>
  );
}
