# Testing a Multi-Page SaaS Application with AI WebTester

## Overview

This guide explains how to use AI WebTester to test a complex SaaS application — specifically one with an authentication layer followed by multiple functional modules (e.g., Risk Assessment, Technical Audits, Policies & Procedures, Vendor Management). The framework treats each user journey as an independent test plan, allowing you to validate individual modules in isolation while capturing full video and screenshot evidence of every interaction.

---

## Architecture of a Typical Test

Every test plan follows the same structural pattern:

```
[Login] → [Navigate to Module] → [Perform Actions] → [Verify Outcome]
```

Since most SaaS applications require authentication before accessing any functional page, each test plan begins with a login sequence. This is intentional — it ensures every test is self-contained and can run independently without depending on session state from a previous test.

---

## Test Plan Structure

### Authentication Phase

Every test begins with the same login block. This is repeated across all test plans to guarantee isolation:

```yaml
steps:
  - title: "Navigate to login page"
    action: navigate
    target: "https://your-grc-app.com/login"

  - title: "Enter username"
    action: fill
    target: "#username"
    data:
      value: "admin@company.com"

  - title: "Enter password"
    action: fill
    target: "#password"
    data:
      value: "TestPass123!"

  - title: "Submit login form"
    action: submit
    target: "button[type='submit']"

  - title: "Verify authentication succeeded"
    action: verify
    verification:
      text: "Dashboard"
```

### Module-Specific Phase

After login, each test navigates to its target module and executes the relevant user journey.

---

## Example Test Plans by Module

### 1. Risk Assessment — Create a New Risk Entry

This test validates the full create flow: navigating to the risk module, filling in a new risk form, submitting it, and verifying persistence.

```yaml
name: "Risk Assessment - Create New Risk"
description: "Validates the risk creation workflow from login through submission and verification"

steps:
  # --- Authentication ---
  - title: "Navigate to login page"
    action: navigate
    target: "https://your-grc-app.com/login"

  - title: "Enter username"
    action: fill
    target: "#username"
    data:
      value: "admin@company.com"

  - title: "Enter password"
    action: fill
    target: "#password"
    data:
      value: "TestPass123!"

  - title: "Submit login"
    action: submit
    target: "button[type='submit']"

  - title: "Verify dashboard loaded"
    action: verify
    verification:
      text: "Dashboard"

  # --- Navigate to Risk Assessment ---
  - title: "Open Risk Assessment module"
    action: click
    target: "a[href='/risk-assessment']"

  - title: "Verify Risk Assessment page loaded"
    action: verify
    verification:
      text: "Risk Assessment"

  # --- Create New Risk ---
  - title: "Click New Risk button"
    action: click
    target: "#new-risk-btn"

  - title: "Fill risk title"
    action: fill
    target: "#risk-title"
    data:
      value: "Data Breach Risk - Automated Test"

  - title: "Select risk category"
    action: click
    target: "select#category option[value='cybersecurity']"

  - title: "Fill risk description"
    action: fill
    target: "#description"
    data:
      value: "Automated test entry for validating risk creation workflow"

  - title: "Set risk likelihood"
    action: fill
    target: "#likelihood"
    data:
      value: "High"

  - title: "Set risk impact"
    action: fill
    target: "#impact"
    data:
      value: "Critical"

  - title: "Submit the risk form"
    action: submit
    target: "button[type='submit']"

  - title: "Verify risk was created successfully"
    action: verify
    verification:
      text: "Data Breach Risk - Automated Test"
```

### 2. Policies & Procedures — Create a New Policy

```yaml
name: "Policies - Create New Policy"
description: "Validates the policy creation workflow including metadata entry and submission"

steps:
  # --- Authentication (same login block) ---
  - title: "Navigate to login page"
    action: navigate
    target: "https://your-grc-app.com/login"

  - title: "Enter username"
    action: fill
    target: "#username"
    data:
      value: "admin@company.com"

  - title: "Enter password"
    action: fill
    target: "#password"
    data:
      value: "TestPass123!"

  - title: "Submit login"
    action: submit
    target: "button[type='submit']"

  - title: "Verify dashboard loaded"
    action: verify
    verification:
      text: "Dashboard"

  # --- Navigate to Policies ---
  - title: "Open Policies module"
    action: click
    target: "a[href='/policies']"

  - title: "Verify Policies page loaded"
    action: verify
    verification:
      text: "Policies"

  # --- Create New Policy ---
  - title: "Click Create Policy"
    action: click
    target: "#create-policy-btn"

  - title: "Fill policy title"
    action: fill
    target: "#policy-title"
    data:
      value: "Data Retention Policy - Automated Test"

  - title: "Fill policy description"
    action: fill
    target: "#policy-description"
    data:
      value: "Defines data retention requirements for all business units"

  - title: "Select policy owner"
    action: click
    target: "select#owner option[value='compliance-team']"

  - title: "Set review date"
    action: fill
    target: "#review-date"
    data:
      value: "2026-12-31"

  - title: "Submit policy"
    action: submit
    target: "button[type='submit']"

  - title: "Verify policy was created"
    action: verify
    verification:
      text: "Data Retention Policy - Automated Test"
```

### 3. Vendor Management — Add a New Vendor

```yaml
name: "Vendor Management - Add New Vendor"
description: "Validates the vendor onboarding workflow"

steps:
  # --- Authentication ---
  - title: "Navigate to login page"
    action: navigate
    target: "https://your-grc-app.com/login"

  - title: "Enter username"
    action: fill
    target: "#username"
    data:
      value: "admin@company.com"

  - title: "Enter password"
    action: fill
    target: "#password"
    data:
      value: "TestPass123!"

  - title: "Submit login"
    action: submit
    target: "button[type='submit']"

  - title: "Verify dashboard loaded"
    action: verify
    verification:
      text: "Dashboard"

  # --- Navigate to Vendor Management ---
  - title: "Open Vendor Management module"
    action: click
    target: "a[href='/vendors']"

  - title: "Verify Vendor Management page loaded"
    action: verify
    verification:
      text: "Vendor Management"

  # --- Add New Vendor ---
  - title: "Click Add Vendor"
    action: click
    target: "#add-vendor-btn"

  - title: "Fill vendor name"
    action: fill
    target: "#vendor-name"
    data:
      value: "Acme Cloud Services - Automated Test"

  - title: "Fill vendor contact email"
    action: fill
    target: "#contact-email"
    data:
      value: "vendor-test@acme.com"

  - title: "Select vendor risk tier"
    action: click
    target: "select#risk-tier option[value='high']"

  - title: "Fill service description"
    action: fill
    target: "#service-description"
    data:
      value: "Cloud infrastructure provider for production workloads"

  - title: "Submit vendor form"
    action: submit
    target: "button[type='submit']"

  - title: "Verify vendor was added"
    action: verify
    verification:
      text: "Acme Cloud Services - Automated Test"
```

---

## Environment Configuration

All test plans share a single environment file that defines connection settings and browser behavior:

```yaml
name: "GRC Application - Test Environment"
description: "Configuration for testing the GRC SaaS platform"

target:
  base_url: "https://your-grc-app.com"
  timeout: 15000

credentials:
  username: "admin@company.com"
  password: "TestPass123!"

settings:
  headful: true       # Set to false for CI/CD pipelines
  slow_mo: 300        # Milliseconds between actions (helps with slower UIs)
  video: true         # Record browser session video
  screenshots: true   # Capture screenshots on failures
```

---

## Two Approaches to Test Creation

### Approach 1: AI-Generated Tests (Faster Initial Setup)

Point the AI at each page of your application:

```bash
python -m cli.main generate https://your-app.com/login \
  --description "Test login with valid and invalid credentials"

python -m cli.main generate https://your-app.com/risk-assessment \
  --description "Test creating and editing risk assessments"

python -m cli.main generate https://your-app.com/policies \
  --description "Test creating policies and procedures"

python -m cli.main generate https://your-app.com/vendors \
  --description "Test vendor management CRUD operations"
```

**Key constraint:** The AI analyzes what it can see on the page. Pages behind authentication will show a login redirect instead of the actual module content. For authenticated pages, you have two options:

- Generate tests for the login page first, then manually prepend those steps to module-specific generated tests.
- Write the login steps by hand and use AI generation only for the module-specific interactions.

### Approach 2: Manual YAML (Full Control)

Write test plans by hand using CSS selectors from your application. This requires inspecting the DOM in Chrome DevTools but gives you precise control over every interaction.

**How to find selectors:**
1. Open your app in Chrome
2. Right-click any element → Inspect
3. Look for identifying attributes:
   - `id` attribute → use `#the-id`
   - `name` attribute → use `[name='the-name']`
   - Unique class → use `.the-class`
   - Button by text → use `button:has-text('Save')`

---

## Execution

### Running Individual Tests

```bash
python -m cli.main run --plan test-risk-assessment.yaml --env grc-env.yaml --control-room
python -m cli.main run --plan test-policies.yaml --env grc-env.yaml --control-room
python -m cli.main run --plan test-vendors.yaml --env grc-env.yaml --control-room
```

### Running a Full Test Suite

Create a simple script to execute all test plans sequentially:

```bash
#!/bin/bash
PLANS=(
  "test-login.yaml"
  "test-risk-assessment.yaml"
  "test-policies.yaml"
  "test-vendors.yaml"
  "test-technical-audits.yaml"
)

for plan in "${PLANS[@]}"; do
  echo "Running: $plan"
  python -m cli.main run --plan "$plan" --env grc-env.yaml
  echo "---"
done

echo "All tests completed. Results in artifacts/"
```

---

## Analyzing Results

Each test run produces a timestamped directory under `artifacts/` containing:

| Artifact | Purpose |
|----------|---------|
| `video/*.webm` | Full browser session recording — shows exactly what happened |
| `trace.zip` | Playwright trace — open with `playwright show-trace trace.zip` for step-by-step debugging |
| `run.json` | Machine-readable pass/fail status with timing data |
| `events.json` | Chronological log of every action, network request, and console message |
| `*_failure.png` | Screenshots captured at the moment of any step failure |

To inspect a trace interactively:

```bash
playwright show-trace artifacts/<run-id>/trace.zip
```

This opens a timeline view showing every browser action, network request, and DOM state at each step — invaluable for diagnosing why a test failed.

---

## Practical Considerations

### What the framework handles well
- Form-based workflows (create, edit, submit, verify)
- Navigation across multiple pages and modules
- Verification that expected content appears after actions
- Full evidence capture for compliance and audit documentation
- Detecting broken pages, missing elements, and failed form submissions

### Current limitations
- **File uploads** — Not supported as a built-in action
- **Drag and drop** — Not supported as a built-in action
- **Multi-factor authentication** — Test accounts should have MFA disabled or use a bypass
- **Email/SMS verification flows** — The tool cannot read external inboxes
- **PDF or file download validation** — The tool verifies page content, not downloaded files
- **Parallel execution** — Tests run sequentially; you cannot run multiple modules simultaneously in one process

### Recommendations for a GRC application
- **Create a dedicated test user account** with appropriate permissions and MFA disabled
- **Start with the login test** — if login fails, nothing else works
- **Test one user journey per YAML file** — keep tests focused and independent
- **Use descriptive step titles** — they appear in the video timeline and failure reports
- **Set `slow_mo: 300-500`** in the environment config if your UI has animations or loading spinners that need time to complete
- **Run with `--control-room`** during development to watch tests live; disable it in CI/CD for speed
