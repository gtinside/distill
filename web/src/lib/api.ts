// Server-side BFF data layer. In demo mode it reads/writes the in-memory demo
// store; otherwise it forwards authenticated requests to the FastAPI backend
// with the user's Supabase access token. All business rules (validation,
// 10-topic cap, refresh rate limit) live in FastAPI — this is a thin passthrough.

import "server-only";
import type { Digest, Settings, Topic, TopicCard, TrendingCard } from "./types";
import { DEMO_TRENDING, demoState, isDemoMode } from "./demo";
import { getAccessToken } from "./supabase/server";

const API_URL = process.env.DISTILL_API_URL ?? "http://localhost:8000";

export class RateLimitError extends Error {
  retryAt: string;
  constructor(message: string, retryAt: string) {
    super(message);
    this.retryAt = retryAt;
  }
}

async function backend(path: string, init?: RequestInit) {
  const token = await getAccessToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  return res;
}

// ---------------------------------------------------------------- Topics

export async function getTopics(): Promise<Topic[]> {
  if (isDemoMode()) {
    return [...demoState().topics].sort((a, b) => a.display_order - b.display_order);
  }
  const res = await backend("/topics");
  if (!res.ok) return [];
  return res.json();
}

export async function createTopic(phrase: string): Promise<Topic> {
  if (isDemoMode()) {
    const s = demoState();
    const topic: Topic = {
      id: `t${Date.now()}`,
      phrase,
      display_order: s.topics.length,
    };
    s.topics.push(topic);
    return topic;
  }
  const res = await backend("/topics", {
    method: "POST",
    body: JSON.stringify({ phrase }),
  });
  if (!res.ok) throw new Error((await safeDetail(res)) ?? "Failed to create topic");
  return res.json();
}

export async function updateTopic(
  id: string,
  data: { phrase?: string; display_order?: number }
): Promise<void> {
  if (isDemoMode()) {
    const t = demoState().topics.find((x) => x.id === id);
    if (t) Object.assign(t, data);
    return;
  }
  await backend(`/topics/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteTopic(id: string): Promise<void> {
  if (isDemoMode()) {
    const s = demoState();
    s.topics = s.topics.filter((t) => t.id !== id);
    return;
  }
  await backend(`/topics/${id}`, { method: "DELETE" });
}

export async function reorderTopics(orderedIds: string[]): Promise<void> {
  await Promise.all(orderedIds.map((id, i) => updateTopic(id, { display_order: i })));
}

// ---------------------------------------------------------------- Digest

export async function getDigest(): Promise<Digest | null> {
  if (isDemoMode()) return demoState().digest;
  const res = await backend("/digest");
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return res.json();
}

export async function generateDigest(): Promise<Digest | null> {
  if (isDemoMode()) return demoState().digest;
  const res = await backend("/digest/generate", { method: "POST" });
  if (!res.ok) return null;
  return res.json();
}

export async function refreshCard(topicId: string): Promise<TopicCard> {
  if (isDemoMode()) {
    const card = demoState().digest?.topic_cards.find((c) => c.topic_id === topicId);
    if (card) {
      card.status = "ok";
      card.tldr = card.tldr ?? "Refreshed: latest sources synthesized just now.";
      card.bullets = card.bullets ?? ["Fresh point one", "Fresh point two"];
      card.sources = card.sources ?? [{ title: "Latest source", url: "https://example.com" }];
      card.last_refreshed_at = new Date().toISOString();
    }
    return card as TopicCard;
  }
  const res = await backend(`/digest/topics/${topicId}/refresh`, { method: "POST" });
  if (res.status === 429) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail ?? {};
    throw new RateLimitError(detail.detail ?? "Rate limited", detail.retry_after ?? "");
  }
  if (!res.ok) throw new Error("Refresh failed");
  return res.json();
}

// ---------------------------------------------------------------- Trending

export async function getTrending(): Promise<TrendingCard[]> {
  if (isDemoMode()) return DEMO_TRENDING;
  const res = await fetch(`${API_URL}/trending`, { cache: "no-store" }).catch(
    () => null
  );
  if (!res || !res.ok) return [];
  const body = await res.json();
  return (body?.cards ?? []) as TrendingCard[];
}

// ---------------------------------------------------------------- Settings

export async function getSettings(): Promise<Settings> {
  if (isDemoMode()) {
    const { delivery_time, timezone } = demoState().settings;
    return { delivery_time, timezone };
  }
  const res = await backend("/settings", { method: "GET" }).catch(() => null);
  if (!res || !res.ok) return { delivery_time: "07:00", timezone: "UTC" };
  return res.json();
}

export async function updateSettings(data: Partial<Settings>): Promise<void> {
  if (isDemoMode()) {
    Object.assign(demoState().settings, data);
    return;
  }
  await backend("/settings", { method: "PATCH", body: JSON.stringify(data) });
}

async function safeDetail(res: Response): Promise<string | null> {
  try {
    const body = await res.json();
    return typeof body?.detail === "string" ? body.detail : null;
  } catch {
    return null;
  }
}
