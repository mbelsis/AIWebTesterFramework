# AI WebTester Framework

A comprehensive Python-based framework for automated web application testing that combines browser automation, AI-powered testing logic, and real-time monitoring capabilities.

## 🎯 What is AI WebTester?

AI WebTester is a powerful testing framework designed to automate web application testing through browser automation while providing comprehensive evidence collection and real-time monitoring. The framework captures videos, traces, screenshots, and detailed logs of every test execution, making it perfect for documenting application behavior and debugging issues.

### Key Features

- **🤖 AI-Powered Testing**: Intelligent test execution using OpenAI for smart decision making
- **🎥 Video Recording**: Complete browser session recordings with Playwright
- **📊 Real-time Monitoring**: Live Control Room dashboard with WebSocket communication
- **📋 Comprehensive Evidence**: Automatic collection of traces, screenshots, and detailed logs
- **⚡ Async Architecture**: High-performance asynchronous execution
- **🎛️ Flexible Configuration**: YAML-based test plans and environment configuration
- **🔄 Error Resilience**: Robust error handling with automatic cleanup
- **📱 Multi-browser Support**: Chromium, Firefox, and WebKit support via Playwright

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key (for AI-powered features)

### Installation

1. **Clone or download the framework**
2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Quick Demo

Run the included demo test:
```bash
python run_test.py
```

This will:
- Start the demo web application on port 5000
- Launch the Control Room on port 8788
- Execute a sample employee creation test
- Generate artifacts in `artifacts/` directory

## 📖 Usage Guide

### Command Line Interface

The framework provides several CLI commands:

#### Run Tests
```bash
# Basic test execution
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml

# With Control Room monitoring
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --control-room

# Headless mode
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --headful false

# Custom artifacts directory
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --artifacts-dir ./my-test-results
```

#### Start Services
```bash
# Start Control Room dashboard
python -m cli.main control-room

# Start demo application
python -m cli.main mock-app
```

### CLI Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--plan` | Path to test plan YAML file | Required |
| `--env` | Path to environment YAML file | Required |
| `--headful` | Show browser window during testing | `true` |
| `--control-room` | Enable real-time monitoring dashboard | `false` |
| `--artifacts-dir` | Directory for test artifacts | `artifacts` |

## 📄 Configuration Files

### Test Plan Configuration

Create YAML files to define your test scenarios:

```yaml
# examples/plan.demo_create_employee.yaml
name: "Demo Employee Creation Test"
description: "Test the employee creation flow in the demo application"

steps:
  - title: "Navigate to login page"
    action: "navigate"
    target: "http://127.0.0.1:5000/login"

  - title: "Enter username"
    action: "fill"
    target: "#username"
    data:
      value: "testuser"

  - title: "Enter password"
    action: "fill"
    target: "#password"
    data:
      value: "testpass"

  - title: "Click login button"
    action: "submit"
    target: "button[type='submit']"

  - title: "Fill employee first name"
    action: "fill"
    target: "#first_name"
    data:
      value: "John"

  - title: "Submit employee form"
    action: "submit"
    target: "button[type='submit']"

  - title: "Verify employee created"
    action: "verify"
    verification:
      text: "Employee John Doe created successfully"
```

#### Supported Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `navigate` | Navigate to URL | `target`: URL to navigate to |
| `fill` | Fill form field | `target`: CSS selector, `data.value`: text to enter |
| `click` | Click element | `target`: CSS selector |
| `submit` | Submit form | `target`: CSS selector of submit button |
| `wait` | Pause execution | `data.seconds`: duration to wait |
| `verify` | Verify page content | `verification.text`: text to find, `verification.selector`: element to check |

### Environment Configuration

Define your test environment settings:

```yaml
# examples/env.local.yaml
name: "Local Development Environment"
description: "Test environment using local mock application"

target:
  base_url: "http://127.0.0.1:5000"
  timeout: 30000

credentials:
  username: "testuser"
  password: "testpass"
  domain: "demo.local"

settings:
  headful: true
  slow_mo: 500
  video: true
  screenshots: true
```

#### Environment Parameters

| Section | Parameter | Description |
|---------|-----------|-------------|
| `target` | `base_url` | Base URL for relative paths |
| `target` | `timeout` | Default timeout in milliseconds |
| `credentials` | `username`, `password` | Test credentials |
| `settings` | `headful` | Show browser window |
| `settings` | `slow_mo` | Slow down automation (ms) |
| `settings` | `video` | Enable video recording |
| `settings` | `screenshots` | Enable screenshots |

## 🎛️ Control Room Dashboard

Access the real-time monitoring dashboard at `http://127.0.0.1:8788` when Control Room is enabled.

### Features:
- **Live Progress**: Real-time test step execution
- **Browser Thumbnails**: Live screenshots during test execution  
- **Detailed Logs**: Console, network, and agent messages
- **User Controls**: Approve/reject/stop test execution
- **Run History**: List and monitor multiple test runs

### WebSocket API:
- **Endpoint**: `/ws/{run_id}`
- **Message Types**: `status`, `step`, `log`, `thumbnail`

## 📂 Test Artifacts

Each test run generates comprehensive artifacts in the `artifacts/{run_id}/` directory:

### Generated Files:
- **`run.json`**: Test execution summary and metadata
- **`events.json`**: Detailed chronological event log
- **`trace.zip`**: Complete Playwright execution trace
- **`video/`**: Browser session video recordings
- **`*.png`**: Screenshots (failures, specific steps)

### Artifact Analysis:
- **Videos**: Watch complete test execution
- **Traces**: Open in Playwright trace viewer: `playwright show-trace trace.zip`
- **Screenshots**: Visual evidence of failures and key steps
- **Logs**: Detailed debugging information

## 🧪 Creating Custom Tests

### 1. Create Test Plan
```yaml
name: "My Custom Test"
description: "Description of what this test does"

steps:
  - title: "Navigate to application"
    action: "navigate"
    target: "/my-app"
    
  - title: "Login with test user"
    action: "fill"
    target: "#email"
    data:
      value: "test@example.com"
```

### 2. Create Environment Config
```yaml
name: "My Test Environment"
target:
  base_url: "https://myapp.example.com"
  timeout: 10000
  
settings:
  headful: false
  video: true
```

### 3. Run Your Test
```bash
python -m cli.main run --plan my-test-plan.yaml --env my-environment.yaml --control-room
```

## 🛠️ Advanced Usage

### AI-Powered Features

The framework includes OpenAI integration for intelligent testing:
- **Smart Element Detection**: AI identifies optimal CSS selectors
- **Content Validation**: AI verifies expected vs actual content
- **Error Analysis**: AI provides failure diagnosis

### Programmatic Usage

```python
import asyncio
from orchestrator.graph import TestGraph
from orchestrator.control_room import ControlRoom

async def run_custom_test():
    # Setup Control Room
    cr = ControlRoom()
    cr.start_in_background()
    
    # Create and run test
    graph = TestGraph("./artifacts", headful=False, control_room=cr, run_id="custom-test")
    result = await graph.run("my-plan.yaml", "my-env.yaml")
    
    print(f"Test {result['status']}: {result.get('error', 'Success')}")

asyncio.run(run_custom_test())
```

### Custom Actions

Extend the executor with custom actions:

```python
# In orchestrator/executor.py
async def _custom_action(self, target: str):
    """Custom test action implementation"""
    # Your custom logic here
    pass
```

## 🐛 Troubleshooting

### Common Issues

1. **Browser Dependencies Missing**
   ```bash
   playwright install-deps
   ```

2. **OpenAI API Key Not Set**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Port Already in Use**
   - Change ports in environment configuration
   - Kill existing processes: `pkill -f "uvicorn"`

### Debug Mode
Enable verbose logging:
```bash
export PYTHONPATH=. 
python -m cli.main run --plan test.yaml --env env.yaml --control-room
```

### Artifact Analysis
- **Video Issues**: Check `artifacts/{run_id}/video/` directory
- **Test Failures**: Review `artifacts/{run_id}/events.json`
- **Browser Issues**: Open `trace.zip` in Playwright trace viewer

## 🚀 Next Steps

1. **Create Your First Test**: Start with the demo and modify it for your application
2. **Setup Control Room**: Enable real-time monitoring for better debugging
3. **Customize Configuration**: Adapt environment and test plan templates
4. **Integrate AI Features**: Leverage OpenAI for intelligent test validation
5. **Automate Testing**: Integrate with CI/CD pipelines

## 📚 Documentation

- **Technical Specifications**: See `docs/Technical_Specs.md` for detailed architecture
- **API Reference**: Control Room API documentation in technical specs
- **Examples**: Check `examples/` directory for sample configurations

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review generated artifacts for debugging information
3. Enable Control Room for real-time monitoring
4. Examine technical specifications for architecture details

---

**AI WebTester Framework** - Comprehensive web application testing with browser automation, AI intelligence, and real-time monitoring.