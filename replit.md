# AI WebTester Framework

## Project Overview
AI WebTester is a comprehensive Python framework for automated web application testing that combines browser automation, AI-powered testing logic, and real-time monitoring capabilities.

## Architecture
- **CLI Interface**: Typer-based command line for running tests and starting services
- **Orchestrator**: Core test execution engine with graph-based plan execution
- **Browser Automation**: Playwright integration with video recording and tracing
- **Control Room**: Real-time monitoring dashboard with WebSocket communication
- **Evidence Collection**: Comprehensive artifact generation including videos, traces, screenshots
- **Mock Demo App**: FastAPI-based test application for framework validation

## Recent Changes (2025-09-11)
- 🔧 **P0 Critical Fixes**: Addressed code review blockers including .gitignore for artifacts, updated dependency versions, GitHub Actions CI pipeline, and file reorganization
- 📁 **Project Reorganization**: Moved calendar_app to examples/calendar_app for better structure and reduced root directory clutter
- 🚀 **CI/CD Pipeline**: Added comprehensive GitHub Actions workflow with multi-Python version testing, Playwright automation, and artifact collection
- 📦 **Dependency Management**: Aligned README with pyproject.toml versions and established single source of truth for dependencies
- 🧠 **Revolutionary AI Test Generation**: Implemented breakthrough AI-powered test plan generation that automatically creates comprehensive YAML tests from any webpage URL
- 🤖 **OpenAI Integration**: Added PageAnalyzer and TestPlanGenerator classes with intelligent test creation capabilities
- 🔍 **Webpage Analysis**: BeautifulSoup integration for HTML parsing and interactive element detection
- ⚡ **CLI Enhancement**: Added 'generate' command with interactive and headful modes for AI test creation

## User Preferences
- Prefer comprehensive error handling and logging
- Focus on evidence collection and artifact generation
- Emphasis on real-time monitoring and control room functionality
- Use modern Python async/await patterns

## Project Structure
```
ai-webtester/
├── cli/                    # Command line interface
├── orchestrator/           # Core execution engine
├── browser/               # Playwright browser automation
├── evidence/              # Artifact collection and reporting
├── mock_app/              # Demo FastAPI application
├── control_room/          # Real-time monitoring interface
├── examples/              # Configuration templates
└── configs/               # System configuration
```

## Current Status
- Core framework implemented with basic functionality
- Mock demo application running on port 5000
- Dependencies installed and configured
- OpenAI integration ready for AI-powered features
- Ready for Control Room frontend implementation and full system testing