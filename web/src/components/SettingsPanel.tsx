"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { Settings } from "@/lib/types";
import { updateSettingsAction } from "@/lib/actions";
import { isDemoMode } from "@/lib/demo";
import { createClient } from "@/lib/supabase/client";
import { Button } from "./ui";

export function SettingsPanel({ settings }: { settings: Settings }) {
  const router = useRouter();
  const [time, setTime] = useState(settings.delivery_time?.slice(0, 5) ?? "07:00");
  const [saved, setSaved] = useState(false);
  const [pending, startTransition] = useTransition();

  function save() {
    setSaved(false);
    startTransition(async () => {
      await updateSettingsAction({ delivery_time: time, timezone: settings.timezone });
      setSaved(true);
    });
  }

  async function signOut() {
    if (!isDemoMode()) {
      await createClient().auth.signOut();
    }
    router.push("/signin");
  }

  return (
    <div className="space-y-5">
      <div>
        <label htmlFor="delivery" className="mb-1 block text-sm font-medium">
          Delivery time
        </label>
        <div className="flex items-center gap-3">
          <input
            id="delivery"
            type="time"
            value={time}
            onChange={(e) => {
              setTime(e.target.value);
              setSaved(false);
            }}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <Button variant="secondary" onClick={save} disabled={pending}>
            {pending ? "Saving…" : "Save"}
          </Button>
          {saved && <span className="text-sm text-muted">Saved ✓</span>}
        </div>
        <p className="mt-2 text-xs text-muted">
          Timezone: <strong>{settings.timezone}</strong>
        </p>
      </div>

      <div className="border-t border-border pt-4">
        <Button variant="danger" onClick={signOut}>
          Sign out
        </Button>
      </div>
    </div>
  );
}
