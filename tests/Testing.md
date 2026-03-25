# Testing Guide

## Overview

The AI WebTester framework has unit and integration tests across multiple test files. All tests run with `pytest` and do not require a running browser, a live mock app, or an OpenAI API key — they use mocks and FastAPI's TestClient where needed.

For the separate framework security checks used in CI, see `tests/Security-Checks.md`.

---

## Running Tests

### Run everything

```bash
pytest tests/
```

### Run a specific test file

```bash
pytest tests/test_redaction.py
pytest tests/test_executor.py
pytest tests/test_mock_app.py
```

### Run a specific test class or test

```bash
pytest tests/test_executor.py::TestFillAction
pytest tests/test_redaction.py::TestRedactionPatterns::test_email_addresses
```

### Run with verbose output

```bash
pytest tests/ -v
```

### Run and stop on first failure

```bash
pytest tests/ -x
```

### Run only tests matching a keyword

```bash
pytest tests/ -k "redaction"
pytest tests/ -k "login"
pytest tests/ -k "fallback"
```

---

## Test Files

### `test_redaction.py` — Security Redaction (60 tests)

Tests the entire security redaction system defined in `configs/security.yaml`.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestRedactionPatterns` | 21 | Every regex pattern: bearer tokens, API keys, emails, phones, SSNs, credit cards, CVVs, passwords, GitHub tokens, Stripe keys, JWTs, URLs with credentials, and more |
| `TestContentTypes` | 6 | JSON structure preservation, HTML attribute redaction, XML content, URL redaction |
| `TestHeaderRedaction` | 2 | HTTP header sensitivity detection, case-insensitive matching |
| `TestEdgeCases` | 10 | Empty input, no sensitive data, mixed content, nested JSON, arrays, unicode, disabled redaction, malformed regexes |
| `TestPerformance` | 2 | Large text (40K chars in <100ms), large JSON (100 objects) |
| `TestStatistics` | 2 | Redaction count tracking, stats reset |
| `TestAuditLogging` | 1 | Audit log emission when enabled |
| `TestPatternValidation` | 2 | Valid patterns compile, invalid patterns handled gracefully |
| `TestGlobalFunctions` | 5 | `redact_text()`, `redact_json()`, `redact_url()`, `redact_headers()`, `get_redactor()` |
| `TestEventsJsonRedaction` | 4 | Event log redaction, DOM snapshot redaction, console log redaction, LLM communication redaction |
| `TestConfigLoadingAndErrorHandling` | 3 | Missing config fallback, invalid YAML fallback, custom config path |
| `TestIntegration` | 2 | Complete redaction pipeline, performance + accuracy on complex nested data (100 users, 200 logs, 50 API responses) |

**When to run:** After any change to `utils/redaction.py`, `configs/security.yaml`, or `evidence/sink.py`.

---

### `test_executor.py` — Test Step Execution (17 tests)

Tests the Executor that runs individual test steps (navigate, click, fill, submit, wait, verify). Uses mocked Playwright page objects.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestStep` | 2 | Step dataclass defaults, construction from dict |
| `TestResolveTarget` | 5 | Absolute URLs pass through, relative paths join with base URL, CSS selectors unchanged, trailing slash handling, empty base URL |
| `TestNavigateAction` | 1 | Calls `page.goto()` and waits for `domcontentloaded` |
| `TestClickAction` | 1 | Waits for selector then clicks |
| `TestFillAction` | 1 | Waits for selector then fills value |
| `TestSubmitAction` | 1 | Waits for selector, clicks, waits for page load |
| `TestWaitAction` | 1 | Actually sleeps for the requested duration |
| `TestVerifyAction` | 3 | Verify by text content, verify by CSS selector, verify both combined |
| `TestRunStep` | 2 | Unknown action raises `ValueError`, step events are logged to sink |

**When to run:** After any change to `orchestrator/executor.py`.

---

### `test_graph.py` — Core Orchestrator (4 tests)

Tests TestGraph, the main execution engine that coordinates browser, executor, and evidence collection. Uses mocked browser context.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestGraphLoadYaml` | 3 | Loads valid YAML, raises on empty files, raises on missing files |
| `TestGraphRun` | 1 | Full mocked end-to-end run: creates browser, executes steps, returns result dict with correct status, run_id, step count, and duration |

**When to run:** After any change to `orchestrator/graph.py` or `browser/context.py`.

---

### `test_mock_app.py` — Demo Application (10 tests)

Tests all HTTP endpoints of the mock FastAPI application using FastAPI's TestClient (no running server needed).

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestHealthEndpoint` | 2 | Returns `{"status": "ok"}`, reflects correct employee count |
| `TestLoginFlow` | 5 | Root redirects to `/login`, login page renders HTML, POST sets session cookie and redirects, `/employees/new` requires auth, accessible after login |
| `TestEmployeeCRUD` | 4 | Create employee returns success JSON, multiple employees get incrementing IDs, list endpoint returns all employees, empty list when no employees |

**When to run:** After any change to `mock_app/app.py` or `mock_app/templates/`.

---

### `test_openai_provider.py` — AI Integration (11 tests)

Tests the OpenAI provider's initialization, availability checks, JSON extraction, and fallback test plan generation. Does not call the real OpenAI API.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestOpenAIProviderInit` | 3 | No API key marks provider unavailable, API key from parameter works, default model is GPT-4o-mini |
| `TestOpenAIModel` | 2 | All models support JSON mode, max token limits are correct |
| `TestExtractJsonFromText` | 3 | Extracts JSON object from mixed text, returns None when no JSON, handles nested structures |
| `TestGenerateCompletionUnavailable` | 1 | Returns failure response when no API key |
| `TestFallbackTestPlan` | 2 | Generates navigate + fill steps for login page (email, password, submit), handles empty element list gracefully |

**When to run:** After any change to `providers/openai_provider.py` or `orchestrator/page_analyzer.py` (fallback logic).

---

### `test_faker_util.py` — Test Data Generation (12 tests)

Tests the SeededFaker utility for deterministic, reproducible test data.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestSeededFaker` | 10 | Same run ID produces identical data, different IDs produce different data, all profile fields present, caching behavior, `cache=False` produces distinct profiles, email contains run suffix, address fields, payment uses test card numbers, form data maps common field names, cache reset |
| `TestGetRunSpecificFaker` | 2 | Same run ID returns same instance, different IDs return different instances |

**When to run:** After any change to `data_gen/faker_util.py` or `utils/data_generation.py`.

---

### `test_ports.py` — Port Utilities (5 tests)

Tests the port detection and allocation functions.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestIsPortAvailable` | 2 | Free port detected as available, occupied port detected as unavailable |
| `TestFindFreePort` | 2 | Finds a port in the expected range, raises `RuntimeError` when none found |
| `TestFindFreePortRange` | 1 | Finds consecutive ports |
| `TestGetServiceUrl` | 2 | HTTP URL generation, HTTPS URL generation |

**When to run:** After any change to `utils/ports.py`.

---

### `test_watchdog.py` — Stuck-Screen Detection (12 tests)

Tests the Watchdog system's configuration, state comparison, statistics, and initialization. Does not require a running browser.

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestWatchdogState` | 5 | DOM hash change detection, request count change detection, `any_changed` with all indicators, `any_changed` with specific indicators, identical states report no change |
| `TestWatchdogConfig` | 2 | Default values correct, custom values override defaults |
| `TestWatchdogStats` | 2 | Default stats are zeroed, recovery strategy stats initialized for all strategies |
| `TestWatchdogInit` | 4 | Creates with defaults, accepts sink parameter, tracks network requests, resets stats |

**When to run:** After any change to `utils/watchdog.py` or `configs/watchdog.yaml`.

---

### `test_hooks.py` — Hook System

Tests the hook loader and extension points used for app-specific test generation and execution.

**What it covers:**
- loading hooks from a Python file
- ordered execution of sync and async hook transforms
- environment customization during generated test creation

**When to run:** After any change to `utils/hooks.py`, CLI hook wiring, or generation hook integration.

---

## When to Run Tests

| Situation | What to Run |
|-----------|-------------|
| Before every commit | `pytest tests/` (full suite, ~10 seconds) |
| Changed a specific module | Run that module's test file (see table above) |
| Changed `configs/security.yaml` | `pytest tests/test_redaction.py` |
| Changed `configs/watchdog.yaml` | `pytest tests/test_watchdog.py` |
| Changed the mock app | `pytest tests/test_mock_app.py` |
| Changed the executor or actions | `pytest tests/test_executor.py` |
| Changed AI/OpenAI integration | `pytest tests/test_openai_provider.py` |
| Changed test data generation | `pytest tests/test_faker_util.py` |
| Pull request / CI | Full suite runs automatically via GitHub Actions |
| After installing new dependencies | `pytest tests/` to verify nothing broke |

---

## CI Integration

Tests run automatically in the GitHub Actions CI pipeline (`.github/workflows/ci.yml`):

- **Test job**: Runs `pytest tests/` on Python 3.11 and 3.12
- **Lint job**: Runs `black --check`, `ruff check`, and `mypy`
- **Security job**: Runs `safety check` and `bandit -r .`

All three jobs run in parallel on every push and pull request.

---

## Requirements

Tests require these packages (included in `pip install -e ".[dev]"`):

- `pytest` — test runner
- `pytest-asyncio` — async test support
- `faker` — test data generation
- `fastapi` + `httpx` — TestClient for mock app tests
- `python-multipart` — form data handling in mock app
- `pyyaml` — YAML config loading
- `playwright` — imported by page_analyzer (not actually launched in tests)
- `openai` — imported by provider (not actually called in tests)

No browser installation, running servers, or API keys are needed to run the test suite.

---

## Adding New Tests

Place test files in `tests/` with the naming convention `test_<module>.py`. Each test class should be named descriptively (e.g., `TestLoginFlow`, `TestRedactionPatterns`).

For async tests, use the `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_something_async():
    result = await some_async_function()
    assert result == expected
```

For tests that need a mocked Playwright page:

```python
from unittest.mock import AsyncMock, MagicMock

page = AsyncMock()
page.on = MagicMock()  # Use sync mock for event listeners
page.url = "http://localhost"
```

The project uses `asyncio_mode = "auto"` in `pyproject.toml`, so async test functions are detected automatically without needing the marker in most cases.
