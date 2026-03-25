# Framework Security Checks

## What This Is

This document explains the local security checks used for **AI WebTester itself**.

These checks are about the safety of the framework code and dependencies that users install and run in CI or local environments. They are **not** tests against the application under test.

## Why It Exists

AI WebTester often runs with access to:
- internal application URLs
- test credentials
- screenshots, traces, and logs from private systems
- `OPENAI_API_KEY` and other environment variables

Because of that, the framework should validate its own code and dependencies before release.

## What The Checks Do

### `safety check`

Checks the Python dependencies declared for this project against known vulnerability databases.

Use it to catch:
- vulnerable package versions
- dependency risk introduced by upgrades
- issues that should block or delay release

### `bandit -r .`

Scans the Python code in this repository for common security issues.

Use it to catch:
- unsafe subprocess usage
- weak temporary-file patterns
- risky deserialization or shell usage
- other common Python security mistakes

## What These Checks Do Not Do

These checks do **not**:
- scan the target application you are testing
- perform penetration testing
- replace SAST, DAST, or application security review for the product under test

They only help ensure that **AI WebTester**, as a tool, is safer to run.

## How To Run Them

Install project dependencies first:

```bash
pip install -e ".[dev]"
```

Run the dependency vulnerability scan:

```bash
safety check
```

Run the static Python security scan:

```bash
bandit -r .
```

Run both before opening a PR or after dependency changes:

```bash
safety check
bandit -r .
pytest tests/
```

## When To Run Them

Run these checks when:
- changing dependencies in `pyproject.toml`
- changing code that handles credentials, tokens, or secrets
- changing subprocess, file-system, or network-related code
- preparing a pull request
- validating CI behavior locally

## CI Relationship

These same checks run in the GitHub Actions `security` job:
- `safety check`
- `bandit -r .`

That job exists to validate the framework users install, not to assess the security of the external application being tested.
