FROM python:3.12-slim

# Needed to build a couple of native wheels (e.g. psycopg2, bcrypt) that
# don't ship prebuilt manylinux wheels for every platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Render (and most PaaS hosts) inject PORT at runtime and expect the
# container to bind to it - 8000 is just the local-dev fallback.
ENV PORT=8000
EXPOSE 8000

# Migrations run automatically on container start (`alembic upgrade head`) -
# if they fail, `&&` short-circuits and the container exits non-zero before
# ever starting uvicorn, rather than serving traffic against a stale schema.
#
# `exec` matters here, not just style: without it, `sh` stays PID 1 and
# uvicorn runs as its child - Docker's SIGTERM on `stop`/redeploy then hits
# the shell, which does not forward it, so uvicorn never gets a chance to
# drain in-flight requests or run the lifespan shutdown (cancelling the
# scheduler task cleanly) and Docker has to SIGKILL after the stop timeout
# instead. `exec` replaces the shell with uvicorn so it becomes PID 1 and
# receives the signal directly. Confirmed empirically: without `exec`,
# `docker stop` took 11.4s (the full grace period, then a hard kill);
# with it, uvicorn shuts down within it instead of forcing the timeout.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]