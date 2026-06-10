import { createBrowserClient } from "@supabase/ssr";

// Browser-side Supabase client, used by the sign-in form to request a magic link.
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
