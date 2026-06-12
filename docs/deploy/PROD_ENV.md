# Production environment variables

Fill the `<...>` values from your own dashboards. Never commit real secrets —
set them in each platform's dashboard.

## Vercel (web) — Project Settings → Environment Variables
```
NEXT_PUBLIC_DEMO_MODE=false
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase anon key>
DISTILL_API_URL=https://<railway-service>.up.railway.app
```

## Railway (backend) — Service → Variables
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<supabase anon key>
SUPABASE_SERVICE_ROLE_KEY=<supabase service role key>
SUPABASE_JWT_SECRET=<supabase jwt secret>
ANTHROPIC_API_KEY=<anthropic key>
EXA_API_KEY=<exa key>
RESEND_API_KEY=<resend key>
RESEND_FROM_EMAIL=onboarding@resend.dev   # Phase 1; digest@yourdomain in Phase 2
APP_BASE_URL=https://<app>.vercel.app
TRENDING_REFRESH_UTC=05:00
```

## Supabase — Authentication → URL Configuration
```
Site URL:            https://<app>.vercel.app
Redirect allowlist:  https://<app>.vercel.app/auth/callback
```
