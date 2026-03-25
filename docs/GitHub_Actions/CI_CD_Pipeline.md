# GitHub Actions CI/CD Pipeline

## Overview

This document describes the GitHub Actions pipeline used by this repository.

The AI WebTester framework includes a **GitHub Actions workflow** that validates the framework across multiple Python versions, runs code quality checks, and includes a dedicated security job. This pipeline is designed to catch regressions early and to validate the safety of the framework code that users run in their own environments.

## Why The Workflow File Lives In `.github/workflows/`

The actual workflow implementation is stored in:

- `.github/workflows/ci.yml`

That location is required by GitHub Actions. GitHub only discovers and runs workflow files placed inside `.github/workflows/`.

### What The `.github` Folder Is

`.github` is a repository metadata folder used by GitHub features. It commonly contains:
- workflow files
- issue templates
- pull request templates
- other GitHub-specific repository configuration

The folder starts with a dot because it follows a standard hidden-configuration convention used across many developer tools. The folder is still present after `git clone`; some terminals or file explorers simply hide dot-folders by default unless you enable hidden-file display.

### What `.github/workflows/ci.yml` Does

The file `.github/workflows/ci.yml` is the **real executable pipeline definition** for this repository.

It tells GitHub Actions:
- when to run the pipeline
- which jobs to run
- which Python versions to test
- which commands install dependencies and Playwright
- which test, lint, and security commands to execute
- which artifacts to upload

This documentation file exists to explain that workflow in human-readable form. The Markdown file is documentation; the YAML file is the actual automation.

## Pipeline Architecture

### 🏗️ **Multi-Job Strategy**

The workflow defines **3 jobs** that can run in parallel:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Test Job   │  │  Lint Job   │  │Security Job │
│ (Matrix)    │  │             │  │             │
│ Python 3.11 │  │ Black       │  │ Safety      │
│ Python 3.12 │  │ Ruff        │  │ Bandit      │
│             │  │ MyPy        │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 🧪 **Test Job (Matrix Strategy)**

**Environment Matrix:**
- **Python Versions**: 3.11 and 3.12
- **Operating System**: Ubuntu Latest
- **Fail-Fast**: Disabled (all combinations run even if one fails)

**Workflow Steps:**

1. **Setup & Dependencies**
   ```yaml
   - Checkout code
   - Setup Python version
   - Install uv (fast Python package installer)
   - Cache dependencies for performance
   - Install framework with: uv pip install -e ".[dev]"
   ```

2. **Browser Automation Setup**
   ```yaml
   - Install Playwright Chromium with system dependencies
   - Install requests for API testing
   ```

3. **Mock Application Service**
   ```yaml
   - Start mock app in background
   - Health check with 60-second timeout
   - URL validation: http://127.0.0.1:5000/health
   - Process ID tracking for cleanup
   ```

4. **Comprehensive Testing**
   ```yaml
   - Demo employee creation test (full UI automation)
   - AI-powered test generation step using OPENAI_API_KEY when available
   - Basic HTTP validation of /health and /login
   ```

5. **OpenAI Integration Testing**
   ```yaml
   - The AI generation step is marked continue-on-error: true
   - This prevents that step from failing the overall job
   - The generator itself has fallback logic when OpenAI is unavailable
   - The workflow does not explicitly skip the step when the key is missing
   ```

6. **Artifact Collection**
   ```yaml
   - Screenshots and videos (30-day retention)
   - Playwright traces and execution logs
   - Test evidence and run summaries
   - Error artifacts for debugging
   ```

7. **Cleanup & Validation**
   ```yaml
   - Stop mock application process
   - Validate run.json status
   - Upload artifacts to GitHub
   - Fail CI if test status is "failed"
   ```

### 🔍 **Lint Job**

**Code Quality Standards:**

1. **Black Formatting**
   ```bash
   black --check --diff .
   ```
   - Line length: 100 characters
   - Python 3.11+ target
   - Consistent code formatting

2. **Ruff Linting**
   ```bash
   ruff check .
   ```
   - Fast Python linter
   - Comprehensive rule set
   - Import sorting and optimization

3. **MyPy Type Checking**
   ```bash
   mypy .
   ```
   - Static type analysis
   - Type safety validation
   - Interface consistency checks

### 🛡️ **Security Job**

**Security Analysis:**

1. **Dependency Vulnerability Scanning**
   ```bash
   safety check
   ```
   - Scans the framework's declared Python dependencies for known vulnerabilities
   - Helps protect users who install and run AI WebTester in CI or local environments

2. **Static Security Analysis**
   ```bash
   bandit -r .
   ```
   - Scans the framework's Python code for common security issues
   - Helps catch unsafe patterns before they ship to users

### What The Security Job Is For

This job secures **AI WebTester itself**, not the application being tested.

Users run this framework inside their own infrastructure and often provide:
- internal URLs
- test credentials
- screenshots, videos, and traces from private systems
- OpenAI API keys for AI-assisted generation

Because of that, the framework should validate its own dependencies and code. The security job exists for that reason.

### What The Security Job Does Not Do

The security job does **not**:
- run penetration tests against the target application
- detect vulnerabilities in the application under test
- replace application security testing or SAST/DAST for the user's product

## Workflow Triggers

### **Automatic Triggers**
- **Push Events**: All pushes
- **Pull Requests**: Comprehensive validation before merge

### **Manual Triggers**
- **Workflow Dispatch**: Manual pipeline execution

## Key Features

### 🚀 **Performance Optimizations**

1. **Fast Dependencies**
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/uv
       key: ${{ runner.os }}-python-${{ matrix.python-version }}-${{ hashFiles('pyproject.toml') }}
   ```

2. **Parallel Execution**
   - All jobs run simultaneously
   - Independent validation streams
   - Faster feedback cycles

3. **Optimized Browser Installation**
   ```bash
   playwright install --with-deps chromium
   ```
   - Installs Chromium only
   - Reduces CI execution time
   - System dependencies included

### 🔐 **Secret Management**

1. **OpenAI API Key Handling**
   ```yaml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   continue-on-error: true  # Fork-safe design
   ```
   - The step still runs even when the secret is absent
   - Fallback behavior comes from the generator implementation, not from a workflow-level skip

2. **Environment Variables**
   ```yaml
   PYTHONPATH: ${{ github.workspace }}
   UV_SYSTEM_PYTHON: 1
   ```

3. **Security Best Practices**
   - No secret exposure in logs
   - Proper secret scoping
   - Graceful degradation

### 📊 **Monitoring & Debugging**

1. **Comprehensive Logging**
   ```yaml
   - Run basic API tests with error capture
   - Health check validation with timeout
   - Process management with PID tracking
   ```

2. **Artifact Collection**
   ```yaml
   - name: Upload test artifacts
     uses: actions/upload-artifact@v4
     with:
       name: test-artifacts-${{ matrix.python-version }}
       path: artifacts/
       retention-days: 30
   ```

3. **Status Validation**
   ```bash
   if jq -r '.status' artifacts/*/run.json | grep -q "failed"; then
     echo "Test failed based on run.json status"
     exit 1
   fi
   ```

## Error Handling & Recovery

### **Graceful Degradation**
- The AI generation step does not fail the whole job because it uses `continue-on-error: true`
- The generator can fall back to non-AI test plan creation when OpenAI is unavailable
- Artifact upload still runs on failures

### **Cleanup Strategies**
```bash
# Process cleanup
if [ -f mock_app.pid ]; then
  kill $(cat mock_app.pid) || true
fi
pkill -f "uvicorn.*mock_app" || true
```

### **Debugging Support**
- Complete error logs captured
- Artifact preservation for analysis
- Process state monitoring

## Integration Examples

### **Repository Setup**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
```

### **Status Badges**
```markdown
![CI Status](https://github.com/your-org/ai-webtester/workflows/CI/badge.svg)
```

### **Branch Protection**
```yaml
# Require CI to pass before merge
required_status_checks:
  strict: true
  contexts:
    - test (3.11)
    - test (3.12)
    - lint
    - security
```

## Maintenance & Updates

### **Dependency Updates**
- Automated dependency scanning
- Regular security updates
- Version compatibility testing

### **Pipeline Evolution**
- Performance monitoring
- Execution time optimization
- Feature expansion planning

### **Best Practices**
- Regular pipeline review
- Security audit compliance
- Documentation maintenance

This workflow provides practical validation for test execution, linting, artifact collection, and framework security checks. The security job is part of the framework's own engineering hygiene because users execute this code inside their own CI and test environments.

## Integrating AI WebTester Into Your GitHub Actions

The AI WebTester framework can be seamlessly integrated into your existing GitHub Actions workflows to provide automated testing for your web applications. Below are comprehensive examples for different integration scenarios.

### 🚀 **Basic Integration Example**

Add AI WebTester to your existing workflow:

```yaml
name: CI with AI WebTester
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Your existing build steps
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install
      
      - name: Build application
        run: npm run build
      
      - name: Start application
        run: |
          npm start &
          sleep 10
      
      # Add AI WebTester integration
      - name: Setup Python for AI WebTester
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Run AI-powered tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ai-webtester
          python -m cli.main generate http://localhost:3000/login --description "Test login functionality"
          python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --no-headful
      
      - name: Upload test artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-evidence
          path: ai-webtester/artifacts/
          retention-days: 30
```

### 🔄 **Deployment Testing Integration**

Test your application after deployment:

```yaml
name: Deploy and Test
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    outputs:
      deployment-url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        id: deploy
        run: |
          # Your deployment logic here
          echo "url=https://staging-app.example.com" >> $GITHUB_OUTPUT

  ai-test:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Setup AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Generate and run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          DEPLOYMENT_URL: ${{ needs.deploy.outputs.deployment-url }}
        run: |
          cd ai-webtester
          python -m cli.main generate ${DEPLOYMENT_URL}/login --description "Test user authentication flow"
          python -m cli.main generate ${DEPLOYMENT_URL}/dashboard --description "Test main dashboard functionality"
          python -m cli.main generate ${DEPLOYMENT_URL}/checkout --description "Test e-commerce checkout process"
          
          for plan in examples/plan.generated_*.yaml; do
            python -m cli.main run --plan "$plan" --env "${plan/plan/env}" --no-headful
          done
      
      - name: Check test results
        run: |
          cd ai-webtester
          if find artifacts/ -name "run.json" -exec grep -l '"status": "failed"' {} \; | grep -q .; then
            echo "❌ Tests failed - check artifacts for details"
            exit 1
          else
            echo "✅ All tests passed successfully"
          fi
```

### 🌐 **Multi-Environment Testing**

Test across multiple environments:

```yaml
name: Multi-Environment Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Run nightly at 2 AM
  workflow_dispatch:

jobs:
  test-environments:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment:
          - name: staging
            url: https://staging.example.com
          - name: production
            url: https://app.example.com
        test-suite:
          - name: smoke-tests
            description: "Critical user journeys and basic functionality"
          - name: regression-tests
            description: "Comprehensive regression test suite"
    
    steps:
      - name: Setup AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Run ${{ matrix.test-suite.name }} on ${{ matrix.environment.name }}
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ai-webtester
          python -m cli.main generate ${{ matrix.environment.url }} \
            --description "${{ matrix.test-suite.description }}" \
            --run-id "${{ matrix.environment.name }}-${{ matrix.test-suite.name }}-$(date +%Y%m%d)"
          
          python -m cli.main run \
            --plan examples/plan.generated_*.yaml \
            --env examples/env.generated_*.yaml \
            --no-headful \
            --control-room-port 0
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: ${{ matrix.environment.name }}-${{ matrix.test-suite.name }}-artifacts
          path: ai-webtester/artifacts/
```

### 🔀 **Pull Request Testing**

Automatically test pull requests:

```yaml
name: PR Testing
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  preview-deploy:
    runs-on: ubuntu-latest
    outputs:
      preview-url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy PR preview
        id: deploy
        run: |
          echo "url=https://pr-${{ github.event.number }}.preview.example.com" >> $GITHUB_OUTPUT

  ai-testing:
    needs: preview-deploy
    runs-on: ubuntu-latest
    steps:
      - name: Setup AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Test PR changes
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PR_URL: ${{ needs.preview-deploy.outputs.preview-url }}
        run: |
          cd ai-webtester
          python -m cli.main generate ${PR_URL} \
            --description "Test changes in PR #${{ github.event.number }}" \
            --run-id "pr-${{ github.event.number }}"
          
          python -m cli.main run \
            --plan examples/plan.generated_*.yaml \
            --env examples/env.generated_*.yaml \
            --no-headful
```

## Integration Best Practices

### 🎯 **Secret Management**
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### 📁 **Artifact Organization**
```yaml
- name: Upload test artifacts
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: ai-webtester-${{ github.run_id }}
    path: |
      ai-webtester/artifacts/
      ai-webtester/configs/
    retention-days: 30
```

### 🔄 **Conditional Testing**
```yaml
- name: Run AI tests
  if: contains(github.event.head_commit.message, '[test]') || github.event_name == 'schedule'
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    # Your AI WebTester commands here
```

### 📈 **Status Reporting**
```yaml
- name: Report test status
  run: |
    cd ai-webtester
    echo "## 🤖 AI WebTester Summary" >> $GITHUB_STEP_SUMMARY
    echo "| Test Plan | Status | Duration |" >> $GITHUB_STEP_SUMMARY
    echo "|-----------|--------|----------|" >> $GITHUB_STEP_SUMMARY
    
    for run_file in artifacts/*/run.json; do
      name=$(jq -r '.plan_name' "$run_file")
      status=$(jq -r '.status' "$run_file")
      duration=$(jq -r '.duration_seconds' "$run_file")
      echo "| $name | $status | ${duration}s |" >> $GITHUB_STEP_SUMMARY
    done
```

These examples demonstrate how to seamlessly integrate AI WebTester into your existing GitHub Actions workflows for automated, intelligent web application testing.
