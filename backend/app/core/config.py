from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./capstonepilot.db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OPENROUTER_API_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

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
