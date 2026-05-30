# Railway Worker Over Serverless for Digest Generation

Digest generation requires fetching sources via Exa.ai and calling Claude Sonnet once per Topic Card. A user with 8 Topics needs ~80–120 seconds of sequential or parallel LLM work. Serverless options (Supabase Edge Functions, AWS Lambda with default config) impose timeout limits too tight for this workload. We use a long-running Railway worker that polls Supabase every minute for users whose Delivery Time matches the current time, then fans out one synthesis task per Topic Card. This keeps timeouts off the critical path and makes the generation pipeline straightforward to debug.

## Considered Options

- **Supabase Edge Functions** — 2-minute timeout, insufficient for multi-topic synthesis
- **AWS Lambda** — 15-minute timeout sufficient, but adds significant infrastructure complexity for an MVP
- **Trigger.dev** — elegant fan-out and retry handling, but introduces another vendor dependency
