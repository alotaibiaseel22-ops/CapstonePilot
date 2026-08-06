import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.deps import get_risk_orchestrator, get_session_factory
from app.api.v1.routers import (
    activity,
    attachments,
    auth,
    comments,
    invitations,
    jobs,
    milestones,
    notifications,
    plans,
    project_members,
    projects,
    proposals,
    recommendations,
    risks,
    tasks,
    users,
)
from app.core.config import settings
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.scheduler import run_monitoring_loop

# The default from config.py - every token issued while this is still the
# secret is forgeable by anyone who reads this (open-source) repo, so
# booting with it in production is refused outright rather than silently
# shipping an insecure deploy.
_INSECURE_DEFAULT_JWT_SECRET = "change-me"

# Without this, app-level logger.info() calls (e.g. the console email
# fallback) are silently dropped - uvicorn only configures its own loggers.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV == "production" and settings.JWT_SECRET == _INSECURE_DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is still the default 'change-me' value - refusing to start in "
            "production. Set a real, random JWT_SECRET in the environment."
        )

    # A plain asyncio background task, not a new deployed service - matches
    # BackgroundTasks' existing "zero extra infra" trade-off. Disabled in
    # tests (settings.ENABLE_SCHEDULER=False via conftest.py) so no stray
    # tick races each test's own temp DB.
    task = None
    if settings.ENABLE_SCHEDULER:
        task = asyncio.create_task(
            run_monitoring_loop(
                get_session_factory(), get_risk_orchestrator(), settings.MONITORING_INTERVAL_SECONDS
            )
        )
    yield
    if task is not None:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="CapstonePilot API", version="0.1.0", lifespan=lifespan)

# In development, also accept any localhost port via regex, not just the
# one exact origin in CORS_ORIGINS. Vite auto-bumps to 5174, 5175, etc. the
# moment port 5173 is already taken (e.g. a leftover dev server process from
# an earlier session) - without this, that silent port change makes every
# API call fail as an opaque "can't reach the server" network error, since
# a CORS rejection is indistinguishable from the backend being down once it
# reaches application code. Never relaxed like this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"http://localhost:\d+" if settings.APP_ENV == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Not a secret, and the single most useful line in the log for diagnosing a
# CORS preflight 400 - the browser's exact Origin header (visible in the
# 400 response itself, or via curl) has to appear verbatim in this list, or
# the request is rejected before it ever reaches a route. Logged once at
# startup so a mismatch (wrong domain, stray trailing slash, wrong scheme)
# is visible without needing an ad hoc print statement each time.
logger.info(
    "CORS configured: APP_ENV=%s allow_origins=%s dev_localhost_regex_active=%s",
    settings.APP_ENV,
    settings.CORS_ORIGINS,
    settings.APP_ENV == "development",
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Without this, an unexpected error (DB connection drop, a bug, etc.)
    produces FastAPI's bare default 500 body and nothing useful in the logs
    beyond uvicorn's own traceback dump. This guarantees a full traceback is
    always logged server-side, and returns the real exception message in
    development so the frontend can show it - never in production, since
    exception text can leak internals (file paths, query fragments)."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    if settings.APP_ENV == "development":
        detail = str(exc)
    else:
        detail = "An unexpected server error occurred."
    return JSONResponse(status_code=500, content={"detail": detail})

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(project_members.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")
app.include_router(proposals.router, prefix="/api/v1")
app.include_router(milestones.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(risks.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(activity.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(attachments.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/ready")
def readiness_check():
    """Liveness (/health) only proves the process is up. This additionally
    proves it can reach the database - what Render's health check should
    actually point at, so a DB outage shows as unhealthy instead of a
    silently-failing app that still answers 200 on every request."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed: database unreachable")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
