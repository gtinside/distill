// Demo mode: a self-contained in-memory backend so the whole app runs locally
// (and on a Vercel preview) with zero Supabase/FastAPI/Resend configuration.
// Toggled by NEXT_PUBLIC_DEMO_MODE. Mutations persist for the life of the
// server process — enough for local use, demos, and screenshots.

import type { Digest, Settings, Topic, TrendingCard } from "./types";

// Cookie that marks a "signed-in" demo session (set by Continue-to-demo).
export const DEMO_COOKIE = "distill_demo";

export function isDemoMode(): boolean {
  // Demo must be explicit. Never infer it from a missing Supabase URL — a prod
  // misconfiguration must fail closed (real auth), not silently serve seed data.
  return process.env.NEXT_PUBLIC_DEMO_MODE === "true";
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

// The shared, global trending digest shown on the front page. A couple overlap
// the seeded personal topics (Fed policy, EU AI regulation) so the signed-in
// "not following" filter is demonstrable; the rest are fresh discovery.
export const DEMO_TRENDING: TrendingCard[] = [
  {
    trending_topic_id: "tt1",
    phrase: "Generative video models",
    status: "ok",
    tldr: "Text-to-video crossed into broadcast quality this week, reshaping the creative tooling debate.",
    bullets: [
      "Two new models hit near-photoreal 60-second clips with consistent characters.",
      "Studios are piloting previz workflows; unions are pushing back on disclosure.",
      "Open-weights challengers are ~6 months behind but closing fast.",
      "Cost-per-second fell roughly 4x in three months.",
    ],
    sources: [
      { title: "The state of AI video, mid-2026", url: "https://example.com/ai-video" },
      { title: "Studios pilot generative previz", url: "https://example.com/previz" },
    ],
  },
  {
    trending_topic_id: "tt2",
    phrase: "Commercial spaceflight",
    status: "ok",
    tldr: "A back-to-back launch cadence pushed reusable heavy-lift economics into a new regime.",
    bullets: [
      "Two heavy-lift cores flew and landed within 48 hours.",
      "Per-kg-to-orbit estimates dropped below the symbolic $1,000 line.",
      "A new crewed station module reached orbit ahead of schedule.",
      "Insurers are repricing launch risk downward for the first time in years.",
    ],
    sources: [
      { title: "Reusable heavy-lift economics", url: "https://example.com/launch" },
    ],
  },
  {
    trending_topic_id: "tt3",
    phrase: "Fed policy",
    status: "ok",
    tldr: "The Fed held rates steady and signalled a patient, data-dependent stance for the summer.",
    bullets: [
      "Target range unchanged for the fourth straight meeting.",
      "Dot plot trimmed expected 2026 cuts from three to two.",
      "Services inflation flagged as the key holdout.",
    ],
    sources: [
      { title: "FOMC statement — June 2026", url: "https://www.federalreserve.gov/" },
    ],
  },
  {
    trending_topic_id: "tt4",
    phrase: "Longevity research",
    status: "ok",
    tldr: "A large partial-reprogramming trial reported its first durable human biomarker shifts.",
    bullets: [
      "Epigenetic age markers moved in a controlled cohort over 9 months.",
      "Safety signals were clean; efficacy claims remain contested.",
      "Funding rotated from supplements toward measurable interventions.",
    ],
    sources: [
      { title: "Reprogramming trial readout", url: "https://example.com/longevity" },
    ],
  },
  {
    trending_topic_id: "tt5",
    phrase: "NBA trades",
    status: "ok",
    tldr: "A blockbuster three-team deal reset the title odds two weeks before the deadline.",
    bullets: [
      "A perennial All-Star changed conferences in a pick-heavy package.",
      "Two contenders cleared cap space for a second move.",
      "Betting markets swung the championship favorite overnight.",
    ],
    sources: [{ title: "Deadline tracker", url: "https://example.com/nba" }],
  },
  {
    trending_topic_id: "tt6",
    phrase: "EU AI regulation",
    status: "ok",
    tldr: "Implementing guidance for the AI Act's high-risk tiers landed, clarifying compliance timelines.",
    bullets: [
      "Foundation-model duties phase in over the next two quarters.",
      "Open-source carve-outs were narrowed from the draft.",
      "National regulators published first audit checklists.",
    ],
    sources: [{ title: "AI Act guidance", url: "https://example.com/ai-act" }],
  },
];
