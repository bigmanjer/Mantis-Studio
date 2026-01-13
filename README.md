# MANTIS Studio

## Docker setup guide

This guide walks you through running MANTIS Studio in Docker and connecting to local model servers (Ollama, LM Studio, llama.cpp) from inside the container.

### Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- A local model server if you want local inference:
  - **Ollama** on `http://localhost:11434`
  - **LM Studio** on `http://localhost:1234/v1`
  - **llama.cpp server** on `http://localhost:8080/v1`

### 1) Build the image

From the repo root:

```bash
docker build -t mantis-studio .
```

### 2) Run the container

```bash
docker run --rm -it \
  -p 8501:8501 \
  -v "${PWD}/projects:/app/projects" \
  mantis-studio
```

> **Note**: The app will be available at http://localhost:8501.

### 3) Connect to local model servers from Docker

`localhost` inside a container points **to the container itself**, not your host machine. Use one of the following instead:

- **Docker Desktop (Windows/macOS):** `host.docker.internal`
- **Linux Docker Engine:** your **host IP address** (e.g. `http://192.168.1.10:11434`)

In the app:

- **Ollama Base URL** → `http://host.docker.internal:11434`
- **LM Studio** → `http://host.docker.internal:1234/v1`
- **llama.cpp server** → `http://host.docker.internal:8080/v1`

### 4) (Optional) Set environment variables

You can override config values via environment variables:

```bash
docker run --rm -it \
  -p 8501:8501 \
  -v "${PWD}/projects:/app/projects" \
  -e OLLAMA_API_URL="http://host.docker.internal:11434" \
  -e OPENAI_API_URL="http://host.docker.internal:1234/v1" \
  mantis-studio
```

### 5) Troubleshooting

- **Connection fails with `localhost`** → switch to `host.docker.internal` or your host IP.
- **Linux host.docker.internal missing** → use the host’s LAN IP instead.
- **Firewall issues** → allow the model server to accept connections from Docker.

---

If you need a production-ready Dockerfile or compose setup, say the word and I’ll add one.
