from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="CapstonePilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
