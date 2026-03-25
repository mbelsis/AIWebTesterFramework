# Autonomous Exploration & Testing

## Overview

The `explore` command is AI WebTester's autonomous testing mode. Instead of writing test plans manually, you point it at your application, give it credentials, and it does everything a human tester would:

1. Logs in to your application
2. Crawls every page it can find
3. Maps all forms, inputs, buttons, and outputs
4. Captures console errors and network failures along the way
5. Uses AI to generate test plans for each discovered page
6. Executes those tests automatically
7. Produces a full report with video evidence

This is designed for complex SaaS applications with many modules behind authentication — GRC platforms, CRMs, ERPs, admin dashboards, and similar multi-page applications.

---

## How It Works

### Phase 1: Authentication

The explorer needs to get past your login page. It supports two methods:

**Credentials** — Provide username and password. The explorer navigates to the login page, auto-detects the username field, password field, and submit button, fills them, and submits. It verifies authentication succeeded by checking that the login page is no longer visible.

**Session Cookie** — If your app uses token-based auth or you already have a valid session, provide the cookie name and value. The explorer injects it into the browser and navigates directly to the app.

The auto-detection tries these selectors in order:
- Username: `input[type='email']`, `input[name*='user']`, `input[name*='email']`
- Password: `input[type='password']`
- Submit: `button[type='submit']`, `button:has-text('Login')`, `button:has-text('Sign in')`

### Phase 2: Crawling

After authentication, the explorer performs a breadth-first crawl starting from the current page:

1. Extracts all links on the page
2. Filters out external domains, logout URLs, API endpoints, and static assets
3. Visits each link, waits for the page to fully load
4. Scrolls to the bottom to trigger any lazy-loaded content
5. Extracts all interactive elements (forms, inputs, buttons)
6. Identifies output areas (tables, alerts, notification messages)
7. Takes a screenshot of every page
8. Records all console errors and HTTP errors (4xx/5xx)
9. Repeats for every newly discovered link, up to the configured depth

**SPA Handling** — For single-page applications where navigation doesn't change the URL, the explorer also clicks sidebar links, menu items, and tab buttons. It detects content changes via DOM hashing — if the page structure changes after a click, it's treated as a new "page" even though the URL is the same.

**Loop Prevention** — Each page is fingerprinted by its normalized URL combined with a DOM structure hash. If the explorer encounters the same fingerprint twice, it skips it. Additional safeguards include a maximum page count (default 200), a maximum crawl depth, and an overall time limit (default 30 minutes).

### Phase 3: AI Test Generation

For every discovered page that has forms, inputs, or buttons, the explorer sends the page structure to OpenAI:

- Page URL and title
- Form fields with their types, names, and placeholders
- Buttons with their text and IDs
- The page type (login, dashboard, form, etc.)

The AI generates a complete test plan with steps like: navigate to the page, fill each form field with realistic data, submit the form, verify success, and test at least one invalid input scenario.

If OpenAI is not available (no API key), the explorer falls back to basic tests: navigate to each page and verify it loads, then fill any visible form fields with generic test data.

### Phase 4: Test Execution

Each generated test plan is executed using the same Executor that powers the `run` command. The explorer runs every step — navigate, fill, click, submit, verify — and captures the result. If a step fails, it logs the failure and continues with the remaining steps (it does not abort the entire test suite on a single failure).

### Phase 5: Reporting

All results are saved to the artifacts directory:

| File | Contents |
|------|----------|
| `app_map.json` | Complete sitemap — every page with its forms, inputs, outputs, buttons, links, and module classification |
| `exploration_report.json` | Full results — test pass/fail per page, all console errors, all network errors, input/output mapping for every form |
| `run.json` | Summary — total pages discovered, tests passed/failed, duration |
| `test_plans/*.json` | Individual AI-generated test plan for each page |
| `page_*.png` | Screenshot of every discovered page |
| `video/*.webm` | Complete browser recording of the entire exploration |
| `trace.zip` | Playwright trace for step-by-step debugging |
| `events.json` | Chronological event log |

---

## Usage

### Basic: Explore Everything

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123"
```

This logs in, crawls the entire app up to 5 levels deep, generates tests for every page with forms, executes them, and saves everything to `artifacts/explore_<timestamp>/`.

### Focus on Specific Modules

If your app has many sections and you only want to test certain ones:

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --modules "Risk Assessment,Vendor Management"
```

The explorer still crawls the full app to find these modules, but only analyzes and tests pages whose titles, headings, or breadcrumbs match the module names you specified.

### Use a Session Cookie

If your app uses SSO, MFA, or a non-standard login flow, log in manually in your browser, copy the session cookie value, and pass it:

```bash
python -m cli.main explore https://your-app.com/dashboard \
  --cookie-name "session_id" \
  --cookie-value "eyJhbGciOi..."
```

### Crawl Only (No Testing)

To just map the application without generating or running tests:

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --no-tests
```

This produces the `app_map.json` with the full sitemap, screenshots, and any errors found — but skips AI test generation and execution. Useful for understanding the app structure first.

### Generate Tests Without Executing

To have the AI generate test plans for review before running them:

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --crawl-only
```

This crawls the app and generates test plans in `test_plans/`, but does not execute them. You can review and edit the plans, then run them individually with the `run` command.

### Control Crawl Depth

For large applications, limit how deep the explorer goes:

```bash
# Shallow exploration — just the main pages
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --max-depth 2

# Deep exploration
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --max-depth 8
```

Depth 1 = only pages directly linked from the post-login page. Depth 2 = those pages plus pages linked from them. And so on.

### Watch It Live

Add `--control-room` to monitor the exploration in real time via the WebSocket dashboard:

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --control-room
```

### Headless Mode (for CI/CD)

Run without opening a visible browser window:

```bash
python -m cli.main explore https://your-app.com/login \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --no-headful
```

### Custom Login Page URL

If the login page is at a different URL than the base application:

```bash
python -m cli.main explore https://your-app.com/dashboard \
  --username "admin@company.com" \
  --password "YourPassword123" \
  --login-url "https://auth.your-app.com/login"
```

---

## All Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `URL` (argument) | Base URL of the application | Required |
| `--username` | Login username/email | None |
| `--password` | Login password | None |
| `--cookie-name` | Session cookie name (alternative to credentials) | None |
| `--cookie-value` | Session cookie value | None |
| `--login-url` | Explicit login page URL | Same as base URL |
| `--max-depth` | Maximum crawl depth from start page | 5 |
| `--modules` | Comma-separated module names to focus on | All modules |
| `--headful / --no-headful` | Show/hide browser window | Show |
| `--no-tests` | Skip test generation and execution entirely | False |
| `--crawl-only` | Generate tests but don't execute them | False |
| `--control-room` | Enable live monitoring dashboard | False |
| `--artifacts-dir` | Output directory for results | `artifacts` |

---

## Example: Testing a GRC Application

A GRC (Governance, Risk, Compliance) platform with modules for Risk Assessment, Policies, Vendor Management, and Technical Audits.

### Step 1: Full Exploration

```bash
python -m cli.main explore https://grc-app.company.com/login \
  --username "qa-tester@company.com" \
  --password "TestAccount123!" \
  --max-depth 4 \
  --headful
```

Watch the browser as it:
- Logs in with the provided credentials
- Discovers the dashboard, sidebar navigation, and all module pages
- Clicks into Risk Assessment, finds the risk registry, create form, edit form
- Clicks into Policies, finds the policy list, create/edit forms
- Maps every form field, button, table, and error message
- Generates and runs tests for each page

### Step 2: Review the App Map

Open `artifacts/explore_<timestamp>/app_map.json`:

```json
{
  "base_url": "https://grc-app.company.com",
  "pages_discovered": 23,
  "total_forms": 8,
  "total_inputs": 47,
  "modules": {
    "Risk Assessment": ["risk-registry", "create-risk", "edit-risk"],
    "Policies": ["policy-list", "create-policy"],
    "Vendor Management": ["vendor-list", "add-vendor"]
  },
  "pages": {
    "https://grc-app.company.com/risks::a3f2b1": {
      "title": "Risk Registry",
      "page_type": "dashboard",
      "forms": [],
      "inputs": [{"name": "search", "type": "text", "placeholder": "Search risks..."}],
      "outputs": [{"type": "table", "headers": ["Risk ID", "Title", "Severity", "Status"]}],
      "console_errors": 0,
      "network_errors": 0
    },
    "https://grc-app.company.com/risks/new::b7c4d2": {
      "title": "Create Risk Assessment",
      "page_type": "registration",
      "forms": [{"method": "post", "fields": [
        {"name": "title", "type": "text", "required": true},
        {"name": "category", "type": "select", "required": true},
        {"name": "description", "type": "textarea"},
        {"name": "likelihood", "type": "select"},
        {"name": "impact", "type": "select"}
      ]}],
      "outputs": [],
      "console_errors": 0,
      "network_errors": 0
    }
  }
}
```

### Step 3: Review Test Results

Open `artifacts/explore_<timestamp>/exploration_report.json`:

```json
{
  "summary": {
    "pages_discovered": 23,
    "tests_executed": 8,
    "tests_passed": 6,
    "tests_failed": 2,
    "console_errors": 3,
    "network_errors": 1,
    "duration_seconds": 145.7
  },
  "test_results": [
    {
      "plan_name": "Test Create Risk Assessment",
      "page_url": "https://grc-app.company.com/risks/new",
      "status": "passed",
      "passed_steps": 7,
      "failed_steps": 0
    },
    {
      "plan_name": "Test Vendor Registration",
      "page_url": "https://grc-app.company.com/vendors/new",
      "status": "failed",
      "passed_steps": 4,
      "failed_steps": 1
    }
  ],
  "console_errors": [
    {"url": "https://grc-app.company.com/reports", "text": "TypeError: Cannot read property 'map' of undefined"}
  ],
  "network_errors": [
    {"url": "https://grc-app.company.com/api/notifications", "status": 500}
  ]
}
```

### Step 4: Re-Test a Specific Module

After fixing the vendor registration bug, re-test just that module:

```bash
python -m cli.main explore https://grc-app.company.com/login \
  --username "qa-tester@company.com" \
  --password "TestAccount123!" \
  --modules "Vendor Management" \
  --max-depth 3
```

### Step 5: Debug a Failure

Open the Playwright trace to see exactly what happened:

```bash
playwright show-trace artifacts/explore_<timestamp>/trace.zip
```

Or watch the video recording in `artifacts/explore_<timestamp>/video/`.

---

## Configuration

Default behavior is controlled by `configs/explorer.yaml`. You can edit this file to change:

- **Crawl limits** — max depth, max pages, time limit
- **SPA settings** — enable/disable SPA detection, clicks per page, wait times
- **Login selectors** — the CSS selectors used to auto-detect login form fields
- **Navigation selectors** — what elements the SPA crawler clicks (sidebar links, menu items, tabs)
- **Excluded URLs** — patterns to skip during crawling (logout, API endpoints, static files)

---

## How Module Filtering Works

When you pass `--modules "Risk Assessment,Vendor Management"`, the explorer:

1. Still crawls the full app to discover all pages
2. For each page, checks the page title, `<h1>` heading, `<h2>` headings, and breadcrumb elements
3. If any of those contain "risk assessment" or "vendor management" (case-insensitive), the page is included
4. Only included pages get AI test generation and execution
5. The app map still contains all discovered pages for completeness, but tests only run on filtered ones

This means you get a full sitemap but targeted testing.

---

## Limitations

- **File uploads** — The explorer cannot test file upload fields
- **Drag and drop** — Not supported as a discoverable interaction
- **Multi-factor authentication** — Use a test account with MFA disabled, or use `--cookie-name`/`--cookie-value` after manual login
- **CAPTCHA** — Cannot solve CAPTCHAs; use a test environment without them
- **Email verification flows** — Cannot read external inboxes
- **Iframes** — The crawler does not enter iframe content (logged but not explored)
- **Infinite scroll** — The crawler scrolls once per page; it does not repeatedly scroll to load all paginated content
- **Rate limiting** — If your app rate-limits requests, increase the `delay_between_pages` in `configs/explorer.yaml`

---

## Comparison: explore vs. run vs. generate

| | `explore` | `run` | `generate` |
|---|---|---|---|
| **Input** | URL + credentials | YAML test plan + env file | URL |
| **Automation** | Fully autonomous | Follows a script | Generates a script |
| **Scope** | Entire app or filtered modules | Single user journey | Single page |
| **AI usage** | Analyzes every discovered page | None (executes predefined steps) | Analyzes one page |
| **Output** | App map + tests + report | Pass/fail + video | YAML test plan files |
| **Best for** | Initial discovery, regression sweeps, finding unknown bugs | Repeatable CI/CD tests | Creating test plans to customize and reuse |

A typical workflow: use `explore` first to discover and map your application, review the generated test plans, customize the ones you want to keep, then use `run` in your CI/CD pipeline for ongoing regression testing.
