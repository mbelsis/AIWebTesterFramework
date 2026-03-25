# AI WebTester - What It Does & How to Use It

## What This Program Does

AI WebTester is a tool that **automatically tests your web application** by controlling a real browser (Chrome). It clicks buttons, fills forms, navigates pages, and checks results — just like a human tester would — while recording everything on video with screenshots.

It has two modes:

1. **AI mode** — You give it a URL, and it uses OpenAI to figure out what's on the page and generates a test plan automatically.
2. **Manual mode** — You write a simple YAML file describing the steps (go here, click this, type that, check this text appears).

---

## How to Test Your SaaS App

### 1. Install

```bash
pip install -e ".[dev]"
playwright install chromium
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="your-key-here"
```

You can get a key at https://platform.openai.com/api-keys. Without it, the AI test generation won't work (manual YAML tests still will).

### 3. Option A: Let AI generate tests automatically

Point it at your login page (or any page):

```bash
python -m cli.main generate https://your-saas-app.com/login --description "Test login with valid and invalid credentials"
```

This opens a browser, analyzes the page, and creates two YAML files in `examples/`. Then run them:

```bash
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room
```

### 3. Option B: Write a test manually

Create a file `my-test.yaml`:

```yaml
name: "Login Test"
steps:
  - title: "Go to login"
    action: navigate
    target: "https://your-saas-app.com/login"

  - title: "Enter email"
    action: fill
    target: "#email"
    data:
      value: "test@example.com"

  - title: "Enter password"
    action: fill
    target: "#password"
    data:
      value: "MyPassword123"

  - title: "Click login"
    action: submit
    target: "button[type='submit']"

  - title: "Check dashboard loaded"
    action: verify
    verification:
      text: "Welcome"
```

Create `my-env.yaml`:

```yaml
name: "My SaaS"
target:
  base_url: "https://your-saas-app.com"
  timeout: 15000
settings:
  headful: true
  video: true
```

Run it:

```bash
python -m cli.main run --plan my-test.yaml --env my-env.yaml --control-room
```

### 4. Review results

After the test runs, you get:
- **Video recording** of the entire browser session in `artifacts/<run-id>/video/`
- **Screenshots** of any failures
- **Trace file** you can inspect with `playwright show-trace artifacts/<run-id>/trace.zip`
- **`run.json`** with pass/fail status

The `--control-room` flag also opens a live WebSocket dashboard where you can watch the test in real time.

### Available actions for test steps

| Action | What it does |
|--------|-------------|
| `navigate` | Go to a URL |
| `fill` | Type text into an input field |
| `click` | Click a button or link |
| `submit` | Click a submit button and wait for page load |
| `wait` | Pause for X seconds |
| `verify` | Check that specific text or element exists on the page |

The `target` is a CSS selector (like `#email`, `.btn-primary`, `button[type='submit']`) or a URL for navigate actions.
