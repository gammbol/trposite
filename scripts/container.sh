#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ACTION="${1:-up}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3}"
GPU="${GPU:-0}"

compose() {
    if [[ "$GPU" == "1" ]]; then
        docker compose -f docker-compose.yml -f docker-compose.gpu.yml "$@"
    else
        docker compose -f docker-compose.yml "$@"
    fi
}

ensure_env() {
    if [[ ! -f .env ]]; then
        cp .env.container.example .env
        echo "[trposite] created .env from .env.container.example"
        echo "[trposite] review .env if you need cloud API keys or production settings"
    fi
}

wait_for_ollama() {
    echo "[trposite] waiting for Ollama..."
    for _ in $(seq 1 60); do
        if compose exec -T ollama ollama list >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "[trposite] Ollama did not become ready in time" >&2
    return 1
}

pull_model() {
    wait_for_ollama
    echo "[trposite] ensuring Ollama model '${OLLAMA_MODEL}' is available..."
    compose exec -T ollama ollama pull "$OLLAMA_MODEL"
}

case "$ACTION" in
    up)
        ensure_env
        compose up -d --build
        pull_model
        echo
        echo "Trposite is running: http://localhost:${APP_PORT:-8080}"
        echo "History:             http://localhost:${APP_PORT:-8080}/history"
        echo "Django admin:        http://localhost:${APP_PORT:-8080}/admin/"
        ;;
    rebuild)
        ensure_env
        compose build --no-cache
        compose up -d
        pull_model
        echo
        echo "Trposite is running: http://localhost:${APP_PORT:-8080}"
        ;;
    down)
        compose down
        ;;
    clean)
        echo "This removes containers AND persistent SQLite/Ollama volumes."
        read -r -p "Continue? [y/N] " answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            compose down -v --remove-orphans
        fi
        ;;
    restart)
        compose restart
        ;;
    logs)
        compose logs -f --tail=200
        ;;
    status|ps)
        compose ps
        ;;
    shell)
        compose exec backend /bin/sh
        ;;
    model)
        ensure_env
        compose up -d ollama
        pull_model
        ;;
    migrate)
        compose exec backend python manage.py migrate
        ;;
    admin|superuser)
        compose exec backend python manage.py createsuperuser
        ;;
    check)
        compose exec backend python manage.py check
        ;;
    *)
        cat <<USAGE
Usage: $0 [command]
Commands:
  up         Build and start frontend, backend and Ollama (default)
  rebuild    Rebuild all images without cache and restart
  down       Stop the stack without deleting persistent data
  clean      Stop the stack and delete SQLite/Ollama volumes
  restart    Restart running services
  logs       Follow logs from all services
  status     Show container status
  shell      Open a shell inside the Django container
  model      Start Ollama and pull the configured model
  migrate    Run Django migrations manually
  admin      Create a Django admin superuser
  check      Run 'python manage.py check' in the backend container
Environment:
  APP_PORT=8080      Public web port
  OLLAMA_MODEL=llama3
  GPU=1              Add docker-compose.gpu.yml (NVIDIA Docker runtime required)
USAGE
        exit 1
        ;;
esac
