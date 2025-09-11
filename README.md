# AI WebTester Framework

A comprehensive Python-based framework for automated web application testing that combines browser automation, AI-powered testing logic, and real-time monitoring capabilities.

## 🎯 What is AI WebTester?

AI WebTester is a powerful testing framework designed to automate web application testing through browser automation while providing comprehensive evidence collection and real-time monitoring. The framework captures videos, traces, screenshots, and detailed logs of every test execution, making it perfect for documenting application behavior and debugging issues.

### Key Features

- **🧠 Revolutionary AI Test Generation**: Automatically generate comprehensive test plans from any URL - no more manual YAML writing!
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

3. **Configure environment variables**:
   ```bash
   # Copy the sample environment file
   cp env.sample .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your-actual-openai-api-key-here
   
   # Or set directly in your shell
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Quick Demo - Choose Your Testing Experience

The AI WebTester framework includes **two demo applications** to showcase its testing capabilities, from simple to comprehensive scenarios.

#### 🎯 **Option 1: Comprehensive Calendar App Demo (Recommended)**

**What it is**: A full-featured calendar application with user authentication, event management, and complete CRUD operations - perfect for demonstrating real-world testing scenarios.

**Start the Calendar Application**:
```bash
# Navigate to the calendar app and start it
cd examples/calendar_app
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# The app will be available at http://127.0.0.1:5000
# Demo accounts: admin/admin123, john/password, alice/alice123
```

**Test the Calendar App** (choose any approach):

**AI-Generated Tests** (Let AI create comprehensive test plans):
```bash
# Generate login tests automatically
python -m cli.main generate http://127.0.0.1:5000/login --description "Test login functionality with security validation"

# Generate calendar navigation tests  
python -m cli.main generate http://127.0.0.1:5000/calendar --description "Test calendar navigation and event management"

# Run the AI-generated tests with real-time monitoring
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room
```

**Pre-built Test Suites** (Ready-to-run comprehensive tests):
```bash
# Test login functionality
python -m cli.main run --plan examples/plan.calendar_login_test.yaml --env examples/env.calendar_login_test.yaml --control-room

# Test calendar navigation  
python -m cli.main run --plan examples/plan.calendar_navigation_test.yaml --env examples/env.calendar_navigation_test.yaml --control-room

# Test event management (create, edit, delete events)
python -m cli.main run --plan examples/plan.calendar_add_events_test.yaml --env examples/env.calendar_add_events_test.yaml --control-room
```

**What you'll see**: Complete testing of login forms, calendar navigation, event creation/editing, user sessions, form validation, and data persistence.

#### 🚀 **Option 2: Simple Mock App Demo (Quick Start)**

**What it is**: A minimal employee management app for basic framework demonstration.

```bash
# One-command demo that handles everything
python run_test.py
```

This automatically:
- Starts the simple mock application on port 5000
- Launches the Control Room dashboard on port 8788  
- Executes a basic employee creation test
- Generates test artifacts in `artifacts/` directory

**What you'll see**: Basic form filling, submission, and result verification in a simple web application.

#### 📊 **Real-time Monitoring**

For both demos, when you use `--control-room`, visit **http://127.0.0.1:8788** to see:
- Live browser screenshots during test execution
- Step-by-step progress with success/failure indicators
- Console logs, network requests, and detailed timing
- Generated artifacts (videos, traces, screenshots)

#### 🎯 **Which Demo Should You Try?**

- **New to the framework?** Start with **Option 2** (Simple Mock App) for a quick 2-minute overview
- **Want to see real capabilities?** Use **Option 1** (Calendar App) to experience comprehensive testing scenarios  
- **Evaluating for your project?** The Calendar App demonstrates real-world complexity your applications might have

## 🔧 Manual Environment Setup

For environments where the automated setup script doesn't work or when you need full control over the installation process, follow these manual setup steps:

### System Requirements
- **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Windows with WSL
- **Python**: 3.11 or higher
- **Memory**: At least 2GB RAM available
- **Storage**: 1GB free space for browser dependencies

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
# Update package lists
sudo apt-get update

# Install Python and pip
sudo apt-get install python3.11 python3.11-pip python3.11-venv

# Install browser system dependencies required by Playwright
sudo apt-get install \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2t64 \
    libxcb1 \
    libxkbcommon0 \
    libatspi2.0-0t64 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libgbm1 \
    libcairo2 \
    libpango-1.0-0 \
    libasound2t64
```

**macOS:**
```bash
# Install Python using Homebrew
brew install python@3.11

# Browser dependencies are automatically handled on macOS
```

**CentOS/RHEL/Fedora:**
```bash
# Install Python
sudo dnf install python3.11 python3.11-pip

# Install browser dependencies
sudo dnf install \
    nspr \
    nss \
    dbus-libs \
    atk \
    at-spi2-atk \
    cups-libs \
    libxcb \
    libxkbcommon \
    at-spi2-core \
    libXcomposite \
    libXdamage \
    libXfixes \
    mesa-libgbm \
    cairo \
    pango \
    alsa-lib
```

### Step 2: Create Virtual Environment

```bash
# Create a virtual environment
python3.11 -m venv ai-webtester-env

# Activate the virtual environment
source ai-webtester-env/bin/activate  # Linux/macOS
# OR for Windows:
# ai-webtester-env\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Make sure you're in the project directory and virtual environment is activated

# Install dependencies (recommended method)
pip install --upgrade pip
pip install -e ".[dev]"

# Note: pyproject.toml contains the authoritative dependency versions
# See pyproject.toml for authoritative versions.
# Manual install alternative (use compatible ranges):
uv pip install \
  "typer[all]>=0.12,<0.15" \
  "playwright>=1.46,<1.49" \
  "fastapi>=0.111,<0.116" \
  "uvicorn[standard]>=0.27,<0.32" \
  "websockets>=12,<15" \
  "pyyaml>=6,<7" \
  "jinja2>=3.1,<3.2" \
  "beautifulsoup4>=4.12,<4.13" \
  "aiofiles>=23,<24" \
  "openai>=1.40,<2"

# Install additional development tools (optional)
pip install pytest pytest-asyncio
```

### Step 4: Install Browser Dependencies

```bash
# Install Playwright browsers and their dependencies
playwright install

# This downloads Chromium, Firefox, and WebKit browsers
# If you only need Chromium (recommended for most cases):
playwright install chromium

# Alternatively, use the system dependency installer
playwright install-deps
```

### Step 5: Set Environment Variables

```bash
# Option 1: Use environment file (recommended)
cp env.sample .env
# Then edit .env file and set: OPENAI_API_KEY=your-actual-openai-api-key-here

# Option 2: Set directly in shell
export OPENAI_API_KEY="your-actual-openai-api-key-here"

# Option 3: Add to your shell profile for persistence
echo 'export OPENAI_API_KEY="your-actual-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 6: Verify Installation

```bash
# Test the CLI is working
python -m cli.main --help

# Test AI generation capabilities
python -m cli.main generate --help

# Start the mock application for testing
python -m cli.main mock-app &

# Test that the mock app is running
curl http://127.0.0.1:5000/login

# Test browser automation (this should work without errors now)
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml

# Test Control Room dashboard
python -m cli.main control-room &
# Then visit http://127.0.0.1:8788 in your browser
```

### Step 7: Test Full AI Generation Pipeline

```bash
# Generate a test plan using AI (requires OpenAI API key)
python -m cli.main generate http://127.0.0.1:5000/login --description "Test login functionality with edge cases"

# Run the AI-generated test with Control Room monitoring
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room --headful

# View results
ls artifacts/  # Check generated artifacts
playwright show-trace artifacts/*/trace.zip  # View detailed execution trace
```

### Troubleshooting Manual Installation

**Issue: Browser launch fails with dependency errors**
```bash
# Run the Playwright dependency installer
playwright install-deps

# Or manually install missing dependencies shown in error message
sudo apt-get install [missing-package-names]
```

**Issue: Python import errors**
```bash
# Make sure virtual environment is activated
source ai-webtester-env/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Issue: OpenAI API errors**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print('OpenAI client initialized successfully')"
```

**Issue: Port conflicts**
```bash
# Kill processes using default ports
sudo lsof -ti:5000 | xargs kill -9  # Mock app port
sudo lsof -ti:8788 | xargs kill -9  # Control Room port

# Or use different ports in environment config files
```

### Docker Alternative (Advanced)

If you prefer containerized setup:

```bash
# Create Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \\
    libnspr4 libnss3 libdbus-1-3 libatk1.0-0t64 \\
    libatk-bridge2.0-0t64 libcups2t64 libxcb1 \\
    libxkbcommon0 libatspi2.0-0t64 libxcomposite1 \\
    libxdamage1 libxfixes3 libgbm1 libcairo2 \\
    libpango-1.0-0 libasound2t64

WORKDIR /app
COPY . .
RUN pip install [dependencies-list]
RUN playwright install

CMD ["python", "-m", "cli.main", "control-room"]
EOF

# Build and run
docker build -t ai-webtester .
docker run -p 8788:8788 -p 5000:5000 ai-webtester
```

### Production Deployment Considerations

- **Resource Requirements**: Ensure adequate CPU/memory for browser automation
- **Headless Mode**: Use `--no-headful` in production environments
- **Artifact Storage**: Configure persistent storage for test results
- **API Rate Limits**: Monitor OpenAI API usage in high-volume scenarios
- **Security**: Keep OpenAI API keys secure and rotate regularly

## 📖 Usage Guide

### 🧠 AI-Powered Test Generation (Revolutionary Feature!)

Instead of spending time writing YAML files, let AI analyze your web application and generate comprehensive test plans automatically!

#### Generate Test Plans from URLs

```bash
# Basic AI generation - analyzes any webpage and creates tests
python -m cli.main generate https://your-app.com/login

# With custom description for targeted testing
python -m cli.main generate https://your-app.com/checkout --description "Test complete checkout flow with payment validation"

# Interactive mode with guided prompts
python -m cli.main generate https://your-app.com --interactive

# Watch the AI analyze your page (when browser deps installed)
python -m cli.main generate https://your-app.com --headful
```

**What the AI generates for you:**
- ✅ Complete YAML test plan with realistic scenarios
- ✅ Environment configuration with proper timeouts
- ✅ Test data including edge cases and security tests
- ✅ Form validation and error handling tests
- ✅ User journey coverage for your specific page type

#### Example AI Generation Workflows

**Example 1: E-commerce Login Page**
```bash
# 1. Generate comprehensive login tests
python -m cli.main generate https://shop.example.com/login --description "Test login with security validation"

# 2. Run the AI-generated test with real-time monitoring
python -m cli.main run --plan examples/plan.generated_login.yaml --env examples/env.generated_login.yaml --control-room

# 3. View results at http://127.0.0.1:8788 and check artifacts/
```

**Example 2: Complex Registration Form**
```bash
# 1. Let AI analyze registration form and create comprehensive tests
python -m cli.main generate https://app.example.com/register --description "Test user registration with validation and edge cases"

# 2. Run with video recording and detailed evidence collection
python -m cli.main run --plan examples/plan.generated_register.yaml --env examples/env.generated_register.yaml --control-room

# 3. Monitor live at Control Room and review generated artifacts
```

**Example 3: Dashboard Testing**
```bash
# 1. Generate tests for admin dashboard functionality
python -m cli.main generate https://admin.example.com/dashboard --description "Test dashboard analytics and user management"

# 2. Execute with headful mode to watch the test run
python -m cli.main run --plan examples/plan.generated_dashboard.yaml --env examples/env.generated_dashboard.yaml --control-room --headful
```

### Command Line Interface

The framework provides several CLI commands:

#### Generate AI Test Plans
```bash
# AI test plan generation (recommended approach)
python -m cli.main generate <URL> [--description "test description"] [--interactive] [--headful] [--output-dir examples]
```

#### Run Tests  
```bash
# Basic test execution
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml

# With Control Room monitoring (recommended for real-time viewing)
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --control-room

# Headless mode
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --headful false

# Custom artifacts directory
python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --artifacts-dir ./my-test-results
```

#### Start Services
```bash
# Start Control Room dashboard for real-time monitoring
python -m cli.main control-room

# Start demo application for testing
python -m cli.main mock-app
```

### CLI Parameters

#### AI Generation Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|  
| `url` | URL to analyze and generate test plan for | Required |
| `--description` | Description of what to test | Auto-detected |
| `--output-dir` | Output directory for generated files | `examples` |
| `--headful` | Show browser during analysis | `false` |
| `--interactive` | Interactive mode with prompts | `false` |

#### Test Execution Parameters  
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

## 🎛️ Control Room Dashboard - Real-time Test Monitoring

Access the real-time monitoring dashboard at `http://127.0.0.1:8788` when Control Room is enabled.

### Live Monitoring Features:
- **Live Progress**: Watch test steps execute in real-time with status updates
- **Browser Thumbnails**: Live screenshots showing exactly what's happening during test execution  
- **Detailed Logs**: Console, network, and AI agent messages with timestamps
- **User Controls**: Approve/reject/stop test execution for interactive testing
- **Run History**: List and monitor multiple concurrent test runs
- **Evidence Preview**: Live preview of screenshots, videos, and traces as they're generated

### How to View Tests in Real-time:

1. **Start a test with Control Room enabled:**
   ```bash
   python -m cli.main run --plan your-test-plan.yaml --env your-environment.yaml --control-room
   ```

2. **Open Control Room Dashboard:**
   - Navigate to `http://127.0.0.1:8788` in your browser
   - You'll see live test progress, browser screenshots, and detailed logs

3. **Monitor Test Execution:**
   - **Live Browser View**: Watch browser actions happen in real-time through thumbnails
   - **Step Progress**: See each test step execute with success/failure indicators  
   - **Live Logs**: View console output, network requests, and AI decision making
   - **Artifacts**: Access screenshots, videos, and traces as they're generated

### WebSocket API:
- **Endpoint**: `/ws/{run_id}`
- **Message Types**: `status`, `step`, `log`, `thumbnail`, `artifact`
- **Real-time Updates**: Live streaming of test progress and browser state

## 📂 Test Artifacts & Results Documentation

Each test run generates comprehensive artifacts in the `artifacts/{run_id}/` directory for complete test documentation:

### Generated Files:
- **`run.json`**: Test execution summary and metadata with timing information
- **`events.json`**: Detailed chronological event log with AI decisions and browser actions
- **`trace.zip`**: Complete Playwright execution trace for deep debugging
- **`video/`**: Browser session video recordings showing complete user journey
- **`*.png`**: Screenshots (failures, specific steps, verification points)

### How to View and Analyze Results:

#### 🎥 **Video Analysis**
```bash
# Videos are automatically saved during test execution
ls artifacts/test-run-*/video/
# Play the .webm files to see complete browser automation
```

#### 🔍 **Trace Analysis** (Most Powerful Debugging Tool)
```bash
# Open complete execution trace in Playwright's trace viewer
playwright show-trace artifacts/test-run-*/trace.zip

# This opens a comprehensive timeline showing:
# - Every browser action and network request
# - Screenshots at each step
# - Console logs and JavaScript execution
# - Performance metrics and timings
```

#### 📊 **Log Analysis**
```bash
# View detailed test execution logs
cat artifacts/test-run-*/events.json | jq .

# Check test summary
cat artifacts/test-run-*/run.json | jq .
```

#### 🖼️ **Screenshot Evidence**
```bash
# View all screenshots taken during test
ls artifacts/test-run-*/screenshot_*.png

# Screenshots are automatically taken on:
# - Test failures
# - Verification steps  
# - Key user journey points
```

### Artifact Analysis Benefits:
- **Videos**: Perfect for documentation and showing stakeholders exactly what the test does
- **Traces**: Essential for debugging failed tests - shows exact failure point with browser state
- **Screenshots**: Visual evidence for test reports and failure analysis
- **Logs**: Detailed technical information for developers and QA teams

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