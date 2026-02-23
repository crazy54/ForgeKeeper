# ForgeKeeper

<p align="center">
  <img src="logo/Forge.png" alt="ForgeKeeper logo" width="520" />
</p>

<p align="center">
  <strong>The most capable polyglot developer container — batteries included, zero compromise.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/base-Ubuntu%2024.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white" alt="Ubuntu 24.04" />
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/devcontainer-compatible-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="Dev Container" />
  <img src="https://img.shields.io/badge/portal-port%207000-FF6B35?style=for-the-badge&logo=firefoxbrowser&logoColor=white" alt="Portal Port 7000" />
  <img src="https://img.shields.io/badge/Docker%20Hub-forgekeeper-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Hub" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Node.js-20%20LTS%20%7C%2022-339933?style=flat-square&logo=nodedotjs&logoColor=white" alt="Node.js" />
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Go-1.22-00ADD8?style=flat-square&logo=go&logoColor=white" alt="Go" />
  <img src="https://img.shields.io/badge/Rust-stable%20%2B%20nightly-CE422B?style=flat-square&logo=rust&logoColor=white" alt="Rust" />
  <img src="https://img.shields.io/badge/JDK-17%20%7C%2021-ED8B00?style=flat-square&logo=openjdk&logoColor=white" alt="JDK" />
  <img src="https://img.shields.io/badge/.NET-7%20%7C%208-512BD4?style=flat-square&logo=dotnet&logoColor=white" alt=".NET" />
  <img src="https://img.shields.io/badge/Kotlin-1.9-7F52FF?style=flat-square&logo=kotlin&logoColor=white" alt="Kotlin" />
  <img src="https://img.shields.io/badge/Swift-5.10-F05138?style=flat-square&logo=swift&logoColor=white" alt="Swift" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Terraform-1.7-7B42BC?style=flat-square&logo=terraform&logoColor=white" alt="Terraform" />
  <img src="https://img.shields.io/badge/kubectl-latest-326CE5?style=flat-square&logo=kubernetes&logoColor=white" alt="kubectl" />
  <img src="https://img.shields.io/badge/Helm-3.15-0F1689?style=flat-square&logo=helm&logoColor=white" alt="Helm" />
  <img src="https://img.shields.io/badge/AWS%20CLI-v2-FF9900?style=flat-square&logo=amazonaws&logoColor=white" alt="AWS CLI" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Ollama-local%20LLMs-000000?style=flat-square&logo=ollama&logoColor=white" alt="Ollama" />
  <img src="https://img.shields.io/badge/Open%20WebUI-port%208085-5C5CFF?style=flat-square&logo=openai&logoColor=white" alt="Open WebUI" />
  <img src="https://img.shields.io/badge/LiteLLM-proxy%20gateway-FF6B35?style=flat-square&logo=lightning&logoColor=white" alt="LiteLLM" />
  <img src="https://img.shields.io/badge/Flowise-LLM%20workflows-00C4CC?style=flat-square&logo=node.js&logoColor=white" alt="Flowise" />
  <img src="https://img.shields.io/badge/Aider-AI%20pair%20programmer-6E40C9?style=flat-square&logo=github&logoColor=white" alt="Aider" />
  <img src="https://img.shields.io/badge/AnythingLLM-RAG%20chat-F59E0B?style=flat-square&logo=files&logoColor=white" alt="AnythingLLM" />
</p>

---

## Screenshots

**Step 1 — Launch the setup wizard**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153118.png" alt="Setup wizard — step 1" width="700" />
</p>

**Step 2 — Identity & workspace configuration**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153125.png" alt="Setup wizard — step 2" width="700" />
</p>

**Step 3 — Language runtime selection**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153238.png" alt="Setup wizard — step 3" width="700" />
</p>

**Step 4 — Credentials & API keys**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153250.png" alt="Setup wizard — step 4" width="700" />
</p>

**Step 5 — Build trigger & live log**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153307.png" alt="Setup wizard — step 5" width="700" />
</p>

**Step 6 — Container ready & portal launch**
<p align="center">
  <img src="logo/Screenshot 2026-02-20 153326.png" alt="Setup wizard — step 6" width="700" />
</p>

---

## Project Structure

```
forgekeeper/
├── Dockerfile                  # Base image (no language runtimes)
├── docker-compose.yml
├── devcontainer.json
├── dockerfiles/                # Language module snippets
│   ├── lang-python.dockerfile
│   ├── lang-node.dockerfile
│   ├── lang-go.dockerfile
│   ├── lang-rust.dockerfile
│   ├── lang-java.dockerfile
│   ├── lang-dotnet.dockerfile
│   ├── lang-ruby.dockerfile
│   ├── lang-php.dockerfile
│   ├── lang-swift.dockerfile
│   └── lang-dart.dockerfile
├── portal/                     # In-container web portal (port 7000)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── config.js
│   └── server.py               # Portal HTTP server + API endpoints
├── setup-ui/                   # Setup wizard UI (shared Flow A + B)
│   ├── index.html
│   ├── setup.js
│   └── setup.css
├── scripts/
│   ├── setup.py                # Flow A: pre-build wizard server (host)
│   ├── install-lang.sh         # Runtime installer (inside container)
│   └── forgekeeper-control.sh  # Shutdown / reset control script
├── logo/
│   └── Forge.png
└── .github/workflows/
    └── docker-publish.yml      # Auto-publish to Docker Hub on push
```

---

## Setup Wizard

### Flow A — Pre-build (source)

`python3 scripts/setup.py` spins up a local server on port `7001`, opens your browser, and walks you through:

- Identity (handle, email, workspace)
- Language picker (only selected runtimes are compiled in)
- Credentials (written to `.env` on your host, never baked into the image)
- Build trigger (assembles `Dockerfile.built` and runs `docker compose up --build`)

### Flow B — First-run (pre-built image)

The portal server checks for `/etc/forgekeeper/.setup-complete` on every request to `/`. If missing, it redirects to `/setup`. The same wizard UI runs inside the container, POSTs config to `/forgekeeper/setup`, writes `/etc/forgekeeper/env`, installs selected language runtimes via `forgekeeper-runtime`, and marks setup complete.

Resetting the container wipes `.setup-complete` so the wizard runs again on next boot.

---

## Importing from devcontainer.json

Already have a `devcontainer.json`? ForgeKeeper can import it to auto-detect your language runtimes, environment variables, and forwarded ports — no manual selection needed.

### How it works

The import option appears on **Step 2 (Language Selection)** of the setup wizard in both Flow A and Flow B. You can either upload a file or point to a path on disk.

**File upload** — click the upload button and select your `.json` file.

**Path import** — enter the path to your `devcontainer.json` (e.g. `/workspaces/.devcontainer/devcontainer.json` in Flow B) and click Load.

After import, a preview modal shows what was detected. You can review and edit the selections before applying them to the wizard.

### What gets imported

| Property | Source in devcontainer.json | How it's used |
|---|---|---|
| Language runtimes | `features` + `image` | Pre-selects languages in the wizard grid |
| Environment variables | `remoteEnv` | Written to `.env` (Flow A) or `/etc/forgekeeper/env` (Flow B) |
| Forwarded ports | `forwardPorts` | Documented for reference; validated (1–65535) |
| Unrecognized features | Any feature not in the mapping table | Shown as warnings in the preview |

### Supported language mappings

ForgeKeeper recognizes these devcontainer feature patterns:

| ForgeKeeper Runtime | Devcontainer Feature Prefixes |
|---|---|
| `python` | `ghcr.io/devcontainers/features/python`, `ghcr.io/devcontainers-contrib/features/python` |
| `node` | `ghcr.io/devcontainers/features/node`, `ghcr.io/devcontainers-contrib/features/node` |
| `go` | `ghcr.io/devcontainers/features/go`, `ghcr.io/devcontainers-contrib/features/go` |
| `rust` | `ghcr.io/devcontainers/features/rust`, `ghcr.io/devcontainers-contrib/features/rust` |
| `java` | `ghcr.io/devcontainers/features/java`, `ghcr.io/devcontainers-contrib/features/java` |
| `dotnet` | `ghcr.io/devcontainers/features/dotnet`, `ghcr.io/microsoft/devcontainers/features/dotnet` |
| `ruby` | `ghcr.io/devcontainers/features/ruby`, `ghcr.io/devcontainers-contrib/features/ruby` |
| `php` | `ghcr.io/devcontainers/features/php`, `ghcr.io/devcontainers-contrib/features/php` |

Languages are also detected from the base `image` name (e.g. `python:3.11` → python, `node:20` → node).

### Example devcontainer.json

```json
{
  "name": "My Project",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu-24.04",
  "features": {
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" },
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/go:1": { "version": "1.22" },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "forwardPorts": [3000, 8080, 5432],
  "remoteEnv": {
    "APP_ENV": "development",
    "DATABASE_URL": "postgresql://localhost:5432/mydb"
  },
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "golang.go"]
    }
  }
}
```

Importing this file would:
- Pre-select **python**, **node**, and **go** in the language grid
- Set `APP_ENV` and `DATABASE_URL` as environment variables
- List ports 3000, 8080, and 5432 in the preview
- Flag `docker-in-docker` as an unrecognized feature (Docker is pre-installed in ForgeKeeper)

### API endpoints

**Flow A** (pre-build wizard on host, port 7001):

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/setup/import-devcontainer` | Upload a devcontainer.json file (multipart form data) |
| `POST` | `/setup/import-devcontainer-path` | Import from a file path (JSON body: `{"path": "..."}`) |

**Flow B** (first-run wizard inside container, port 7000):

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/forgekeeper/import-devcontainer` | Upload a devcontainer.json file (multipart form data) |
| `POST` | `/forgekeeper/import-devcontainer-path` | Import from a file path (JSON body: `{"path": "..."}`) |

Both endpoints return JSON with `success`, `mapping` (languages, env_vars, ports, warnings), and `errors` fields.

### Security

- File uploads are limited to 1 MB
- Path imports are validated against path traversal attacks
- Sensitive environment variables (containing `token`, `key`, `secret`, `password`, etc.) are masked in the preview
- Port numbers are validated to the 1–65535 range

---

- [ForgeKeeper](#forgekeeper)
  - [Table of Contents](#table-of-contents)
  - [Vision \& Pillars](#vision--pillars)
  - [Quick Start](#quick-start)
  - [Hosted Services](#hosted-services)
    - [AI \& LLMs](#ai--llms)
    - [IDEs \& Editors](#ides--editors)
    - [Terminals](#terminals)
    - [Data \& ML](#data--ml)
    - [Database UIs](#database-uis)
    - [Observability](#observability)
    - [Container \& Infra](#container--infra)
    - [API \& Docs](#api--docs)
    - [Portal](#portal)
    - [Portal Controls](#portal-controls)
  - [Base Image \& Layering](#base-image--layering)
  - [Core System Packages](#core-system-packages)
  - [Runtimes \& Languages](#runtimes--languages)
    - [JavaScript / TypeScript / Front-end](#javascript--typescript--front-end)
    - [Python \& Data](#python--data)
    - [Go](#go)
    - [Rust](#rust)
    - [JVM \& Polyglot](#jvm--polyglot)
    - [.NET \& C#](#net--c)
    - [Other Languages](#other-languages)
  - [AI Tooling](#ai-tooling)
    - [Hosted UIs](#hosted-uis)
    - [Local LLM Runtime (Ollama)](#local-llm-runtime-ollama)
    - [CLI AI Tools](#cli-ai-tools)
    - [LiteLLM Proxy — unified API](#litellm-proxy--unified-api)
  - [Container, Cloud \& Infra Tooling](#container-cloud--infra-tooling)
    - [Containers \& Orchestration](#containers--orchestration)
    - [HashiCorp Stack](#hashicorp-stack)
    - [Cloud SDKs](#cloud-sdks)
    - [IaC \& Policy](#iac--policy)
  - [Observability \& QA](#observability--qa)
  - [Local Services](#local-services)
  - [Developer Ergonomics](#developer-ergonomics)
    - [Shell \& Prompt](#shell--prompt)
    - [Editors](#editors)
    - [Git Experience](#git-experience)
  - [Inside-Container Workflows](#inside-container-workflows)
    - [Automation Scripts (`justfile`)](#automation-scripts-justfile)
    - [Lifecycle Hooks (`devcontainer.json`)](#lifecycle-hooks-devcontainerjson)
    - [Daily Developer Flow](#daily-developer-flow)
    - [Branding \& Session Personalization](#branding--session-personalization)
  - [Security \& Compliance](#security--compliance)
  - [Performance \& Caching](#performance--caching)
  - [Local Orchestration](#local-orchestration)
  - [Next Steps](#next-steps)

---

## Vision & Pillars

| Pillar | Description |
|---|---|
| 🌐 **Polyglot first** | Ready for web, backend, infrastructure, and ML — no extra installs needed |
| ⚡ **Fast feedback** | Opinionated tooling, formatters, and task runners make tests, lint, and builds one command away |
| 🔒 **Hermetic yet extensible** | Deterministic installs via pinned versions, easy overrides through `mise`/`asdf` |
| 🛡️ **Secure by default** | Secrets handling, scanning, and least-privileged defaults baked in |
| 🎨 **Delightful ergonomics** | Pre-tuned shell, editors, prompt, and helpers for day-to-day work |

---

## Quick Start

There are two ways to get ForgeKeeper running depending on whether you want to build from source or pull a pre-built image.

### Flow A — Build from source (recommended)

Run the interactive setup wizard on your host. It collects your config, lets you pick which language runtimes to include, writes `.env`, assembles a lean custom `Dockerfile.built`, then builds and starts the container — all from a browser UI.

```bash
git clone <your-repo-url> forgekeeper
cd forgekeeper
python3 scripts/setup.py
```

Your browser opens automatically at [http://localhost:7001](http://localhost:7001). Walk through the 4-step wizard:

1. Identity — handle, email, workspace name
2. Languages — pick only what you need (Python, Node, Go, Rust, Java, .NET, Ruby, PHP, Swift, Dart)
3. Credentials — API keys, GitHub token, AWS region (all optional, stored in `.env` only)
4. Build — hit "Build Container" and watch the live log

Once built, the portal is at [http://localhost:7000](http://localhost:7000).

> **VS Code users:** Open the folder and select **Reopen in Container** after the build completes.

### Flow B — Pre-built image from Docker Hub

Pull the base image (no language runtimes baked in — lean by default) and run it. On first load the portal redirects to the setup wizard automatically.

```bash
docker pull forgekeeper/forgekeeper:latest
docker run -d \
  -p 7000:7000 -p 8080:8080 -p 7681:7681 \
  -p 11434:11434 -p 8085:8085 \
  --name forgekeeper \
  forgekeeper/forgekeeper:latest
```

Open [http://localhost:7000](http://localhost:7000) — the setup wizard runs on first boot, collects your config, and installs your chosen language runtimes into the running container. No rebuild needed.

### Adding languages after setup

From the portal — open the **Language Runtimes** panel and click Install/Remove on any runtime.

From the CLI inside the container:

```bash
forgekeeper-runtime install python
forgekeeper-runtime install go
forgekeeper-runtime remove ruby
forgekeeper-runtime list
```

---

## Hosted Services

Once the container is running, the following services are available:

### AI & LLMs

| Service | Port | Description |
|---|---|---|
| 🤖 **Open WebUI** | `8085` | ChatGPT-style UI for Ollama and any OpenAI-compatible API |
| 🦙 **Ollama** | `11434` | Local LLM runtime — run Llama 3, Mistral, CodeLlama offline, no API key needed |
| 📂 **AnythingLLM** | `3003` | RAG-powered chat over your own documents and codebase |
| 🔗 **Flowise** | `3004` | Visual drag-and-drop LLM workflow and agent builder |
| 🔀 **LiteLLM Proxy** | `4000` | Unified API gateway — one endpoint for OpenAI, Anthropic, Bedrock, Ollama |

### IDEs & Editors

| Service | Port | Description |
|---|---|---|
| 🛠️ **VS Code Server** | `8080` | Full VS Code in any browser |
| 🧭 **OpenVSCode Server** | `3000` | Lightweight VS Code from Microsoft sources |

### Terminals

| Service | Port | Description |
|---|---|---|
| 💻 **ttyd Terminal** | `7681` | Browser-based zsh/tmux with personalized MOTD |
| 🖥️ **Wetty Terminal** | `3002` | SSH-over-HTTP terminal — full shell in a browser tab |

### Data & ML

| Service | Port | Description |
|---|---|---|
| 📓 **JupyterLab** | `8888` | Data notebooks with ForgeKeeper kernels |
| 📈 **MLflow UI** | `5000` | Track experiments, parameters, and metrics |
| 🧠 **TensorBoard** | `6006` | Visualize training runs and scalars |

### Database UIs

| Service | Port | Description |
|---|---|---|
| 🐘 **pgAdmin** | `5050` | Full-featured PostgreSQL administration and query tool |
| 🗄️ **Adminer** | `8082` | Lightweight DB admin for PostgreSQL, MySQL, SQLite, and more |
| 🔴 **RedisInsight** | `8001` | Visual browser and profiler for Redis data structures |
| 🍃 **Mongo Express** | `8081` | Web-based MongoDB admin interface |

### Observability

| Service | Port | Description |
|---|---|---|
| 📊 **Grafana** | `3001` | Dashboards for metrics, logs, and traces from any source |
| 🔥 **Prometheus** | `9090` | Metrics scraping and alerting — query with PromQL |
| 🔭 **Jaeger UI** | `16686` | Distributed tracing — visualize request flows across services |
| ⚡ **Netdata** | `19999` | Real-time system performance: CPU, memory, disk, network |

### Container & Infra

| Service | Port | Description |
|---|---|---|
| 🐳 **Portainer** | `9000` | Docker container management — start, stop, inspect, and log |

### API & Docs

| Service | Port | Description |
|---|---|---|
| 📋 **Swagger UI** | `8083` | Interactive OpenAPI documentation and live API testing |
| 📚 **MkDocs** | `8084` | Live preview of your project documentation site |

### Portal

| Service | Port | Description |
|---|---|---|
| 🔥 **ForgeKeeper Portal** | `7000` | Dashboard for all hosted tooling + container controls |

### Portal Controls

The portal at `/forgekeeper/control` (served by `portal/server.py`) exposes two actions:

- **Shutdown** — sends `SIGTERM` to PID 1, stopping the container gracefully
- **Reset** — wipes `/workspaces/*` and restarts supervised services

Extend `scripts/forgekeeper-control.sh` for enterprise-grade automation.

---

## Base Image & Layering

```
mcr.microsoft.com/devcontainers/base:ubuntu-24.04
  └── Locale/timezone (UTF-8, UTC)
      └── Non-root user: `vscode` (passwordless sudo, docker group, zsh)
          └── Dotfiles bootstrap (Git-based, cached to /workspaces/.cache/dotfiles)
```

---

## Core System Packages

<details>
<summary>Build & Compiler Toolchain</summary>

`build-essential` · `cmake` · `ninja-build` · `pkg-config` · `gdb` · `lldb` · `valgrind` · `clang` · `clangd`

</details>

<details>
<summary>Shell & Terminal Utilities</summary>

`zsh` · `fish` · `tmux` · `zellij` · `starship` · `fzf` · `ripgrep` · `fd` · `bat` · `delta` · `direnv` · `just` · `gh` · `gpg` · `neovim` · `helix`

</details>

<details>
<summary>Networking & Diagnostics</summary>

`netcat-openbsd` · `iperf3` · `httpie` · `curl` · `wget` · `jq` · `yq` · `dnsutils` · `traceroute`

</details>

<details>
<summary>Monitoring & Troubleshooting</summary>

`htop` · `btop` · `glances` · `iotop` · `iftop` · `nvtop` · `strace` · `lsof` · `sysstat` · `procs`

</details>

<details>
<summary>Fonts</summary>

JetBrains Mono Nerd Font · Fira Code — copied to `/usr/local/share/fonts` for GUI editor attachments.

</details>

---

## Runtimes & Languages

### JavaScript / TypeScript / Front-end

![Node.js](https://img.shields.io/badge/Node.js-20%20LTS%20%7C%2022-339933?style=flat-square&logo=nodedotjs&logoColor=white)
![Bun](https://img.shields.io/badge/Bun-latest-000000?style=flat-square&logo=bun&logoColor=white)
![Deno](https://img.shields.io/badge/Deno-latest-000000?style=flat-square&logo=deno&logoColor=white)

Installed via `mise`. `corepack enable` activates Yarn/PNPM. Extras: `bun`, `deno`, `eslint`, `prettier`, `tsc`, `vitest`, `playwright`, `turborepo`.

### Python & Data

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/JupyterLab-latest-F37626?style=flat-square&logo=jupyter&logoColor=white)

CPython 3.12 + 3.11 via `mise`. `uv` for dependency resolution. Includes `pipx`, `poetry`, `rye`, `tox`, `pytest`, `ruff`, `black`, `mypy`.

Data tooling: `jupyterlab`, `pandas`, `numpy`, `scipy`, `polars`, `matplotlib`, `scikit-learn`. CUDA toolkits optional via build arg.

### Go

![Go](https://img.shields.io/badge/Go-1.22-00ADD8?style=flat-square&logo=go&logoColor=white)

Go 1.22 with `delve`, `gofumpt`, `golangci-lint`, `air` (live reload), `mockgen`.

### Rust

![Rust](https://img.shields.io/badge/Rust-stable%20%2B%20nightly-CE422B?style=flat-square&logo=rust&logoColor=white)

`rustup` with stable + nightly toolchains, `clippy`, `rustfmt`, `cargo-nextest`, `cargo-watch`, `wasm32` target.

### JVM & Polyglot

![Java](https://img.shields.io/badge/JDK-17%20%7C%2021-ED8B00?style=flat-square&logo=openjdk&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-1.9-7F52FF?style=flat-square&logo=kotlin&logoColor=white)

Temurin JDK 21 + 17, `maven`, `gradle`, `coursier`, Kotlin compiler, Scala (via sbt).

### .NET & C\#

![.NET](https://img.shields.io/badge/.NET-7%20%7C%208-512BD4?style=flat-square&logo=dotnet&logoColor=white)

.NET SDK 8.0 + 7.0, `omnisharp`, `dotnet-ef`, `dotnet-script`.

### Other Languages

| Language | Version | Notes |
|---|---|---|
| Ruby | 3.3 | rbenv via mise, `bundler`, `jekyll` |
| PHP | 8.3 | Composer included |
| Elixir/Erlang | latest | via mise, `hex`, `rebar3` |
| Swift | 5.10 | Full toolchain |
| Dart | stable | SDK included |

---

## AI Tooling

ForgeKeeper ships a full local AI stack — no API keys required to get started.

### Hosted UIs

| Tool | Port | Description |
|---|---|---|
| 🤖 **Open WebUI** | `8085` | ChatGPT-style interface connected to Ollama out of the box |
| 📂 **AnythingLLM** | `3003` | RAG over your workspace — drop in docs, code, PDFs and chat with them |
| 🔗 **Flowise** | `3004` | Visual LLM workflow builder — chain tools, agents, and memory without code |
| 🔀 **LiteLLM Proxy** | `4000` | Single OpenAI-compatible endpoint that routes to any backend |

### Local LLM Runtime (Ollama)

Ollama starts automatically and serves models on port `11434`. Pull any model at runtime:

```bash
ollama pull llama3          # Meta Llama 3 8B — great all-rounder
ollama pull codellama       # Code-focused Llama variant
ollama pull mistral         # Mistral 7B — fast and capable
ollama pull phi3            # Microsoft Phi-3 — small but punchy
ollama pull deepseek-coder  # DeepSeek Coder — strong at code generation
ollama list                 # see what's installed
```

Open WebUI auto-connects to Ollama — just open [http://localhost:8085](http://localhost:8085) and start chatting.

### CLI AI Tools

These are available in every shell session:

```bash
# Aider — AI pair programmer that edits your actual files
aider --model ollama/codellama file.py
aider --model gpt-4o file.py          # swap to OpenAI if key is set

# llm — quick one-liners from the terminal
llm "explain this bash script" < script.sh
llm -m ollama/llama3 "write a Dockerfile for a Node app"

# Fabric — run AI prompts as pipelines
cat README.md | fabric --pattern summarize
cat error.log | fabric --pattern explain_code
```

### LiteLLM Proxy — unified API

All tools in the container can point to `http://localhost:4000` and get routed to whichever backend is configured. Set env vars to unlock cloud providers:

```bash
# .env or docker-compose environment
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# Ollama is always available with no key
```

---

## Container, Cloud & Infra Tooling

### Containers & Orchestration

![Docker](https://img.shields.io/badge/Docker-CLI%20%2B%20Compose%20v2-2496ED?style=flat-square&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-kubectl%20%7C%20helm%20%7C%20k9s-326CE5?style=flat-square&logo=kubernetes&logoColor=white)

`docker`, `docker compose`, `nerdctl`, `buildx`, `dive` · `kubectl`, `helm`, `kustomize`, `kind`, `minikube`, `skaffold`, `k9s`

### HashiCorp Stack

![Terraform](https://img.shields.io/badge/Terraform-1.7-7B42BC?style=flat-square&logo=terraform&logoColor=white)

`terraform`, `packer`, `vault`, `consul`, `nomad`, `boundary`

### Cloud SDKs

![AWS](https://img.shields.io/badge/AWS%20CLI-v2-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![GCP](https://img.shields.io/badge/gcloud-latest-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Azure](https://img.shields.io/badge/az-latest-0078D4?style=flat-square&logo=microsoftazure&logoColor=white)

`awscli`, `aws-vault`, `sam` · `gcloud` · `az` · `doctl`, `flyctl`, `heroku`, `supabase`, `vercel`, `netlify`

### IaC & Policy

`ansible`, `pulumi`, `cue`, `opa`, `conftest`

---

## Observability & QA

| Category | Tools |
|---|---|
| Testing | `act`, `tilt`, `k6`, `locust`, `newman`, `mockoon-cli` |
| Debug Proxies | `mitmproxy`, `ngrok`, `cloudflared`, `httptoolkit-server` |
| Tracing/Logging | `otel-cli`, `stern`, `kubetail` |
| Security Scanning | `semgrep`, `trivy`, `grype`, `syft`, `gitleaks`, `bandit`, `cargo-audit` |

---

## Local Services

Provisioned via `docker-compose` inside the devcontainer — toggle per project:

<details>
<summary>Datastores</summary>

PostgreSQL 16 · MySQL 8 · Redis 7 · KeyDB · MongoDB 7 · Elasticsearch/OpenSearch · Meilisearch · MinIO · RabbitMQ · Kafka/Redpanda · LocalStack · Azurite · MailHog · Temporal · NATS

</details>

<details>
<summary>Feature Flags & Testing</summary>

Flipt · Testcontainers CLI

</details>

<details>
<summary>Reverse Proxies</summary>

Caddy · Traefik (TLS termination during dev)

</details>

<details>
<summary>Ops Dashboards</summary>

Portainer · Lazydocker · pgAdmin · Adminer · RedisInsight · Meilisearch console

</details>

---

## Developer Ergonomics

### Shell & Prompt

- **zsh** default with Oh My Zsh, starship prompt, autosuggestions, syntax highlighting
- `direnv` hooks, alias pack for `kubectl`/`terraform`
- `tmux` with `tmuxinator forgekeeper.yml`, Zellij layout (editor/tests/logs panes)

### Editors

- VS Code extensions pre-installed: ESLint, Prettier, Python, Rust Analyzer, Go, Docker, YAML, Terraform, GitHub Copilot
- Neovim nightly with LazyVim distribution
- Helix for lightweight editing

### Git Experience

`lazygit` · `forgit` · commit template · conventional commits CLI · `pre-commit` with shared hook set

---

## Inside-Container Workflows

### Automation Scripts (`justfile`)

```bash
just bootstrap   # Sync dotfiles, install mise tools, fetch git hooks, install VS Code extensions
just update      # Refresh packages, run security scanners, update lockfiles, regenerate SBOM
just qa          # Formatters, linters, unit tests, coverage, type checks for every language
just db.up       # Stand up docker-compose defined services
just db.down     # Tear down docker-compose defined services
just ship        # Build image, run integration tests, produce release artifacts
just status      # Print versions, running services, disk usage, network forwarding info
```

### Lifecycle Hooks (`devcontainer.json`)

| Hook | Action |
|---|---|
| `onCreateCommand` | `just bootstrap` + `pre-commit install` + `mise install` + `direnv allow` |
| `postCreateCommand` | Seed databases, run migrations, start background watchers |
| `postStartCommand` | Launch `tmuxinator forgekeeper`, attach to tmux, present status dashboard |
| `postAttachCommand` | Run `mise doctor`, print versions, tail logs |

### Daily Developer Flow

```
1. Attach      → drop into tmux (editor + just monitor + k9s panes)
2. Sync        → mise install  (matches .tool-versions)
3. Start deps  → just db.up
4. Watch       → npm run dev / air / cargo watch -x check
5. QA loop     → just qa
6. Preflight   → just ship  (SBOM + trivy scan + changelog)
```

### Branding & Session Personalization

Set these env vars before building to personalize banners, MOTD, and Docker labels:

```bash
FORGEKEEPER_USER_EMAIL="you@example.com"
FORGEKEEPER_HANDLE="yourhandle"
FORGEKEEPER_WORKSPACE="myproject"
```

On first attach: `gum format` + `figlet` + `lolcat` render the ForgeKeeper badge, followed by a `cowsay` session summary.

---

## Security & Compliance

| Area | Tools |
|---|---|
| Secrets management | `1password-cli`, `aws-vault`, `doppler`, `sops`, `age` |
| Pre-commit hooks | `detect-secrets`, `checkov`, `eslint --max-warnings=0`, `ruff`, `go fmt`, `terraform fmt`, `hadolint` |
| Image scanning | Nightly `trivy image forgekeeper` + SBOM via `syft` committed to `sbom/` |
| Supply chain | `cosign` for signing, `slsa-verifier` for verifying upstream binaries |

> Secrets mount point: `/workspaces/.secrets` (git-ignored templates provided).

---

## Performance & Caching

- Docker build cache mounts for `npm`, `pip`, `go`, `cargo` package managers
- Host `~/.ssh` mounted read-only via `vscode-remote.tryWorkspaceMount`
- Optional remote cache: `bazelisk` with RBE stub, `buildkitd` with `BUILDKIT_PROGRESS=plain`
- Global caches persisted to `/workspaces/.cache` — survive container rebuilds

---

## Local Orchestration

```bash
# Boot the full stack locally
docker compose up --build forgekeeper

# Attach with VS Code Remote Containers
# Set FORGEKEEPER_* env vars before rebuild to personalize banners

# Supervisor manages: code-server, openvscode, Jupyter, ttyd, MLflow, Portal
# Logs: /var/log/forgekeeper/
```

Healthcheck script ensures runtime managers, watchers, and services are up — surfaces results in VS Code "Ports" / "Dev Containers" panels.

---

## Next Steps

- Wire `/forgekeeper/control` to your orchestration (or extend `forgekeeper-control.sh`) for production-grade shutdown/reset approvals
- Set up nightly `docker build && docker push` via GitHub Actions and add the resulting status badge to this README
- Document onboarding and architecture diagrams for the hosted service mesh
- Connect `FORGEKEEPER_*` env vars to your secrets manager for team-wide personalization

---

<p align="center">
  <img src="logo/Forge.png" alt="ForgeKeeper" width="80" />
  <br/>
  <sub>Built with 🔥 by the ForgeKeeper project</sub>
</p>
