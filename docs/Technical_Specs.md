# AI WebTester Framework - Technical Specifications

## Overview

AI WebTester is a comprehensive Python-based framework for automated web application testing that combines browser automation, AI-powered testing logic, and real-time monitoring capabilities. The framework provides end-to-end testing with visual evidence collection, real-time monitoring, and intelligent test execution.

## Architecture & Technologies

### Core Technologies Stack

#### Programming Languages
- **Python 3.11+**: Primary language for the entire framework
- **JavaScript/TypeScript**: Future frontend development (Control Room dashboard)
- **HTML/CSS**: Mock application templates and UI components

#### Frameworks & Libraries

##### Backend Frameworks
- **FastAPI**: Web framework for Control Room backend and mock application
- **Uvicorn**: ASGI server for serving FastAPI applications
- **Typer**: Command-line interface framework for CLI commands

##### Browser Automation
- **Playwright**: Browser automation library used in this project with Chromium-based execution
- **Async/Await**: Asynchronous programming for concurrent browser operations

##### AI & Data Processing  
- **OpenAI API**: AI-powered testing logic and intelligent decision making
- **PyYAML**: YAML configuration file parsing for test plans and environments
- **Pydantic**: Data validation and settings management
- **BeautifulSoup**: HTML parsing for webpage analysis and element extraction

##### Communication & Monitoring
- **WebSockets**: Real-time communication between Control Room and test execution
- **Jinja2**: Template engine for HTML rendering in mock applications
- **Python-multipart**: Form data handling for web applications

##### Utility Libraries
- **AsyncIO**: Asynchronous I/O operations and concurrency management
- **AIOFiles**: Asynchronous file operations for evidence collection
- **Pathlib**: Modern file system path handling

## File Structure & Organization

```
ai-webtester/
├── cli/                           # Command Line Interface
│   ├── __init__.py               # Package initialization
│   └── main.py                   # Main CLI entry point with Typer commands
│
├── orchestrator/                  # Core Test Execution Engine
│   ├── __init__.py               # Package initialization  
│   ├── control_room.py           # Control Room backend server and WebSocket handler
│   ├── graph.py                  # Test execution graph and plan processing
│   ├── executor.py               # Step-by-step test execution engine
│   ├── page_analyzer.py          # AI-powered webpage analysis and element detection
│   └── test_plan_generator.py    # Automatic test plan generation from URLs
│
├── browser/                       # Browser Automation Layer
│   ├── __init__.py               # Package initialization
│   └── context.py                # Playwright browser context management
│
├── evidence/                      # Artifact Collection System
│   ├── __init__.py               # Package initialization
│   └── sink.py                   # Evidence collection and storage
│
├── mock_app/                      # Demo Testing Application
│   ├── __init__.py               # Package initialization
│   ├── app.py                    # FastAPI demo application
│   └── templates/                # HTML templates
│       ├── login.html            # Login page template
│       └── employees_new.html    # Employee creation form
│
├── examples/                      # Configuration Templates
│   ├── env.local.yaml            # Local environment configuration
│   └── plan.demo_create_employee.yaml # Sample test plan
│
├── configs/                       # System Configuration (Future Use)
│   └── profiles/                 # User profiles directory
│
├── control_room/                  # Real-time Monitoring Dashboard
│   ├── backend/                  # Control Room backend (integrated in orchestrator)
│   └── frontend/                 # React/Vite frontend (future implementation)
│
├── docs/                          # Documentation
│   └── Technical_Specs.md        # This technical specification document
│
├── artifacts/                     # Generated Test Artifacts (auto-created)
│   └── [run_id]/                 # Per-run artifact directories
│       ├── video/                # Browser session recordings
│       ├── trace.zip             # Playwright execution traces
│       ├── events.json           # Detailed event logs
│       ├── run.json              # Test run summary
│       └── *.png                 # Screenshots (failures, steps)
│
├── pyproject.toml                # Python project configuration and dependencies
├── run_test.py                   # Quick test runner script
├── setup.sh                     # Installation and setup script
├── README.md                     # User documentation and usage guide
├── replit.md                     # Project memory and preferences
└── .env.sample                   # Environment variables template
```

## Internal Logic & Workflow

### 1. AI-Powered Test Plan Generation Flow

#### Revolutionary Feature: Automatic Test Plan Creation

The framework now includes breakthrough AI-powered test plan generation that eliminates the need for manual YAML creation:

#### Step 1: Page Analysis
1. **URL Input**: User provides webpage URL via `ai-webtester generate` command
2. **Browser Automation**: Playwright launches browser and navigates to target URL
3. **HTML Extraction**: Complete page HTML structure captured for analysis
4. **Element Detection**: Interactive elements (forms, buttons, inputs, links) automatically identified
5. **Page Classification**: AI determines page type (login, registration, dashboard, etc.)

#### Step 2: AI-Powered Analysis
1. **OpenAI Integration**: Page content and structure sent to the configured OpenAI model
2. **Intelligent Test Generation**: AI generates comprehensive test scenarios based on:
   - Detected forms and input fields
   - Interactive elements and user flows
   - Page type and common testing patterns
   - Security considerations (injection, XSS testing)
   - Edge cases and validation scenarios
3. **Test Plan Creation**: Complete YAML test plan generated with realistic test data
4. **Environment Configuration**: Matching environment config created with appropriate settings

#### Step 3: File Generation
1. **YAML Output**: Generated test plan saved as executable YAML file
2. **Environment Setup**: Corresponding environment configuration created
3. **User Notification**: File paths and execution commands provided to user

### 2. Traditional Test Execution Flow

#### Step 1: Initialization
1. **CLI Command Processing**: User invokes test via `ai-webtester run` or uses AI-generated plans
2. **Configuration Loading**: System loads test plan (manually created or AI-generated) and environment
3. **Run ID Generation**: Unique timestamp-based identifier created for this test session
4. **Artifact Directory Setup**: Creates dedicated directory for all test outputs

#### Step 2: Component Initialization  
1. **Control Room Startup** (if enabled):
   - FastAPI server starts on port 8788
   - WebSocket endpoints configured for real-time communication
   - API endpoints setup for run management
   
2. **Browser Context Creation**:
   - Playwright instance launched
   - Chromium browser started in headful/headless mode
   - Context configured with video recording and tracing enabled
   - Page instance created for automation

3. **Evidence Collection Setup**:
   - Evidence sink initialized with artifact directory
   - Event logging system activated
   - Screenshot capture system prepared

#### Step 3: Test Plan Execution
1. **Plan Parsing**: YAML test plan loaded and validated
2. **Step Iteration**: Each test step processed sequentially:
   
   **For Each Step**:
   - **Pre-execution**: Step status broadcast to Control Room
   - **Target Resolution**: URLs resolved using base_url from environment
   - **Action Execution**: Based on step action type:
     - `navigate`: Browser navigates to specified URL
     - `fill`: Form fields populated with test data
     - `click`: Elements clicked (buttons, links)
     - `submit`: Forms submitted  
     - `wait`: Pauses for specified duration
     - `verify`: Page state validation
   - **Evidence Capture**: Screenshots on failures, event logging
   - **Status Update**: Results sent to Control Room and evidence sink

#### Step 4: Active AI Integration Points
1. **Test Plan Generation**: OpenAI-assisted test plan creation from page analysis
2. **Fallback Generation**: Rule-based fallback plan creation when OpenAI is unavailable

#### Step 5: Cleanup & Artifact Generation
1. **Browser Cleanup**: 
   - Tracing stopped and saved to trace.zip
   - Browser context closed
   - Browser instance terminated
   - Playwright process stopped

2. **Evidence Finalization**:
   - Event logs saved to events.json
   - Final test summary generated (run.json)
   - Video files processed and stored
   - Screenshots organized by step/failure

3. **Status Reporting**:
   - Control Room notified of completion
   - Final status (passed/failed) determined
   - Artifacts list compiled and returned

### 2. Control Room Real-time Monitoring

#### WebSocket Communication Protocol
- **Connection**: `/ws/{run_id}` endpoint for each test session
- **Message Types**:
  - `status`: Overall test status updates
  - `step`: Individual step progress and results  
  - `log`: Console/network/agent messages
  - `thumbnail`: Live browser screenshots (1-2 FPS)

#### User Interaction Controls
- **Approval Gates**: Tests can pause for user approval on destructive actions
- **Manual Intervention**: Users can approve/reject/stop tests via Control Room
- **Live Monitoring**: Real-time visibility into test execution progress

### 3. Configuration System

#### Test Plans (YAML)
```yaml
name: "Test Plan Name"
description: "Test description"
steps:
  - title: "Step description"
    action: "navigate|fill|click|submit|wait|verify"
    target: "CSS selector or URL"
    data:
      value: "input data"
    verification:
      text: "expected text"
      selector: "element selector"
```

#### Environment Configuration (YAML)
```yaml
name: "Environment Name"
description: "Environment description"
target:
  base_url: "http://localhost:5000"
  timeout: 30000
credentials:
  username: "test_user"
  password: "test_pass"
settings:
  headful: true
  slow_mo: 500
  video: true
  screenshots: true
```

### 4. Error Handling & Resilience

#### Browser Automation Resilience
- **Element Waiting**: Automatic waits for elements before interaction
- **Timeout Management**: Configurable timeouts from environment settings
- **Network Stability**: Wait for network idle states after navigation

#### Failure Recovery
- **Automatic Screenshots**: Failure points captured visually
- **Detailed Logging**: Comprehensive event and error logging
- **Resource Cleanup**: Guaranteed cleanup even on failures
- **Graceful Degradation**: Tests continue when possible, fail safely when not

#### Evidence Preservation
- **Failure Screenshots**: Automatic capture on step failures
- **Complete Traces**: Full Playwright traces for debugging
- **Event Timelines**: Detailed chronological event logs
- **Video Recordings**: Complete browser session recordings

### 5. Extensibility Points

#### Custom Actions
- Executor supports additional action types through method extension
- Plugin architecture for custom verification methods

#### AI Enhancement Integration  
- OpenAI API integration points throughout execution flow
- Modular AI services for different testing aspects
- Configurable AI model selection and parameters

#### Reporting Extensions
- Evidence system designed for multiple output formats
- Template-based report generation capability
- Integration points for external reporting systems

### 6. Performance & Scalability

#### Asynchronous Architecture
- Full async/await implementation for concurrent operations
- Non-blocking I/O for file and network operations
- Parallel evidence collection and browser automation

#### Resource Management
- Automatic browser process cleanup
- Memory-efficient event streaming
- Configurable video recording settings for storage optimization

#### Concurrent Testing (Future)
- Architecture supports multiple parallel test sessions
- Unique run IDs prevent artifact conflicts
- Isolated browser contexts for test isolation

## Security Considerations

### API Key Management
- OpenAI API keys stored in environment variables
- No key exposure in code or logs
- Secure integration with Replit Secrets

### Local Development Security
- Control Room runs on localhost only by default
- No authentication on local WebSocket connections
- Production deployment would require authentication layer

### Browser Security
- Sandboxed browser contexts
- No persistence of sensitive data between test runs
- Configurable browser security settings

### 3. AI Test Plan Generation Architecture

#### Core Components

**PageAnalyzer Class** (`orchestrator/page_analyzer.py`):
- **Browser Automation**: Launches Playwright browser to analyze target webpages
- **Element Extraction**: Identifies all interactive elements (forms, buttons, inputs, links)
- **HTML Parsing**: Uses BeautifulSoup for detailed HTML structure analysis  
- **Page Classification**: Determines page type (login, registration, checkout, dashboard, etc.)
- **Screenshot Capture**: Takes screenshots for AI visual analysis
- **Selector Generation**: Creates robust CSS selectors for element targeting

**TestPlanGenerator Class** (`orchestrator/test_plan_generator.py`):
- **AI Integration**: Connects with the configured OpenAI provider for test plan creation
- **YAML Generation**: Produces complete test plans with realistic scenarios
- **Environment Configuration**: Creates matching environment configs with proper settings
- **File Management**: Saves generated files with organized naming conventions
- **Interactive Mode**: Provides guided user experience for test generation

#### AI Model Integration
- **Default Model**: `gpt-4o-mini`
- **Supported Models in Code**: `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4o`, `gpt-4`
- **Input**: Page structure, detected elements, user requirements
- **Output**: Comprehensive JSON test plan converted to YAML format
- **Capabilities**: 
  - Form validation testing
  - Security scenario generation (SQL injection, XSS)
  - User journey mapping
  - Edge case identification
  - Realistic test data creation

## Infrastructure Improvements (2025)

### 🚀 **CI/CD Pipeline Architecture**

**GitHub Actions Workflow** (`.github/workflows/ci.yml`):
- **Multi-job Strategy**: 3 parallel jobs (test, lint, security) for comprehensive validation
- **Matrix Testing**: Python 3.11 and 3.12 in the test job
- **Browser Automation**: Full Playwright installation with Chromium browser and system dependencies
- **Mock App Service**: Background mock application with health checks and proper cleanup
- **AI Integration**: OpenAI generation step with `continue-on-error: true`; generator fallback exists in application code
- **Artifact Collection**: Complete evidence gathering with 30-day retention
- **Security Scanning**: Workflow runs Safety and Bandit to validate the framework's own dependencies and Python code

See [CI_CD_Pipeline.md](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/GitHub_Actions/CI_CD_Pipeline.md) for the detailed GitHub Actions pipeline documentation and the explanation of why the executable workflow must remain under `.github/workflows/`.

**Key Features**:
- **Fail-Safe Design**: The AI generation step does not fail the entire job
- **Secret Management**: OpenAI API key is passed from GitHub Actions secrets when available
- **Performance Optimized**: Uses `uv pip` with caching for fast dependency installation
- **Cross-Platform**: Ubuntu latest with comprehensive browser dependency support

**Security Job Scope**:
- Validates the safety of AI WebTester itself
- Protects users who run the framework in CI with credentials, artifacts, and internal URLs
- Does not assess the security posture of the application under test

### 🔒 **Security Infrastructure**

**Security Redaction System** (`configs/security.yaml`, `utils/redaction.py`):
- **Comprehensive Pattern Matching**: 21 regex patterns for sensitive data detection
- **Multi-Format Support**: JSON, HTML, XML structure-preserving redaction
- **Framework Integration**: Applied across logs, evidence collection, and LLM communications
- **Performance Optimized**: Fast processing (28ms for 40k characters)
- **Audit Trail**: Complete redaction activity logging for compliance

**Protected Data Types**:
- Authorization tokens and API keys
- Personal information (emails, phone numbers, SSNs)
- Database credentials and connection strings
- Payment information and financial data
- Authentication tokens and session data

### 🤖 **Modern AI Provider Architecture**

**OpenAI Integration** (`providers/openai_provider.py`):
- **SDK Usage**: OpenAI Responses API with structured JSON mode
- **Retry Logic**: Exponential backoff with 90-second timeout and fallback parsing
- **Model Support**: `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4o`, `gpt-4`
- **Error Resilience**: Graceful degradation when API unavailable
- **Security Integration**: Input/output redaction for sensitive data protection

### 🎯 **Test Data Management**

**Seeded Faker System** (`data_gen/faker_util.py`, `utils/data_generation.py`):
- **Deterministic Generation**: Same run_id produces identical data across executions
- **Run Isolation**: Different run_ids generate unique but consistent datasets
- **Email Uniqueness**: Run-specific email suffixes prevent conflicts
- **Realistic Data**: Comprehensive user profiles, addresses, payment data
- **Form Integration**: Dynamic form field detection and appropriate data injection

### ⚡ **Reliability Features**

**Stuck-Screen Watchdog** (`utils/watchdog.py`, `configs/watchdog.yaml`):
- **Multi-Indicator Monitoring**: DOM hash, request count, pixel signatures
- **Intelligent Recovery**: Back navigation, page reload, graceful continuation
- **Configurable Detection**: 12-second timeout with environment-specific settings
- **Evidence Integration**: State snapshots and health metrics for debugging
- **Performance Optimized**: Minimal overhead during normal operations

**Automatic Port Detection** (`utils/ports.py`):
- **Dynamic Port Allocation**: Automatic free port discovery starting from preferred ranges
- **Conflict Prevention**: Eliminates "port already in use" errors
- **Multi-Service Support**: Independent port allocation for mock app and Control Room
- **Environment Flexibility**: Supports concurrent development environments

### 🎥 **Evidence Durability System**

**Video Finalization** (`browser/context.py`, `orchestrator/graph.py`):
- **Guaranteed Durability**: Proper Playwright context closure ensures video flush
- **Stability Validation**: File size monitoring to confirm complete video recording
- **Artifact Organization**: Recursive discovery of videos, traces, screenshots, logs
- **Run Summaries**: Both minimal `run.json` and comprehensive `run_summary.json`
- **Error Resilience**: Complete evidence collection even during test failures

## Current Status & Implementation

### Fully Implemented Features
1. ✅ **AI Test Plan Generation**: Webpage analysis and OpenAI-assisted plan creation with rule-based fallback
2. ✅ **Browser Automation**: Chromium Playwright integration with guaranteed video finalization and durability
3. ✅ **Real-time Monitoring**: Control Room with live WebSocket communication and automatic port detection
4. ✅ **Evidence Collection**: Comprehensive artifact generation with security redaction and guaranteed persistence
5. ✅ **CLI Interface**: Complete command-line interface with seeded data generation and AI integration
6. ✅ **OpenAI Integration**: Modern Responses API with JSON mode, retry logic, and security redaction
7. ✅ **Multi-format Output**: YAML test plans and environment configurations with realistic faker data
8. ✅ **CI/CD Pipeline**: GitHub Actions workflow with multi-Python test coverage, linting, artifact collection, and framework security checks
9. ✅ **Security Infrastructure**: Enterprise-grade data redaction across all framework components
10. ✅ **Reliability Features**: Stuck-screen watchdog and automatic port conflict resolution
11. ✅ **Test Data Management**: Seeded Faker with run-specific uniqueness and realistic data generation

### Future Enhancements
1. **Control Room Frontend**: React/Vite dashboard for enhanced monitoring
2. **Multi-browser Support**: Support for browsers beyond the current Chromium-based execution path
3. **Report Generation**: PDF and HTML report generation with custom templates
4. **Test Recording**: Record user actions to generate test plans
5. **Visual Regression**: AI-powered visual comparison testing
6. **Performance Monitoring**: Page load time and performance metrics with thresholds
