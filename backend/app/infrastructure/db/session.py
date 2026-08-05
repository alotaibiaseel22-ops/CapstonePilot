from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

if _is_sqlite:
    # SQLite does not enforce foreign keys (or their ON DELETE CASCADE
    # actions) unless told to, per connection - without this, the
    # ondelete="CASCADE" on every project-child FK is silently inert here,
    # local dev/tests would never exercise it, and the exact class of bug
    # this was added to fix (a forgotten child table causing a real FK
    # violation in production Postgres, which always enforces this) would
    # keep passing locally right up until the next deploy.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
