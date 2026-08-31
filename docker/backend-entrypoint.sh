#!/bin/sh
set -eu

echo "[backend] applying database migrations..."
python manage.py migrate --noinput

echo "[backend] collecting Django static files..."
python manage.py collectstatic --noinput

echo "[backend] starting application server..."
exec "$@"
