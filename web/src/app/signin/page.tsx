"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { isDemoMode } from "@/lib/demo";
import { enterDemoAction } from "@/lib/actions";
import { Button, Card, Field, IconCheck, Input, Logo } from "@/components/ui";

export default function SignInPage() {
  const demo = isDemoMode();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function sendMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setError(null);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setStatus("error");
      setError(error.message);
    } else {
      setStatus("sent");
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Logo className="justify-center" />
          <p className="mt-3 text-sm text-muted">
            Your daily AI digest of the topics you care about.
          </p>
        </div>

        <Card>
          {demo ? (
            <div className="space-y-4 text-center">
              <p className="text-sm text-muted">
                You’re viewing the <strong>demo</strong>. No account needed —
                jump straight in with seeded sample data.
              </p>
              <form action={enterDemoAction}>
                <Button type="submit" className="w-full">
                  Continue to demo
                </Button>
              </form>
            </div>
          ) : status === "sent" ? (
            <div className="space-y-3 text-center">
              <span className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-accent-soft text-accent">
                <IconCheck size={22} />
              </span>
              <p className="font-display text-lg text-foreground">
                Check your inbox
              </p>
              <p className="text-sm leading-relaxed text-muted">
                We sent a magic link to <strong>{email}</strong>. Click it to
                sign in.
              </p>
              <Button
                variant="ghost"
                className="mt-1"
                onClick={() => setStatus("idle")}
              >
                Use a different email
              </Button>
            </div>
          ) : (
            <form onSubmit={sendMagicLink} className="space-y-4">
              <Field label="Email" htmlFor="email">
                <Input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </Field>
              <Button
                type="submit"
                className="w-full"
                disabled={status === "sending"}
              >
                {status === "sending" ? "Sending…" : "Send magic link"}
              </Button>
              {error && (
                <p role="alert" className="text-sm text-danger">
                  {error}
                </p>
              )}
              <p className="text-center text-xs text-muted">
                No passwords. We’ll email you a one-time sign-in link.
              </p>
            </form>
          )}
        </Card>
      </div>
    </main>
  );
}
