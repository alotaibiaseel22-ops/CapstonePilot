# Deployment Guide

CapstonePilot deploys as two independent pieces:

- **Backend** — FastAPI app, containerized with Docker, hosted on [Render](https://render.com) as a Web Service, backed by managed PostgreSQL.
- **Frontend** — Vite/React static build, hosted on [Vercel](https://vercel.com).

This guide covers first-time setup. Nothing here is automated (no CI/CD) - each step is a manual action in the Render/Vercel dashboard, on purpose, to keep the deployment simple to understand and explain.

## 1. Backend on Render

1. **Create a PostgreSQL database** on Render (or any managed Postgres provider). Copy its connection string - this becomes `DATABASE_URL`.
2. **Create a new Web Service** on Render, pointed at this repo, with:
   - **Root Directory**: `backend`
   - **Environment**: Docker (Render will use `backend/Dockerfile` automatically)
   - **Health Check Path**: `/health/ready` (checks the app can actually reach the database, not just that the process is up)
3. **Set the environment variables** listed in the [table below](#environment-variables) on the Render service. At minimum: `APP_ENV=production`, `DATABASE_URL`, `JWT_SECRET` (a real random value - the app refuses to boot in production with the default), `GEMINI_API_KEY`, `FRONTEND_URL`, `CORS_ORIGINS`.
4. **Deploy.** Render builds the Docker image and starts the container, which only runs `uvicorn` - it does **not** run database migrations automatically.
5. **Run migrations manually**, once, after the first successful deploy (and again after any future release that adds a new migration):
   ```bash
   # From Render's shell for the service, or any machine with DATABASE_URL set to the same database:
   cd backend
   alembic upgrade head
   ```
6. Confirm `https://<your-render-service>.onrender.com/health` and `/health/ready` both return `{"status": "ok"}`.

**Known trade-off**: Render's free tier spins the service down after ~15 minutes of inactivity and cold-starts it on the next request. If `ENABLE_SCHEDULER=true`, the background risk-monitoring loop (`app/infrastructure/scheduler.py`) only runs while the service is actually up, so it will be interrupted by spin-down on the free tier. For the scheduler to run continuously, use at least Render's Starter tier.

## 2. Health Check Verification

The backend exposes two distinct endpoints - Render (and any host) should point its health check at `/health/ready`, not `/health`:

| Endpoint | Checks | Use |
|---|---|---|
| `GET /health` | The process is up and answering requests. Does **not** touch the database. | A basic liveness probe, if your host wants a separate one. |
| `GET /health/ready` | The above, plus a real `SELECT 1` against `DATABASE_URL`. Returns `200 {"status": "ok"}` when the database is reachable, `503 {"status": "unavailable"}` when it isn't. | The **readiness** probe - this is what should gate whether Render considers the service healthy, since a DB outage should show as unhealthy rather than as an app that answers every request with an opaque 500. |

To verify by hand after any deploy:
```bash
curl https://<your-render-service>.onrender.com/health
curl https://<your-render-service>.onrender.com/health/ready
```
Both should return `{"status": "ok"}`. If `/health` succeeds but `/health/ready` returns 503, the app is running but can't reach Postgres - check `DATABASE_URL` and that migrations have been run (a missing `projects` table, etc. also surfaces as a 503 here, since the readiness query itself will fail against a database Alembic never touched).

## 3. Frontend on Vercel

1. **Import the repo** into Vercel as a new project, with:
   - **Root Directory**: `frontend`
   - Framework preset: Vite (auto-detected). `frontend/vercel.json` already sets the build command, output directory, and the SPA rewrite rule React Router needs so refreshing a route like `/projects/:id` doesn't 404.
2. **Set the environment variable** `VITE_API_BASE_URL` to the Render backend's URL from step 1 (e.g. `https://capstonepilot-api.onrender.com`), no trailing slash.
3. **Deploy.** Vercel builds and hosts the static site, and gives it a URL (e.g. `https://capstonepilot.vercel.app`).

## 4. Deploy order (important)

The backend's CORS config and the frontend's API base URL each need the *other* service's real URL, so the first deploy has to happen in this order:

1. Deploy the **backend** first (its `CORS_ORIGINS` can temporarily be anything, or left as the local-dev default).
2. Note the backend's Render URL, set it as `VITE_API_BASE_URL` on Vercel, and deploy the **frontend**.
3. Note the frontend's Vercel URL, set it as `CORS_ORIGINS` on the backend (as a JSON array, e.g. `["https://capstonepilot.vercel.app"]` - not comma-separated), and **redeploy the backend** so the new CORS config takes effect.

## Environment Variables

### Backend (Render)

| Variable | Required | Description | Example |
|---|---|---|---|
| `APP_ENV` | Yes | `production` in deployment - gates the JWT_SECRET safety check, dev-only CORS regex, and whether error detail is exposed in responses. | `production` |
| `DATABASE_URL` | Yes | SQLAlchemy connection string. Must be Postgres in production - SQLite doesn't survive Render's ephemeral filesystem. | `postgresql://user:pass@host:5432/dbname` |
| `JWT_SECRET` | Yes | Signing secret for auth tokens. The app refuses to start in production if this is left at the default `change-me`. | a long random string |
| `JWT_ALGORITHM` | No | JWT signing algorithm. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Session length in minutes. | `43200` (30 days) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key - without it the app falls back to placeholder (non-AI) plans/analysis. | `AIza...` |
| `GEMINI_MODEL` | No | Gemini model name. | `gemini-flash-latest` |
| `FRONTEND_URL` | Yes | Used to build invitation links in emails. | `https://capstonepilot.vercel.app` |
| `CORS_ORIGINS` | Yes | JSON array of allowed frontend origins - not comma-separated. | `["https://capstonepilot.vercel.app"]` |
| `ENABLE_SCHEDULER` | No | Enables the background Risk/Recommendation monitoring loop. | `true` |
| `MONITORING_INTERVAL_SECONDS` | No | How often the scheduler checks active projects. | `1800` |
| `SMTP_HOST` | No | SMTP server for real invitation emails. Left empty, emails are logged to the console instead of sent. | `smtp.gmail.com` |
| `SMTP_PORT` | No | SMTP port. | `587` |
| `SMTP_USERNAME` | No | SMTP auth username. | `you@example.com` |
| `SMTP_PASSWORD` | No | SMTP auth password/app password. | *(secret)* |
| `SMTP_FROM_EMAIL` | No | "From" address on invitation emails. | `no-reply@capstonepilot.app` |
| `SMTP_USE_TLS` | No | Whether to use STARTTLS. | `true` |

### Frontend (Vercel)

| Variable | Required | Description | Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | Base URL of the deployed backend, no trailing slash. | `https://capstonepilot-api.onrender.com` |

## Common Deployment Issues

- **`/health` returns 200 but `/health/ready` returns 503.** Migrations haven't been run against the production database yet (see step 5 above), or `DATABASE_URL` points at the wrong instance. Run `alembic upgrade head` and re-check.
- **Frontend loads but every API call fails as a network error / CORS error in the browser console.** `CORS_ORIGINS` on the backend doesn't include the frontend's real Vercel URL, or it's malformed - it must be a **JSON array string**, e.g. `["https://capstonepilot.vercel.app"]`, not a bare comma-separated value. This is the single easiest mistake to make in this config. Redeploy the backend after changing it - it's read once at process start.
- **Backend won't start at all, container exits immediately.** Almost always `JWT_SECRET` was left at the default `change-me` with `APP_ENV=production` - the app refuses to boot in that combination on purpose (see `main.py`'s startup guard). Check the service logs for the exact `RuntimeError` message and set a real secret.
- **Invitation links point at `localhost`.** `FRONTEND_URL` wasn't set to the deployed Vercel URL - it defaults to `http://localhost:5173`.
- **AI features (plan generation, risk analysis) silently produce placeholder/generic output instead of failing.** `GEMINI_API_KEY` is unset or wrong - the app is designed to degrade gracefully to `FakePlanningOrchestrator`/`FakeRiskOrchestrator` rather than error out, so a misconfigured key doesn't look like an obvious failure. Check for the `[Placeholder plan — no GEMINI_API_KEY configured]` prefix in a generated plan's summary as the tell.
- **Invitation/notification emails never arrive but nothing errors.** `SMTP_HOST` is unset - this is the documented fallback (emails are logged server-side instead of sent), not a bug. Check the service logs for `[email:console]` lines, or set real SMTP credentials.
- **The Risk/Recommendation background loop never seems to run.** Either `ENABLE_SCHEDULER` is `false`/unset, or the service is on Render's free tier and has spun down from inactivity (see the trade-off noted above) - the loop only runs while the process is actually up.
- **A redeploy seems to hang or takes unusually long to roll over.** Confirmed empirically during this pass: the Dockerfile's `CMD` must use `exec uvicorn ...` (it does) so `SIGTERM` reaches uvicorn directly instead of being swallowed by an intermediate shell - without it, every stop/redeploy has to wait out the full stop timeout and get force-killed instead of shutting down in ~1-2 seconds.

## Production Verification Checklist

Run through this after every deploy:

- [ ] Backend is running (`GET /health` returns `{"status": "ok"}`)
- [ ] Health endpoint returns OK (`GET /health/ready` returns `{"status": "ok"}`, confirming DB connectivity)
- [ ] Frontend loads correctly at its Vercel URL
- [ ] Database connected (covered by `/health/ready`, but also confirm login/register works end to end)
- [ ] Gemini API working (create a project and confirm a real, non-placeholder plan is generated)
- [ ] Proposal upload works (upload a PDF/DOCX/TXT during project creation)
- [ ] Planner works (the generated plan has specific milestones/tasks, not the placeholder fallback text)
- [ ] Risk Analysis works (an overdue or off-track project surfaces a risk)
- [ ] Recommendation Agent works (a surfaced risk comes with an actionable recommendation)
- [ ] Invitation email works (inviting a teammate by email either sends a real email via SMTP or, if SMTP isn't configured, logs it server-side)
- [ ] Invitation acceptance works (the invited teammate can join via the emailed link)
