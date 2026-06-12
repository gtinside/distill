# Daily Digest App

An iOS app where a user defines topics of interest and receives AI-synthesized summaries — either on a daily schedule or pulled on demand.

## Language

**Digest**:
A daily reading session composed of Topic Cards, each an independent AI-synthesized summary for one Topic. Delivered once per day or generated on demand.
_Avoid_: Report, newsletter, feed, briefing

**Topic Card**:
The synthesized summary for a single Topic within a Digest. Structure: one-sentence TL;DR headline, 4-5 bullet takeaways, and source links. Independently refreshable.
_Avoid_: Summary, article, item, entry

**Topic**:
A user-defined area of interest expressed as a free-text phrase (e.g. "Fed policy", "ultra-low latency systems"). The unit against which content is fetched and synthesized.
_Avoid_: Category, tag, interest, keyword

**User**:
A person with a server-side account (authenticated via magic-link email through Supabase Auth) who defines Topics and reads Digests. Identity is stable across devices.
_Avoid_: Account, subscriber, reader

**Source**:
A content origin the backend fetches from for a given Topic — either a search result from a semantic search API (default) or a user-pinned feed (RSS, subreddit, etc.).
_Avoid_: Feed, channel, subscription

**Delivery Time**:
The user-configured time (in the User's stored timezone) at which the backend generates and emails the daily Digest.
_Avoid_: Schedule, notification time, send time

**Trending**:
A shared, global set of Topic Cards for a curated list of timely Topics, generated once daily and shown to everyone — the public front page, and the discovery source signed-in Users can Follow from.
_Avoid_: Popular, hot, feed, for-you
