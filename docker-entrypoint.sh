#!/bin/sh
# Punto de entrada del contenedor ERP Django (local con docker-compose y Render)
set -e

echo "==> [entrypoint] Ejecutando migraciones..."
python manage.py migrate --noinput

echo "==> [entrypoint] Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> [entrypoint] Verificando configuración de Django..."
python manage.py check

echo "==> [entrypoint] Iniciando Gunicorn en el puerto ${PORT:-8000}..."
exec gunicorn core.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 120 \
    --log-file - \
    --access-logfile -
