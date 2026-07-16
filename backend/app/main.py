import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import (
    auth,
    invitations,
    milestones,
    project_members,
    projects,
    proposals,
    tasks,
    users,
)
from app.core.config import settings

# Without this, app-level logger.info() calls (e.g. the console email
# fallback) are silently dropped - uvicorn only configures its own loggers.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="CapstonePilot API", version="0.1.0")

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


@app.get("/health")
def health_check():
    return {"status": "ok"}
