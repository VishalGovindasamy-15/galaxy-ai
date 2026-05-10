# Galaxy AI — The AI Engineering Operating System

> Build entire codebases with a single command. Galaxy orchestrates AI agents that plan, code, test, and validate — all locally.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
# Install
pip install galaxy-ai

# First-time setup (auto-detects GPU, installs Ollama, pulls models)
galaxy setup

# Build something (starts CLI + web dashboard together)
galaxy run "Build a REST API with user auth"
```

## What is Galaxy?

Galaxy is an **AI Engineering Operating System** — a hierarchical multi-agent system that builds production-grade software autonomously:

- 🧠 **Master Agent** — Architect. Decomposes projects into domains.
- 📋 **Domain Agents** — Managers. Plan and coordinate workers.
- ⚙️ **Worker Agents** — Builders. Write code, run tests, fix errors.

### Key Features

- **Local-first** — Runs on your hardware with Ollama. No cloud required.
- **Zero-config** — `galaxy setup` handles everything automatically.
- **Real-time dashboard** — Rich terminal UI + web dashboard (Galaxy Studio).
- **Test-as-you-build** — Every file validated immediately after generation.
- **Crash recovery** — Checkpoint and resume from any point.
- **5-level escalation** — Worker → Domain → Master → Model Fallback → User.

## Architecture

```
Master Agent (Architect)
  ├── Backend Domain Agent
  │   ├── Worker: models/user.py
  │   ├── Worker: routes/auth.py
  │   └── Worker: tests/test_auth.py
  ├── Frontend Domain Agent
  │   ├── Worker: components/Login.tsx
  │   └── Worker: pages/Dashboard.tsx
  └── DevOps Domain Agent
      ├── Worker: Dockerfile
      └── Worker: docker-compose.yml
```

## Commands

| Command | Description |
|---------|------------|
| `galaxy setup` | Auto-install deps, detect GPU, pull models |
| `galaxy run "..."` | Build a project (CLI + Studio start together) |
| `galaxy status` | Show current project status |
| `galaxy pause` | Pause execution with checkpoint |
| `galaxy resume` | Resume from last checkpoint |
| `galaxy init` | Initialize a Galaxy workspace |

## Documentation

- [Complete Specification](galaxy_complete_spec.md)
- [Implementation Guide](implementation_plan.md)

## License

MIT
