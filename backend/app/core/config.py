from pydantic import field_validator
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
    #
    # GEMINI_API_KEY is the legacy single-key var, kept so an existing deployment
    # that only has this set keeps working unchanged. GEMINI_API_KEY_1/2/3 are the
    # preferred multi-key vars - set any number of them (1 is enough) to enable
    # automatic rotation past a rate-limited/quota-exhausted key in
    # infrastructure/agents/gemini_client.py. If any numbered key is set, the
    # numbered ones win outright (no mixing) - see GEMINI_API_KEYS below.
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    # "gemini-2.5-flash" and "gemini-2.5-flash-lite" both 404 as "no longer
    # available to new users" on this project's actual API key (confirmed live
    # against the real API, not assumed - same restriction Google applies to
    # several versioned model names for newer projects). "gemini-flash-lite-latest"
    # is Google's own always-current Flash-Lite alias and is what's actually
    # accessible; confirmed live (client.models.get) that it resolves to a real
    # "Gemini Flash-Lite Latest" model, not a relabeled regular Flash. Lightest
    # production Flash-tier model available to this key, replacing
    # "gemini-flash-latest" to cut cost and 503/high-demand errors.
    GEMINI_MODEL: str = "gemini-flash-lite-latest"

    @property
    def GEMINI_API_KEYS(self) -> list[str]:
        """The ordered pool of keys gemini_client.py rotates through. Prefers
        GEMINI_API_KEY_1/2/3 (whichever are non-empty, in order); if none of
        those are set at all, falls back to the single legacy GEMINI_API_KEY
        so a deployment with only that var still works normally."""
        numbered = [
            key
            for key in (self.GEMINI_API_KEY_1, self.GEMINI_API_KEY_2, self.GEMINI_API_KEY_3)
            if key
        ]
        if numbered:
            return numbered
        return [self.GEMINI_API_KEY] if self.GEMINI_API_KEY else []

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _strip_trailing_slashes(cls, origins: list[str]) -> list[str]:
        """CORSMiddleware's origin check is an exact string match against the
        browser's Origin header, which never has a trailing slash - a
        configured origin with one (an easy copy-paste mistake from a
        browser address bar or a hosting dashboard) silently fails every
        preflight from that origin with no indication why. Confirmed
        empirically: CORS_ORIGINS=["https://app.vercel.app/"] does not match
        an incoming Origin of "https://app.vercel.app". Normalizing here
        makes that whole class of mistake a non-issue."""
        return [origin.rstrip("/") for origin in origins]

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
