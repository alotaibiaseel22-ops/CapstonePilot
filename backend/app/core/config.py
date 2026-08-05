from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./capstonepilot.db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    # 30 days, not 60 minutes: invited collaborators onboarded via
    # provision_invited_user() get a random password they never see, so a
    # short-lived session would leave them with no way back in once it
    # expires. Applies to every user, owners included - a 60-minute session
    # was arguably too short for this app regardless of this feature.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    # Official Google GenAI SDK (crewai's native "gemini" provider), not OpenRouter.
    # One Flash-tier model for both Documentation Analysis and the Planner - see
    # architecture.md section 11. Model choice stays a config change, not a code one.
    GEMINI_API_KEY: str = ""
    # "gemini-2.5-flash" itself 404s as "no longer available to new users" on
    # freshly-created API keys (confirmed against the real API, not assumed) -
    # "gemini-flash-latest" is Google's own always-current-Flash alias and is
    # what's actually accessible; satisfies "2.5 Flash or the latest available
    # Flash model" either way.
    GEMINI_MODEL: str = "gemini-flash-latest"

   
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Automatic Risk/Recommendation monitoring (Iteration 12). Disabled by
    # default in tests (conftest.py) so no stray background task races each
    # test's own temp DB - a plain asyncio loop, not Celery/APScheduler, per
    # the same "zero extra infra" trade-off BackgroundTasks already made.
    ENABLE_SCHEDULER: bool = True
    MONITORING_INTERVAL_SECONDS: int = 1800

    # Used to build invitation links in emails, e.g. {FRONTEND_URL}/invite/{token}.
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP is optional: when SMTP_HOST is unset, EmailService falls back to
    # logging the email instead of sending it, so invitations keep working
    # in local dev without real credentials.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@capstonepilot.app"
    SMTP_USE_TLS: bool = True


settings = Settings()
print("CORS_ORIGINS =", settings.CORS_ORIGINS)
