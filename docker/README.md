# Containerized runtime

The container setup builds and runs the entire application without requiring a
local Python, Node.js, npm, Django, virtualenv or Ollama installation.

## Services

- **frontend** — multi-stage Node.js build followed by Nginx serving the React SPA.
- **backend** — Django under Gunicorn; migrations run automatically at startup.
- **ollama** — persistent local LLM runtime used by `OllamaSolver`.

Nginx exposes one public origin and proxies `/api/*` to Django over the private
Compose network. The React production build is compiled with
`REACT_APP_API_URL=/api`, so no host-specific API URL is embedded into the
bundle.

## Start

From the repository root:

```bash
chmod +x scripts/container.sh
./scripts/container.sh up
```

The application is then available at `http://localhost:8080` by default.

The first start pulls the configured Ollama model and can therefore take longer
than subsequent starts. Both the SQLite database and Ollama model files live in
Docker named volumes and survive `down`/`up` cycles.

## Configuration

If `.env` is absent, the script creates it from `.env.container.example`.
Relevant values include:

- `APP_PORT`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `OPENAI_API_KEY`
- `DEEP_SEEK_API_KEY`
- `OLLAMA_MODEL`

## Useful commands

```bash
./scripts/container.sh logs
./scripts/container.sh status
./scripts/container.sh check
./scripts/container.sh shell
./scripts/container.sh down
```

`clean` also deletes the persistent database and downloaded Ollama models, so it
asks for confirmation.

## GPU acceleration

An optional Compose override is provided for an NVIDIA Docker setup:

```bash
GPU=1 ./scripts/container.sh up
```

The normal CPU configuration remains the default and requires no GPU runtime.
