// Demo mode: a self-contained in-memory backend so the whole app runs locally
// (and on a Vercel preview) with zero Supabase/FastAPI/Resend configuration.
// Toggled by NEXT_PUBLIC_DEMO_MODE. Mutations persist for the life of the
// server process — enough for local use, demos, and screenshots.

import type { Digest, Settings, Topic } from "./types";

export function isDemoMode(): boolean {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") return true;
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "false") return false;
  // Default: demo unless a real Supabase project is configured. Makes a
  // zero-config deploy (e.g. a fresh Vercel import) work out of the box.
  return !process.env.NEXT_PUBLIC_SUPABASE_URL;
}

export const DEMO_USER = { id: "demo-user", email: "maya@example.com" };

interface DemoState {
  topics: Topic[];
  digest: Digest | null;
  settings: Settings;
}

// Module-level singleton so it survives across requests in a running process.
const g = globalThis as unknown as { __distillDemo?: DemoState };

function seed(): DemoState {
  const topics: Topic[] = [
    { id: "t1", phrase: "Fed policy", display_order: 0 },
    { id: "t2", phrase: "Ultra-low-latency systems", display_order: 1 },
    { id: "t3", phrase: "EU AI regulation", display_order: 2 },
  ];
  const digest: Digest = {
    id: "d1",
    generated_at: new Date().toISOString(),
    topic_cards: [
      {
        id: "c1",
        topic_id: "t1",
        status: "ok",
        tldr: "The Fed held rates steady and signalled a patient, data-dependent stance for the summer.",
        bullets: [
          "Target range unchanged at 4.25–4.50% for the fourth straight meeting.",
          "Updated dot plot trimmed expected 2026 cuts from three to two.",
          "Chair stressed that services inflation remains the key holdout.",
          "Markets read the tone as mildly hawkish; 2-year yields ticked up.",
        ],
        sources: [
          { title: "FOMC statement — June 2026", url: "https://www.federalreserve.gov/" },
          { title: "Reuters: Fed holds, trims cut path", url: "https://www.reuters.com/" },
        ],
        last_refreshed_at: null,
      },
      {
        id: "c2",
        topic_id: "t2",
        status: "ok",
        tldr: "Kernel-bypass networking and io_uring keep pushing tail latency lower across trading and real-time infra.",
        bullets: [
          "A widely-shared benchmark showed io_uring beating epoll by ~40% at p99.",
          "DPDK + AF_XDP comparisons dominated the week's systems discussion.",
          "Several teams reported sub-microsecond NIC-to-app paths in production.",
          "Debate continues on whether userspace TCP is worth the maintenance cost.",
        ],
        sources: [
          { title: "An io_uring vs epoll deep dive", url: "https://example.com/io-uring" },
          { title: "AF_XDP in production notes", url: "https://example.com/af-xdp" },
        ],
        last_refreshed_at: null,
      },
      {
        id: "c3",
        topic_id: "t3",
        status: "error",
        last_refreshed_at: null,
      },
    ],
  };
  return {
    topics,
    digest,
    settings: { delivery_time: "08:00", timezone: "America/New_York" },
  };
}

export function demoState(): DemoState {
  if (!g.__distillDemo) g.__distillDemo = seed();
  return g.__distillDemo;
}

export function demoReset() {
  g.__distillDemo = seed();
}
