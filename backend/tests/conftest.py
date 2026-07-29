import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import (
    get_db,
    get_email_service,
    get_planning_orchestrator,
    get_risk_orchestrator,
    get_session_factory,
)
from app.core.config import settings
from app.infrastructure.agents.fake_planning_orchestrator import FakePlanningOrchestrator
from app.infrastructure.agents.fake_risk_orchestrator import FakeRiskOrchestrator
from app.infrastructure.db import models  # noqa: F401  (registers all models on Base.metadata)
from app.infrastructure.db.session import Base
from app.infrastructure.email.email_service import ConsoleEmailService
from app.main import app


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # The real scheduler is a background asyncio loop started from main.py's
    # lifespan - without this, TestClient(app) below would start it against
    # this test's own temp DB every single test run.
    settings.ENABLE_SCHEDULER = False

    app.dependency_overrides[get_db] = override_get_db
    # Default every test to the free/fast/deterministic fake orchestrators,
    # even if whoever runs the suite has a real GEMINI_API_KEY in backend/.env
    # (expected for manual smoke-testing) - the test suite must never make real,
    # paid API calls unless a test deliberately opts back into the real wiring.
    app.dependency_overrides[get_planning_orchestrator] = lambda: FakePlanningOrchestrator()
    app.dependency_overrides[get_risk_orchestrator] = lambda: FakeRiskOrchestrator()
    # Same discipline as above: default every test to the console fallback,
    # even if whoever runs the suite has real SMTP_* credentials in
    # backend/.env (expected for manual smoke-testing) - the test suite must
    # never attempt a real network connection to send email.
    app.dependency_overrides[get_email_service] = lambda: ConsoleEmailService()
    # Every project/task/milestone-affecting route now schedules an immediate
    # risk-check BackgroundTask via get_session_factory (proposals.py's
    # generate_plan already needed this override ad hoc). Without defaulting
    # it here too, those background tasks would silently open a session
    # against the real dev SessionLocal/capstonepilot.db instead of this
    # test's own temp DB - exactly the kind of test-isolation leak this
    # project has already been bitten by once.
    app.dependency_overrides[get_session_factory] = lambda: TestingSessionLocal

    with TestClient(app) as test_client:
        test_client.session_factory = TestingSessionLocal
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()
    os.close(db_fd)
    Path(db_path).unlink(missing_ok=True)
