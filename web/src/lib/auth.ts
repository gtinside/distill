import "server-only";
import { cookies } from "next/headers";
import { DEMO_COOKIE, isDemoMode } from "./demo";
import { createClient } from "./supabase/server";

// Is the current visitor signed in? In demo mode this is a cookie set by the
// "Continue to demo" button; otherwise it's a real Supabase session.
export async function isSignedIn(): Promise<boolean> {
  if (isDemoMode()) {
    const store = await cookies();
    return store.get(DEMO_COOKIE)?.value === "1";
  }
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return !!user;
}
