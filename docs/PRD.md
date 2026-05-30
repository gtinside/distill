# PRD: Daily Digest iOS App

## Problem Statement

Users who follow multiple fast-moving topics — monetary policy, niche technology areas, consumer product releases, geopolitical news — have no good way to stay informed without spending 30–60 minutes daily across Reddit, RSS readers, Twitter, and news sites. The information exists but the synthesis doesn't: users want to know *what matters today* across their specific interests, not scroll a firehose.

## Solution

An iOS app where a User defines a set of Topics (free-text phrases expressing areas of interest) and receives a daily AI-synthesized Digest — a feed of Topic Cards, one per Topic. Each Topic Card contains a one-sentence TL;DR headline, 4–5 bullet takeaways, and source links. The Digest is pushed to the device at a User-configured Delivery Time, and any Topic Card can be refreshed on demand to pull the latest content.

## User Stories

1. As a User, I want to sign in with Apple so that my Topics and Digest are tied to a stable identity across reinstalls.
2. As a new User, I want to be guided through a short onboarding wizard so that I can set up my Topics and Delivery Time before seeing my first Digest.
3. As a new User, I want my first Digest generated automatically after I finish onboarding so that I see value immediately rather than waiting until the next morning.
4. As a User, I want to type a free-text phrase as a Topic so that I can define interests as specifically as I think about them.
5. As a User, I want to see example Topics as tappable chips during onboarding so that I have inspiration if I'm unsure what to enter.
6. As a User, I want Topic names to be between 3 and 60 characters so that I'm guided toward phrases specific enough to produce useful results.
7. As a User, I want to add up to 10 Topics so that I can cover my key interests without the Digest becoming overwhelming.
8. As a User, I want to receive a push notification at my configured Delivery Time so that I know my daily Digest is ready without opening the app.
9. As a User, I want the push notification to mention my Topic names so that I feel the Digest is personalised to me.
10. As a User, I want tapping the push notification to open the Digest feed directly so that I can start reading immediately.
11. As a User, I want to see a feed of Topic Cards on the Digest screen so that I can scan all my Topics at a glance.
12. As a User, I want each Topic Card to show a one-sentence TL;DR headline so that I can decide in seconds whether to read the detail.
13. As a User, I want each Topic Card to show 4–5 bullet takeaways so that I can get the substance without reading full articles.
14. As a User, I want each Topic Card to show source links so that I can follow up on the underlying content.
15. As a User, I want to refresh a single Topic Card on demand so that I can get the latest content for that Topic without waiting for tomorrow's Digest.
16. As a User, I want the on-demand refresh to fetch fresh sources and resynthesize so that I'm getting genuinely new content, not a rewrite of old sources.
17. As a User, I want refresh to be rate-limited to once per hour per Topic so that I understand why repeated taps don't trigger multiple fetches.
18. As a User, I want to drag Topics into a custom order so that my most important Topics appear at the top of the Digest feed.
19. As a User, I want to see a clear error state on a Topic Card if it failed to generate so that I know the issue is isolated and the rest of my Digest is still valid.
20. As a User, I want a manual refresh tap on a failed Topic Card so that I can retry it without waiting for tomorrow.
21. As a User, I want to read my Digest when offline so that the app is useful on a plane or in a low-signal environment.
22. As a User, I want the offline Digest to show a "last updated" timestamp so that I know how fresh the cached content is.
23. As a User, I want to set a Delivery Time for my daily Digest so that it arrives when I'm likely to read it.
24. As a User, I want Delivery Time to default to 7:00 AM local time so that I don't have to configure it if the default works for me.
25. As a User, I want to manage my Topics (add, reorder, delete) from a dedicated Topics tab so that Topic management doesn't clutter the reading experience.
26. As a User, I want Settings (Delivery Time, sign out) accessible from within the Topics tab so that they're reachable without a deeply buried menu.
27. As a User, I want only the current day's Digest shown so that the app stays focused and doesn't accumulate a backlog to manage.

## Implementation Decisions

### Architecture Overview
- **iOS client:** SwiftUI, iPhone-first (iPad deferred to Phase 2).
- **Backend data layer:** Supabase (PostgreSQL + Auth). Sign in with Apple is configured through Supabase Auth.
- **Digest generation:** Railway worker (Python), long-running process. Polls Supabase every minute for Users whose Delivery Time matches the current time (±1 min window). See ADR-0001.
- **Push notifications:** Firebase Cloud Messaging (FCM) as the APNs delivery bridge. Supabase is the source of truth; FCM is used only for push delivery.
- **LLM:** Claude Sonnet. One API call per Topic Card. Structured JSON output to ensure consistent Topic Card shape.
- **Source fetching:** Exa.ai semantic search API (Phase 1 only). User-pinnable RSS/subreddits are deferred to Phase 2.

### Modules

**SynthesisEngine (backend — deep module)**
Input: Topic string + Exa.ai search results.
Output: structured TopicCard (tldr: string, bullets: string[], sources: [{title, url}]).
Encapsulates the Claude Sonnet prompt, structured output parsing, and retry on malformed response. No I/O side effects — purely a transformation function. Tested in isolation.

**DigestOrchestrator (backend — deep module)**
Input: UserId.
Output: Digest with one TopicCard per Topic (some may carry an error state).
Fans out SynthesisEngine calls across all User Topics (up to 10). Each Topic Card is retried up to 3 times before being marked failed. Assembles the partial or complete Digest regardless of individual failures. See ADR-0002. Tested in isolation.

**SchedulerWorker (backend)**
Long-running Railway process. Every 60 seconds: query Supabase for Users whose Delivery Time falls within the current minute. For each matched User, invoke DigestOrchestrator, persist the resulting Digest to Supabase, then trigger PushNotificationService.

**PushNotificationService (backend)**
Formats the personalised push notification body (includes 1–2 Topic names from the User's Topic list). Sends via Firebase FCM to the User's registered device token.

**APILayer (backend)**
REST endpoints consumed by the iOS client:
- `POST /topics` — create Topic (validates 3–60 chars, enforces 10-Topic cap)
- `PATCH /topics/:id` — update Topic name or order
- `DELETE /topics/:id` — delete Topic
- `GET /digest` — fetch current Digest for authenticated User
- `POST /digest/topics/:id/refresh` — trigger on-demand refresh for one Topic Card (rate-limited: once per hour per Topic)
- `PATCH /settings` — update Delivery Time

**OfflineCacheModule (iOS)**
Persists the most recently fetched Digest to the app sandbox as JSON. Serves the cached Digest when the device has no network. Stores a `lastUpdated` timestamp displayed to the User.

**NotificationModule (iOS)**
Registers for APNs on launch, stores device token to Supabase via APILayer. Handles incoming push tap: navigates to the Digest feed tab.

**OnboardingModule (iOS)**
Three-screen linear wizard:
1. Sign in with Apple
2. Add Topics (min 1, example chips shown, 10-Topic cap enforced)
3. Delivery Time picker (defaults to 7:00 AM local time)

On completion, calls `POST /digest/generate` to trigger first Digest generation immediately. Shows a loading state ("Building your first digest…") during the ~30s wait.

**TopicModule (iOS)**
Topics tab: list of Topics with drag-to-reorder (persisted via `PATCH /topics/:id` order field), add Topic sheet, swipe-to-delete.

**DigestModule + TopicCardModule (iOS)**
Digest tab: `List` of Topic Cards fetched from `GET /digest`. Pull-to-refresh triggers `POST /digest/topics/:id/refresh` per card. Each TopicCard renders TL;DR, bullets, and source links. Error state shows retry CTA. OfflineCacheModule is consulted when network is unavailable.

### Schema (Supabase / PostgreSQL)

- `users` — id, apple_sub, delivery_time, device_token, created_at
- `topics` — id, user_id, phrase, display_order, created_at
- `digests` — id, user_id, generated_at
- `topic_cards` — id, digest_id, topic_id, tldr, bullets (jsonb), sources (jsonb), status (ok | error), last_refreshed_at

### Rate Limiting
On-demand refresh enforced server-side: check `topic_cards.last_refreshed_at`; reject with 429 if less than 60 minutes ago.

### Topic Cap
Enforced server-side on `POST /topics`: count existing Topics for User; reject with 422 if already at 10.

## Testing Decisions

Good tests verify external behaviour through the module's public interface — not internal implementation details like which prompt template was used or how retries are implemented internally.

**SynthesisEngine**
- Given a Topic string and a set of Exa.ai result fixtures, assert the returned TopicCard has a non-empty tldr, 4–5 bullets, and at least one source.
- Given Exa.ai results with no usable content, assert the engine raises a synthesis error rather than returning a malformed card.
- Given a Claude response that fails structured output parsing, assert the engine retries before raising.
- Tests use fixture data (recorded Exa.ai responses) — no live API calls in CI.

**DigestOrchestrator**
- Given a User with 5 Topics where 4 succeed and 1 exhausts retries, assert the returned Digest contains 4 valid TopicCards and 1 error-state TopicCard.
- Given a User with 0 Topics, assert the orchestrator returns an empty Digest without error.
- Given a SynthesisEngine that always fails, assert all TopicCards carry error status and the Digest is still returned (not raised as an exception).
- SynthesisEngine is injected as a dependency so tests can supply a stub without mocking internals.

## Out of Scope

- **User-pinnable Sources (RSS, subreddits):** Deferred to Phase 2. All Sources in Phase 1 are Exa.ai semantic search results only.
- **iPad layout:** iPhone-first. iPad support deferred to Phase 2.
- **Digest history / archive:** Only the current Digest is stored and shown. No scrollable history.
- **Monetization / subscription gating:** App is free. No billing infrastructure.
- **Duplicate Topic detection:** Users manage their own Topic list; fuzzy deduplication is not implemented.
- **Multi-device sync:** Digest is tied to the authenticated User in Supabase; a second device will fetch the same Digest data, but multi-device notification handling is not addressed.

## Further Notes

- **ADR-0001** (`docs/adr/0001-railway-worker-over-serverless.md`): explains why a long-running Railway worker was chosen over serverless functions for Digest generation.
- **ADR-0002** (`docs/adr/0002-partial-digest-on-topic-failure.md`): explains the decision to push a partial Digest on Topic Card failure rather than withholding the whole Digest.
- The 10-Topic hard cap and 1-hour refresh rate limit are the primary cost controls while the app is free. These should be revisited if usage patterns suggest abuse.
