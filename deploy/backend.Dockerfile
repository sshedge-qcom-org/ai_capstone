FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY backend/pyproject.toml backend/requirements.lock ./
COPY backend/app ./app
RUN pip install --no-cache-dir --constraint requirements.lock . \
    && groupadd --gid 10001 procurement \
    && useradd --uid 10001 --gid procurement --no-create-home procurement \
    && mkdir -p /data/backups \
    && chown -R procurement:procurement /data
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY deploy/backend-entrypoint.sh /usr/local/bin/backend-entrypoint
RUN chmod 755 /usr/local/bin/backend-entrypoint

USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["backend-entrypoint"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
