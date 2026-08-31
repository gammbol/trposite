FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/requirements-container.txt /tmp/requirements-container.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements-container.txt

COPY backend /app/backend
COPY docker/backend-entrypoint.sh /usr/local/bin/trposite-backend-entrypoint

RUN chmod +x /usr/local/bin/trposite-backend-entrypoint

WORKDIR /app/backend

EXPOSE 8000

ENTRYPOINT ["trposite-backend-entrypoint"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
