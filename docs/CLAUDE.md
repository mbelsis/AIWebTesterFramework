# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI WebTester is a Python framework for automated web application testing combining Playwright browser automation, OpenAI-powered test generation, and real-time monitoring via a Control Room dashboard.

## Build & Setup

```bash
./setup.sh                        # Automated setup
pip install -e ".[dev]"           # Manual install with dev deps
playwright install                # Install browser engines
```

## Common Commands

```bash
# Run tests
pytest tests/

# Run a single test file
pytest tests/test_redaction.py

# Linting and formatting
black --check --line-length 100 .
ruff check .
mypy .

# CLI commands
python -m cli.main run --plan examples/plan.login.yaml --env examples/env.login.yaml --control-room
python -m cli.main generate https://app.com --description "test login"
python -m cli.main control-room
python -m cli.main mock-app

# Quick demo
python run_test.py
```

## Architecture

The framework follows an async-first design with these key layers:

- **CLI** (`cli/main.py`): Typer app with commands: `run`, `generate`, `control-room`, `mock-app`. Entry point: `cli.main:app`.
- **TestGraph** (`orchestrator/graph.py`): Main orchestrator — loads YAML plan/env configs, manages browser lifecycle, coordinates execution, collects evidence, produces `run.json` and `run_summary.json`.
- **Executor** (`orchestrator/executor.py`): Executes individual test steps (navigate, click, fill, submit, wait, verify). Integrates with Watchdog for stuck-screen recovery and Control Room for live updates.
- **TestPlanGenerator** (`orchestrator/test_plan_generator.py`): AI-powered — analyzes pages via PageAnalyzer, sends to OpenAI, outputs YAML test plans with seeded test data.
- **PageAnalyzer** (`orchestrator/page_analyzer.py`): Extracts interactive elements and page structure using Playwright + BeautifulSoup.
- **ControlRoom** (`orchestrator/control_room.py`): FastAPI + WebSocket server for real-time monitoring. Streams status, steps, logs, and screenshots.
- **BrowserContext** (`browser/context.py`): Playwright wrapper handling recording, DOM/pixel state capture, and video/trace finalization.
- **EvidenceSink** (`evidence/sink.py`): Collects screenshots, logs, and artifacts with security redaction applied.
- **SecurityRedactor** (`utils/redaction.py`): 21 regex patterns for redacting sensitive data (tokens, API keys, PII, credentials). Patterns defined in `configs/security.yaml`.
- **Watchdog** (`utils/watchdog.py`): Detects frozen UI via DOM hash, request count, and pixel signatures. Recovery strategies: back, reload, replan, continue, timeout. Config in `configs/watchdog.yaml`.
- **OpenAIProvider** (`providers/openai_provider.py`): OpenAI client with JSON mode, exponential backoff retry, and redaction.
- **SeededFaker** (`data_gen/faker_util.py`): Deterministic test data generation keyed by run_id.

## Configuration

Test plans and environments are YAML files. Examples in `examples/`:
- `plan.*.yaml`: Test plans with steps (title, action, target, data, verification)
- `env.*.yaml`: Environment configs (base_url, credentials, browser settings, test data)

## Key Conventions

- Python 3.11+ required
- Black formatting with 100-char line length (`target-version = ['py311']`)
- pytest with `asyncio_mode = "auto"`
- All I/O is async (Playwright, WebSockets, file operations)
- Build system: Hatchling
