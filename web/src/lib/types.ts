// Domain types — mirror the backend / CONTEXT.md glossary.

export interface Source {
  title: string;
  url: string;
}

export interface TopicCard {
  id?: string;
  topic_id: string;
  status: "ok" | "error";
  tldr?: string;
  bullets?: string[];
  sources?: Source[];
  last_refreshed_at?: string | null;
}

export interface Digest {
  id: string;
  generated_at: string;
  topic_cards: TopicCard[];
}

export interface Topic {
  id: string;
  phrase: string;
  display_order: number;
}

export interface Settings {
  delivery_time: string; // "HH:MM"
  timezone: string; // IANA tz name
}

export const TOPIC_MIN = 3;
export const TOPIC_MAX = 60;
export const TOPIC_LIMIT = 10;

export const EXAMPLE_TOPICS = [
  "Fed policy",
  "Ultra-low-latency systems",
  "EU AI regulation",
  "NBA trades",
  "Climate tech funding",
  "Formula 1 strategy",
  "Generative video models",
  "Commercial spaceflight",
];
