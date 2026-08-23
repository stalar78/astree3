FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN python -m pip install --no-cache-dir . \
    && useradd --create-home --home-dir /home/astrea --shell /usr/sbin/nologin --uid 10001 astrea \
    && install -d -o astrea -g astrea /var/lib/astrea/private \
    && chown -R astrea:astrea /app/backend

USER astrea

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
