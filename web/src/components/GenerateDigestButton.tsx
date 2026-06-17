"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { generateDigestAction } from "@/lib/actions";
import { Button } from "./ui";

// Triggers background digest generation, then polls (via router.refresh) until
// the server re-renders with cards — at which point this component unmounts.
export function GenerateDigestButton() {
  const router = useRouter();
  const [phase, setPhase] = useState<"idle" | "preparing" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function go() {
    setError(null);
    setPhase("preparing");
    const r = await generateDigestAction();
    if (!r.ok) {
      setPhase("error");
      setError(r.error);
      return;
    }
    let tries = 0;
    const poll = () => {
      tries += 1;
      router.refresh();
      if (tries < 10) setTimeout(poll, 8000);
    };
    setTimeout(poll, 8000);
  }

  if (phase === "preparing") {
    return (
      <p className="text-sm text-muted">
        Synthesizing your Digest… this takes about a minute. It’ll appear here
        automatically — or refresh the page.
      </p>
    );
  }

  return (
    <div>
      <Button onClick={go}>Generate my Digest now</Button>
      {phase === "error" && error && (
        <p className="mt-2 text-sm text-danger">{error}</p>
      )}
    </div>
  );
}
