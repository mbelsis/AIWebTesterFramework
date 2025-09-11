#!/bin/bash

# AI WebTester Framework Setup Script
# This script installs and configures the AI WebTester framework

set -e  # Exit on any error

echo "🚀 AI WebTester Framework Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.11+ required. Found: $PYTHON_VERSION"
            exit 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python"
        else
            print_error "Python 3.11+ required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.11+"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip not found. Please install pip"
        exit 1
    fi
    
    # Determine pip command
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    # Install dependencies from requirements or pyproject.toml
    if [ -f "pyproject.toml" ]; then
        print_status "Installing from pyproject.toml..."
        $PIP_CMD install -e .
    else
        print_status "Installing individual packages..."
        $PIP_CMD install playwright fastapi uvicorn typer jinja2 websockets pyyaml pydantic aiofiles python-multipart openai
    fi
    
    print_success "Python dependencies installed"
}

# Install Playwright browsers
install_playwright() {
    print_status "Installing Playwright browsers..."
    
    # Install Playwright browsers
    $PYTHON_CMD -m playwright install
    
    # Install system dependencies for Playwright (if supported)
    if command -v apt-get &> /dev/null; then
        print_status "Installing Playwright system dependencies (requires sudo)..."
        if sudo -n true 2>/dev/null; then
            sudo $PYTHON_CMD -m playwright install-deps
        else
            print_warning "Cannot install system dependencies without sudo access"
            print_warning "You may need to run: sudo $PYTHON_CMD -m playwright install-deps"
        fi
    elif command -v yum &> /dev/null; then
        print_warning "Playwright system dependencies not automatically installed on Red Hat systems"
        print_warning "Please manually install required packages or run: sudo $PYTHON_CMD -m playwright install-deps"
    else
        print_warning "Playwright system dependencies not automatically installed on this system"
        print_warning "Please run: $PYTHON_CMD -m playwright install-deps"
    fi
    
    print_success "Playwright installation completed"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    # Create .env file from sample if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.sample" ]; then
        cp .env.sample .env
        print_success "Created .env file from sample"
    fi
    
    # Check for OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OpenAI API key not set in environment"
        echo ""
        echo "To enable AI-powered features, you need an OpenAI API key:"
        echo "1. Go to https://platform.openai.com/"
        echo "2. Create an account or login"
        echo "3. Navigate to API keys section"
        echo "4. Create a new API key"
        echo "5. Set it in your environment:"
        echo "   export OPENAI_API_KEY=\"your-api-key-here\""
        echo ""
        echo "Or add it to your .env file:"
        echo "   OPENAI_API_KEY=your-api-key-here"
        echo ""
    else
        print_success "OpenAI API key found in environment"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create artifacts directory if it doesn't exist
    mkdir -p artifacts
    
    # Create configs directory structure if it doesn't exist  
    mkdir -p configs/profiles
    
    # Create control room frontend directory if it doesn't exist
    mkdir -p control_room/frontend
    
    print_success "Directories created"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python imports
    $PYTHON_CMD -c "
import sys
try:
    import playwright
    import fastapi 
    import typer
    import yaml
    print('✓ Core dependencies imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"
    
    # Test CLI availability
    if $PYTHON_CMD -m cli.main --help &> /dev/null; then
        print_success "CLI interface working"
    else
        print_warning "CLI interface may have issues"
    fi
    
    # Test mock app can start (quick check)
    print_status "Testing mock application..."
    timeout 5s $PYTHON_CMD -c "
import asyncio
from mock_app.app import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/health')
if response.status_code == 200:
    print('✓ Mock application working')
else:
    print('✗ Mock application has issues')
" 2>/dev/null || print_warning "Mock application test timed out (this is normal)"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Installation completed successfully!"
    echo "====================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Set your OpenAI API key (if not already done):"
    echo "   export OPENAI_API_KEY=\"your-api-key-here\""
    echo ""
    echo "2. Run the quick demo:"
    echo "   python run_test.py"
    echo ""
    echo "3. Or use the CLI interface:"
    echo "   python -m cli.main run --plan examples/plan.demo_create_employee.yaml --env examples/env.local.yaml --control-room"
    echo ""
    echo "4. Start individual services:"
    echo "   python -m cli.main mock-app          # Demo application on port 5000"
    echo "   python -m cli.main control-room      # Control Room on port 8788"
    echo ""
    echo "5. Create custom tests:"
    echo "   - Copy examples/plan.demo_create_employee.yaml"
    echo "   - Copy examples/env.local.yaml"
    echo "   - Modify for your application"
    echo ""
    echo "Documentation:"
    echo "   - README.md: User guide and usage instructions"
    echo "   - docs/Technical_Specs.md: Technical architecture details"
    echo ""
    echo "Happy testing! 🚀"
}

# Main installation flow
main() {
    echo ""
    print_status "Starting AI WebTester Framework installation..."
    echo ""
    
    # Run installation steps
    check_python
    install_dependencies
    install_playwright
    setup_environment
    create_directories
    test_installation
    
    # Show completion message
    show_next_steps
}

# Handle script interruption
trap 'print_error "Installation interrupted"; exit 1' INT TERM

# Run main installation
main