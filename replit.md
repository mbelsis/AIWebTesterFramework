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
- 🧠 **Revolutionary AI Test Generation**: Implemented breakthrough AI-powered test plan generation that automatically creates comprehensive YAML tests from any webpage URL
- 📄 **Comprehensive Documentation Updates**: Updated README.md, Technical_Specs.md, and setup.sh with detailed AI generation examples and real-time monitoring instructions
- 🤖 **OpenAI Integration**: Added PageAnalyzer and TestPlanGenerator classes with GPT-5 integration for intelligent test creation
- 🔍 **Webpage Analysis**: BeautifulSoup integration for HTML parsing and interactive element detection
- ⚡ **CLI Enhancement**: Added 'generate' command with interactive and headful modes for AI test creation
- 🎯 **Sample Generation**: Created demonstration AI-generated test plans showing the revolutionary capability

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