"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { Settings } from "@/lib/types";
import { updateSettingsAction, exitDemoAction } from "@/lib/actions";
import { isDemoMode } from "@/lib/demo";
import { createClient } from "@/lib/supabase/client";
import { Button, Field, IconCheck, Input } from "./ui";

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
    if (isDemoMode()) {
      await exitDemoAction();
      return;
    }
    await createClient().auth.signOut();
    router.push("/signin");
  }

  return (
    <div className="space-y-5">
      <Field
        label="Delivery time"
        htmlFor="delivery"
        hint={
          <>
            Timezone: <strong>{settings.timezone}</strong>
          </>
        }
      >
        <div className="flex items-center gap-3">
          <Input
            id="delivery"
            type="time"
            value={time}
            onChange={(e) => {
              setTime(e.target.value);
              setSaved(false);
            }}
            className="w-auto"
          />
          <Button variant="secondary" onClick={save} disabled={pending}>
            {pending ? "Saving…" : "Save"}
          </Button>
          {saved && (
            <span
              role="status"
              className="inline-flex items-center gap-1 text-sm text-accent"
            >
              <IconCheck size={15} />
              Saved
            </span>
          )}
        </div>
      </Field>

      <div className="border-t border-border pt-4">
        <Button variant="danger" onClick={signOut}>
          Sign out
        </Button>
      </div>
    </div>
  );
}
