# Web Client and Email Delivery (Pivot Off Apple)

Distill began as a native iOS app, but two of its core features — push
notifications and Sign in with Apple — require a paid Apple Developer account
with no free tier. Rather than pay that ongoing cost, Distill moves to the web.

**Client.** A Next.js (App Router) web app replaces the SwiftUI client. The
browser never calls the backend directly: a thin server-side BFF holds the
Supabase session in httpOnly cookies (`@supabase/ssr`) and forwards the user's
access token to the existing FastAPI REST API. All business rules (Topic-name
validation, the 10-Topic cap, the once-per-hour refresh limit) stay in FastAPI —
the web tier duplicates none of them. The original iOS client is retained but
deprecated.

**Auth.** Sign in with Apple is replaced by **Supabase magic-link** (passwordless
email). This reuses the email channel Distill already needs and removes the
Apple-account requirement. A Postgres trigger creates the application `users`
row on Supabase Auth signup so `users.id == auth.uid()`.

**Delivery.** The daily push notification is replaced by an **email Digest** sent
via Resend. `EmailDigestService` renders the Topic Cards (and a deep link back to
the web app) as HTML; the `SchedulerWorker` calls it at the user's Delivery Time
in place of the old `PushNotificationService`. Firebase/FCM is removed.

**Delivery Time becomes timezone-aware.** iOS relied on the device's local time;
the web has no equivalent, so the user's IANA timezone is captured at onboarding
and stored alongside `delivery_time`. A pure `user_is_due(now_utc, delivery_time,
tz)` function does the matching.

**Offline reading is dropped.** The iOS `OfflineCacheModule` has low value for a
text app read primarily online; the already-delivered email is the offline
fallback.

The synthesis pipeline (`SynthesisEngine`, `DigestOrchestrator`), the
long-lived-worker decision (ADR-0001), and partial-Digest-on-failure (ADR-0002)
are all unchanged.
