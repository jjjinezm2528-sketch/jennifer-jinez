# ERP Django con WeasyPrint — Python 3.11 / Debian Bookworm
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libcairo-gobject2 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        fonts-liberation \
        fonts-dejavu-core \
        libjpeg62-turbo \
        libwebp7 \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY --chown=app:app . .

# Carpetas de escritura, creadas ANTES de que Docker inicialice los volúmenes
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app/staticfiles /app/media

USER app

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health/" -o /dev/null || exit 1

# "sh" evita depender del bit de ejecución (volumen en Windows)
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]