# Calendar App Testing Guide

## Overview

This guide demonstrates how to test a comprehensive Python calendar application using the AI WebTester framework. The calendar app features user authentication, monthly calendar navigation, and event management with JSON storage.

## Prerequisites and Setup

### 🛠️ **Installation Requirements**

Before testing, ensure you have the following dependencies installed:

```bash
# Install Python dependencies
pip install fastapi uvicorn jinja2 pyyaml beautifulsoup4 aiofiles

# Install AI WebTester framework dependencies (if not already installed)
pip install typer playwright openai

# Install browser automation dependencies
playwright install
```

### 📋 **Start the Calendar Application**

```bash
# Navigate to the calendar app directory
cd calendar_app

# Start the application (runs on port 5000)
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Calendar Application Features

### 🔐 **Authentication System**
- **Login Page**: Username/password authentication
- **Demo Accounts**: 
  - **Admin**: `admin` / `admin123`
  - **User**: `john` / `password` 
  - **User**: `alice` / `alice123`
- **Session Management**: Basic in-memory session storage (demo purposes)
- **Logout Functionality**: Clean session termination

### 📅 **Calendar Interface**
- **Monthly View**: Interactive calendar grid with navigation
- **Month Navigation**: Previous/Next month browsing
- **Day Headers**: Full week display (Sun-Sat)
- **Responsive Design**: Clean, professional interface

### 📝 **Event Management**
- **Add Events**: Click any date to create events
- **Event Modal**: Form with title, description, date, time
- **Event Storage**: JSON file persistence
- **Event Display**: Upcoming events list
- **Form Validation**: Required fields and data validation

## Testing Approaches

### Method 1: Manual YAML Test Plans (Detailed Control)

We've created three comprehensive test suites for different aspects of the application:

#### 1. Login Functionality Test

**Test File**: `examples/plan.calendar_login_test.yaml`  
**Environment**: `examples/env.calendar_login_test.yaml`

**Test Coverage**:
- ✅ Valid login with all three demo accounts
- ✅ Invalid password handling
- ✅ Non-existent user validation
- ✅ Empty form submission prevention
- ✅ Successful redirects after login
- ✅ Session management and logout
- ✅ Error message display

**Run the test**:
```bash
python -m cli.main run --plan examples/plan.calendar_login_test.yaml --env examples/env.calendar_login_test.yaml --control-room
```

**What this test validates**:
- Authentication security works correctly
- All demo accounts can log in successfully
- Invalid credentials are properly rejected
- Form validation prevents empty submissions
- Session management maintains user state
- Error messages guide users appropriately

#### 2. Calendar UI Navigation Test

**Test File**: `examples/plan.calendar_navigation_test.yaml`  
**Environment**: `examples/env.calendar_navigation_test.yaml`

**Test Coverage**:
- ✅ Calendar interface loading
- ✅ Month navigation (Previous/Next)
- ✅ Calendar grid structure validation
- ✅ Day headers display correctly
- ✅ Event modal interaction
- ✅ User interface elements
- ✅ Responsive behavior

**Run the test**:
```bash
python -m cli.main run --plan examples/plan.calendar_navigation_test.yaml --env examples/env.calendar_navigation_test.yaml --control-room
```

**What this test validates**:
- Calendar loads and displays properly
- Navigation between months works smoothly
- All UI elements are present and functional
- Calendar grid structure is correct
- Interactive elements respond properly

#### 3. Add Events Test  

**Test File**: `examples/plan.calendar_add_events_test.yaml`  
**Environment**: `examples/env.calendar_add_events_test.yaml`

**Test Coverage**:
- ✅ Event creation workflow
- ✅ Form field validation
- ✅ Date and time input handling
- ✅ Special characters in event data
- ✅ Modal open/close functionality
- ✅ Multiple event creation
- ✅ Cancel functionality
- ✅ Early/late time handling

**Run the test**:
```bash
python -m cli.main run --plan examples/plan.calendar_add_events_test.yaml --env examples/env.calendar_add_events_test.yaml --control-room
```

**What this test validates**:
- Users can successfully create events
- Form validation prevents invalid submissions
- Events are saved and persist properly
- Special characters and edge cases work
- Modal interactions behave correctly
- Different time formats are handled

### Method 2: AI-Generated Test Plans (Revolutionary Approach)

The AI WebTester framework can automatically analyze the calendar application and generate comprehensive test plans. This eliminates manual YAML writing and discovers test scenarios you might not think of.

#### 🧠 **AI Test Generation Commands**

**Generate Login Tests**:
```bash
# Let AI analyze the login page and create comprehensive tests
python -m cli.main generate http://127.0.0.1:5000/login --description "Test login functionality with all security scenarios"
```

**Generate Calendar Interface Tests**:
```bash
# Let AI analyze the calendar interface after login
python -m cli.main generate http://127.0.0.1:5000/calendar --description "Test calendar navigation, UI elements, and user interactions"
```

**Generate Complete Application Tests**:
```bash
# Let AI create end-to-end tests covering the entire application
python -m cli.main generate http://127.0.0.1:5000 --description "Create comprehensive test suite covering login, calendar navigation, and event management" --interactive
```

#### **What AI Generation Discovers**:

The AI automatically identifies and tests:
- **Form Elements**: All input fields, buttons, and interactive elements
- **Navigation Flows**: User journey paths through the application
- **Edge Cases**: Boundary conditions and error scenarios
- **Security Aspects**: Authentication vulnerabilities and validation
- **Usability Issues**: User experience problems and accessibility
- **Data Scenarios**: Various input types and validation cases

#### **Example AI-Generated Scenarios**:

When you run AI generation on the calendar app, it creates tests like:
```yaml
# AI automatically discovers these test scenarios:
- "Verify login form accepts valid credentials"
- "Test password field hides input characters"  
- "Validate calendar renders current month correctly"
- "Test event modal closes on outside click"
- "Verify date picker accepts future dates only"
- "Test time input validates 24-hour format"
- "Check calendar navigation updates URL properly"
- "Validate logout clears session data"
```

## Running Tests with Real-time Monitoring

### 🎛️ **Control Room Dashboard**

For the best testing experience, use the Control Room for real-time monitoring:

```bash
# Run any test with live monitoring
python -m cli.main run --plan [your-test-plan].yaml --env [your-environment].yaml --control-room
```

**Then visit**: `http://127.0.0.1:8788`

**Real-time Features**:
- **Live Browser View**: Watch tests execute in real-time
- **Step Progress**: See each test step complete with status
- **Live Logs**: Console output and AI decision making  
- **Screenshots**: Visual evidence of each test action
- **Network Monitoring**: API calls and responses
- **Error Detection**: Immediate failure notification

### 📊 **Test Artifacts & Results**

After each test run, comprehensive evidence is generated:

```bash
# View test results
ls artifacts/[timestamp]/

# Files generated:
# - run.json          # Test execution summary
# - events.json       # Detailed step-by-step log
# - trace.zip         # Complete browser trace
# - video/            # Screen recordings
# - screenshot_*.png  # Visual evidence
```

**Analyzing Results**:
```bash
# View execution summary
cat artifacts/[timestamp]/run.json | jq .

# Open interactive trace viewer
playwright show-trace artifacts/[timestamp]/trace.zip

# Review step-by-step events
cat artifacts/[timestamp]/events.json | jq '.[] | select(.type=="step")'
```

## Complete Testing Workflow

### 🚀 **Step-by-Step Testing Process**

#### 1. **Start the Calendar Application**
```bash
# The calendar app should already be running on port 5000
# If not, start it:
cd calendar_app
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

#### 2. **Manual Testing with Detailed Control**
```bash
# Test login functionality comprehensively
python -m cli.main run --plan examples/plan.calendar_login_test.yaml --env examples/env.calendar_login_test.yaml --control-room

# Test calendar navigation and UI
python -m cli.main run --plan examples/plan.calendar_navigation_test.yaml --env examples/env.calendar_navigation_test.yaml --control-room

# Test event creation and management
python -m cli.main run --plan examples/plan.calendar_add_events_test.yaml --env examples/env.calendar_add_events_test.yaml --control-room
```

#### 3. **AI-Generated Testing for Discovery**
```bash
# Let AI create comprehensive tests automatically
python -m cli.main generate http://127.0.0.1:5000/login --description "Comprehensive login security testing"

# Run the AI-generated tests
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room
```

#### 4. **Review Results**
```bash
# Check test artifacts
ls artifacts/

# Open browser trace for detailed analysis
playwright show-trace artifacts/[latest-timestamp]/trace.zip

# Watch video recordings
ls artifacts/[timestamp]/video/
```

## Test Results Analysis

### 🎯 **What Successful Tests Show**

**Login Test Success Indicators**:
- ✅ All demo accounts authenticate successfully
- ✅ Invalid credentials are rejected with proper error messages
- ✅ Session management works correctly
- ✅ Redirects happen at appropriate times
- ✅ Form validation prevents empty submissions

**Calendar Navigation Success Indicators**:
- ✅ Calendar loads and displays current month
- ✅ Previous/Next month navigation works
- ✅ Day headers display correctly
- ✅ Calendar grid structure is proper
- ✅ Event modal opens and closes correctly

**Event Management Success Indicators**:  
- ✅ Event creation modal opens on day click
- ✅ Form fields accept and validate input
- ✅ Events save successfully to JSON storage
- ✅ Special characters and edge cases handled
- ✅ Multiple events can be created
- ✅ Form validation prevents invalid submissions

### 🐛 **Common Issues and Debugging**

**Login Issues**:
- **Session not persisting**: Check cookie settings in browser
- **Redirects failing**: Verify base URL in environment config
- **Credentials not working**: Confirm user data in `data/users.json`

**Calendar Issues**:
- **Calendar not loading**: Check JavaScript console for errors
- **Navigation not working**: Verify AJAX calls are successful
- **Modal not appearing**: Check CSS and JavaScript loading

**Event Issues**:
- **Events not saving**: Check `data/events.json` file permissions
- **Modal form not working**: Verify form validation JavaScript
- **Date/time issues**: Check date format validation

## Advanced Testing Techniques

### 🔄 **Continuous Testing Integration**

```bash
# Create a test suite runner
cat > run_calendar_tests.sh << 'EOF'
#!/bin/bash

echo "🧪 Starting Calendar App Test Suite..."

# Test 1: Login Functionality
echo "Testing login functionality..."
python -m cli.main run --plan examples/plan.calendar_login_test.yaml --env examples/env.calendar_login_test.yaml

# Test 2: Calendar Navigation  
echo "Testing calendar navigation..."
python -m cli.main run --plan examples/plan.calendar_navigation_test.yaml --env examples/env.calendar_navigation_test.yaml

# Test 3: Event Management
echo "Testing event management..."  
python -m cli.main run --plan examples/plan.calendar_add_events_test.yaml --env examples/env.calendar_add_events_test.yaml

echo "✅ Calendar test suite completed!"
echo "📊 Check artifacts/ directory for detailed results"
EOF

chmod +x run_calendar_tests.sh
./run_calendar_tests.sh
```

### 🎯 **Custom Test Scenarios**

Create your own test scenarios by modifying the YAML files:

```yaml
# Add custom test steps to existing plans
steps:
  - title: "Test your specific scenario"
    action: "click"
    target: "#your-element"
  
  - title: "Verify your expected outcome"
    action: "verify"
    verification:
      text: "Expected result text"
```

### 🧠 **AI Testing for Edge Cases**

```bash
# Generate tests for specific edge cases
python -m cli.main generate http://127.0.0.1:5000/calendar --description "Test calendar with different timezones and date formats"

python -m cli.main generate http://127.0.0.1:5000/login --description "Security testing for SQL injection and XSS vulnerabilities"

python -m cli.main generate http://127.0.0.1:5000 --description "Accessibility testing for screen readers and keyboard navigation"
```

## Benefits of Each Testing Approach

### 📋 **Manual YAML Tests (High Control)**

**Advantages**:
- ✅ **Precise Control**: Exact test steps and validations
- ✅ **Reproducible**: Same tests run identically every time
- ✅ **Customizable**: Modify any aspect of the test
- ✅ **Comprehensive**: Cover specific business logic
- ✅ **Regression Testing**: Detect breaking changes

**Best For**:
- Critical business functionality
- Regression testing after code changes
- Compliance and audit requirements
- Complex multi-step workflows

### 🧠 **AI-Generated Tests (Discovery & Speed)**

**Advantages**:
- ✅ **Speed**: Generate comprehensive tests in seconds
- ✅ **Discovery**: Find test scenarios you didn't consider
- ✅ **Coverage**: Automatic exploration of the application
- ✅ **Evolution**: Adapt to application changes automatically
- ✅ **Learning**: Discover usability and accessibility issues

**Best For**:
- Initial application testing
- Exploratory testing
- Finding edge cases and bugs
- Testing unfamiliar applications
- Continuous discovery testing

## Conclusion

The AI WebTester framework provides two powerful approaches to testing the calendar application:

1. **Manual YAML Tests**: Give you precise control and comprehensive coverage of specific scenarios
2. **AI Generation**: Provides rapid test creation and discovers scenarios you might miss

**Recommendation**: 
- Start with **AI generation** to quickly discover what to test
- Create **manual YAML tests** for critical business flows
- Use **Control Room monitoring** for real-time visibility
- Analyze **artifacts** for comprehensive test evidence

Both approaches ensure your calendar application is thoroughly tested and ready for production use!