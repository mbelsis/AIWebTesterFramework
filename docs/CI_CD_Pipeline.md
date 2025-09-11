# CI/CD Pipeline Documentation

## Overview

The AI WebTester framework includes a comprehensive **GitHub Actions CI/CD pipeline** that automatically validates the framework across multiple Python versions, ensures code quality, and provides security scanning. This pipeline is designed to catch regressions early and maintain enterprise-grade reliability.

## Pipeline Architecture

### 🏗️ **Multi-Job Strategy**

The pipeline runs **3 parallel jobs** for maximum efficiency and comprehensive validation:

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
   - Install Playwright browsers: chromium, firefox, webkit
   - Install system dependencies with: playwright install-deps
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
   - AI-powered test generation (when OpenAI API key available)
   - Basic API endpoint validation
   - Network request testing
   ```

5. **OpenAI Integration Testing**
   ```yaml
   - Graceful handling of missing API keys
   - Fork-safe design prevents failures on public forks
   - Uses continue-on-error: true for AI tests
   - Fallback to rule-based test generation
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
   - Scans for known vulnerabilities
   - Checks all dependencies
   - Security advisory database

2. **Static Security Analysis**
   ```bash
   bandit -r .
   ```
   - Security issue detection
   - Common vulnerability patterns
   - Code security best practices

## Workflow Triggers

### **Automatic Triggers**
- **Push Events**: All pushes to any branch
- **Pull Requests**: Comprehensive validation before merge
- **Scheduled**: Optional nightly builds (configurable)

### **Manual Triggers**
- **Workflow Dispatch**: Manual pipeline execution
- **Repository Dispatch**: External service triggers

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
   - Only installs required browser
   - Reduces CI execution time
   - System dependencies included

### 🔐 **Secret Management**

1. **OpenAI API Key Handling**
   ```yaml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   continue-on-error: true  # Fork-safe design
   ```

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
- AI tests skip when API key unavailable
- Browser tests continue with single browser fallback
- Partial artifact collection on failures

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

This CI/CD pipeline ensures every release of the AI WebTester framework is thoroughly validated, secure, and production-ready with enterprise-grade reliability.

## Integrating AI WebTester into Your GitHub Actions

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
          python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --headless
      
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
          # Generate comprehensive tests for key user journeys
          python -m cli.main generate ${DEPLOYMENT_URL}/login --description "Test user authentication flow"
          python -m cli.main generate ${DEPLOYMENT_URL}/dashboard --description "Test main dashboard functionality"
          python -m cli.main generate ${DEPLOYMENT_URL}/checkout --description "Test e-commerce checkout process"
          
          # Run all generated tests
          for plan in examples/plan.generated_*.yaml; do
            python -m cli.main run --plan "$plan" --env "${plan/plan/env}" --headless
          done
      
      - name: Check test results
        run: |
          cd ai-webtester
          # Fail the workflow if any tests failed
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
            --headless \
            --control-room-port 0  # Auto-allocate port
      
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
          # Deploy PR to preview environment
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
          # Generate tests specific to the PR
          python -m cli.main generate ${PR_URL} \
            --description "Test changes in PR #${{ github.event.number }}" \
            --run-id "pr-${{ github.event.number }}"
          
          python -m cli.main run \
            --plan examples/plan.generated_*.yaml \
            --env examples/env.generated_*.yaml \
            --headless
      
      - name: Comment PR with results
        uses: actions/github-script@v7
        if: always()
        with:
          script: |
            const fs = require('fs');
            const path = 'ai-webtester/artifacts';
            
            // Check test results
            const runFiles = fs.readdirSync(path, { recursive: true })
              .filter(file => file.endsWith('run.json'));
            
            let results = '## 🤖 AI WebTester Results\n\n';
            let hasFailures = false;
            
            for (const file of runFiles) {
              const content = JSON.parse(fs.readFileSync(`${path}/${file}`, 'utf8'));
              const status = content.status === 'passed' ? '✅' : '❌';
              if (content.status === 'failed') hasFailures = true;
              
              results += `${status} **${content.plan_name}**: ${content.status}\n`;
              results += `   Duration: ${content.duration_seconds}s\n`;
            }
            
            results += `\n[View detailed artifacts](${context.payload.pull_request.html_url}/checks)`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: results
            });
            
            if (hasFailures) {
              core.setFailed('Some tests failed - check artifacts for details');
            }
```

### 🐳 **Docker Integration**

Use AI WebTester in containerized environments:

```yaml
name: Docker Testing
on: [push]

jobs:
  test-with-docker:
    runs-on: ubuntu-latest
    services:
      app:
        image: your-app:latest
        ports:
          - 3000:3000
        options: --health-cmd="curl -f http://localhost:3000/health" --health-interval=10s
    
    steps:
      - name: Run AI WebTester in container
        run: |
          docker run --rm \
            --network host \
            -e OPENAI_API_KEY="${{ secrets.OPENAI_API_KEY }}" \
            -v $(pwd)/artifacts:/artifacts \
            your-org/ai-webtester:latest \
            generate http://localhost:3000 --description "Docker integration test"
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docker-test-artifacts
          path: artifacts/
```

### 📊 **Performance Testing Integration**

Combine with performance monitoring:

```yaml
name: Performance and Functional Testing
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - name: Setup AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Run comprehensive tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ai-webtester
          # Generate performance-focused tests
          python -m cli.main generate https://app.example.com \
            --description "Performance and functional validation with timing analysis"
          
          # Run with timing measurements
          python -m cli.main run \
            --plan examples/plan.generated_*.yaml \
            --env examples/env.generated_*.yaml \
            --headless
      
      - name: Analyze performance metrics
        run: |
          cd ai-webtester
          # Extract timing data from test results
          for run_file in artifacts/*/run.json; do
            duration=$(jq -r '.duration_seconds' "$run_file")
            if (( $(echo "$duration > 60" | bc -l) )); then
              echo "⚠️ Performance concern: Test took ${duration}s"
            fi
          done
```

### 🔐 **Security Testing Integration**

Automated security testing:

```yaml
name: Security Testing
on:
  push:
    branches: [main, develop]

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - name: Setup AI WebTester
        run: |
          git clone https://github.com/your-org/ai-webtester.git
          cd ai-webtester
          pip install -e ".[dev]"
          playwright install --with-deps chromium
      
      - name: Run security-focused tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ai-webtester
          # Generate security-specific test scenarios
          python -m cli.main generate https://app.example.com/login \
            --description "Security testing including XSS, CSRF, and injection attacks"
          
          python -m cli.main generate https://app.example.com/admin \
            --description "Administrative interface security validation"
          
          # Run with security redaction enabled
          python -m cli.main run \
            --plan examples/plan.generated_*.yaml \
            --env examples/env.generated_*.yaml \
            --headless
      
      - name: Security analysis
        run: |
          cd ai-webtester
          # Check for security issues in test results
          if grep -r "XSS\|injection\|CSRF" artifacts/*/events.json; then
            echo "🔒 Security tests completed - review artifacts for findings"
          fi
```

## Integration Best Practices

### 🎯 **Secret Management**
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  # Add other secrets as needed
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

These examples demonstrate how to seamlessly integrate AI WebTester into your existing CI/CD workflows for automated, intelligent web application testing.