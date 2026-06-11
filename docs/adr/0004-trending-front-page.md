# Trending Front Page and Shared Global Digest

Distill was a private tool: a visitor hit a sign-in wall, then a blank "type your
topics" box, and only then got value. To fix that cold-start and add a discovery
loop, Distill gains a **public trending front page** plus personal discovery.

**Three states of `/`.** Logged-out visitors see full **Trending Topic Cards**
(TL;DR, bullets, sources) — server-rendered, public, indexable, shareable. Signed-in
users see **their Digest** on top and **trending topics they aren't following yet**
below, each with a one-tap **Follow**. Following a trending Topic adds it to the
user's list (reusing the 3–60 validation and 10-Topic cap) and it moves into their
Digest.

**A shared global digest.** Trending is generated **once daily** as a single global
set of cards served to everyone — compute once, serve to all — rather than
per-user. This is what makes a fast, public, cacheable front page possible. The
`SchedulerWorker` runs this pass daily (env `TRENDING_REFRESH_UTC`, default 05:00)
independently of per-user digests.

**Curated now, world-derived later.** The trending *selection* comes from an
admin-maintained `trending_topics` table; only the selection is curated — card
*content* is always freshly synthesized. The selection is isolated behind
`get_trending_topics()`, so it can later be swapped for world-derived trend
detection (Exa + recency) and eventually aggregate-of-users popularity without
touching the UI or the synthesis pipeline.

**Reuse over rebuild.** Trending reuses `SynthesisEngine` unchanged and the same
`DigestOrchestrator` path (now `generate_cards(topics)` over any topic list),
including the 3-retry + partial-failure behaviour from ADR-0002. The only new API
surface is a public `GET /trending`; Follow reuses `POST /topics`.

**Out of scope (v1):** world-derived/aggregate trend detection, trending in the
daily email (email stays your-topics-only), per-user trending ranking.
