# Calendar Application - Complete Guide

## Overview

This is a comprehensive Python-based calendar application built with FastAPI, featuring user authentication, event management, and a modern web interface. The application demonstrates full-stack development with backend APIs, frontend JavaScript, and JSON-based data storage.

## Application Architecture

### Backend Components
- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Session-based Authentication**: In-memory session storage with secure cookies
- **JSON Data Storage**: File-based storage for users and events
- **RESTful API**: Complete CRUD operations for event management
- **Jinja2 Templates**: Server-side HTML template rendering

### Frontend Components
- **Modern HTML5**: Semantic markup with accessibility features
- **CSS3 Styling**: Responsive design with CSS Grid and Flexbox
- **Vanilla JavaScript**: Interactive calendar with modal forms
- **AJAX Communication**: Asynchronous API calls for seamless user experience

### Data Storage
- **users.json**: User accounts and authentication data
- **events.json**: Calendar events with timestamps and user associations

## Features

### 🔐 Authentication System
- **Secure Login**: Username/password authentication with session management
- **Demo Accounts**: Three pre-configured test accounts
- **Session Persistence**: Maintains user state across requests
- **Automatic Redirects**: Seamless navigation between login and calendar

### 📅 Calendar Interface
- **Monthly View**: Interactive grid showing current month
- **Navigation**: Previous/Next month browsing
- **Today Highlighting**: Current date visual indication
- **Responsive Design**: Works on desktop and mobile devices

### 📝 Event Management
- **Create Events**: Click any date to add new events
- **Edit Events**: Click existing events to modify details
- **Delete Events**: Remove events with confirmation
- **Event Details**: Title, description, date, time, and notes
- **User Isolation**: Each user sees only their own events

### 🎯 Real-time Features
- **Live Updates**: Events appear immediately after creation
- **Modal Forms**: Smooth popup interfaces for event creation
- **Form Validation**: Client-side and server-side input validation
- **Error Handling**: Graceful error messages and recovery

## Prerequisites

### System Requirements
- **Python 3.11+**: Modern Python version with async support
- **Web Browser**: Chrome, Firefox, Safari, or Edge
- **Terminal Access**: Command line for running the application

### Dependencies
```bash
# Core framework
fastapi>=0.104.1
uvicorn[standard]>=0.24.0

# Templating and static files
jinja2>=3.1.2
python-multipart

# Data handling
pydantic>=2.0.0

# Development tools (optional)
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## Installation and Setup

### Step 1: Install Dependencies
```bash
# Navigate to calendar app directory
cd calendar_app

# Install required packages
pip install fastapi uvicorn jinja2 python-multipart pydantic

# Optional: Install development dependencies
pip install pytest pytest-asyncio
```

### Step 2: Verify File Structure
```
calendar_app/
├── main.py                 # FastAPI application
├── templates/              # HTML templates
│   ├── login.html         # Login page
│   └── calendar.html      # Calendar interface
├── static/                # Static assets
│   ├── style.css          # Application styling
│   └── script.js          # Frontend JavaScript
├── data/                  # Data storage
│   ├── users.json         # User accounts
│   └── events.json        # Calendar events
└── TestApp.md            # This documentation
```

### Step 3: Start the Application
```bash
# Method 1: Using Python module
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Method 2: Direct execution
python main.py

# Method 3: Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Step 4: Access the Application
- **Primary URL**: http://127.0.0.1:5000
- **Login Page**: http://127.0.0.1:5000/login
- **Calendar Page**: http://127.0.0.1:5000/calendar (requires login)

## User Guide

### Demo Accounts
The application comes with three pre-configured accounts for testing:

| Username | Password  | Full Name     | Role  |
|----------|-----------|---------------|-------|
| admin    | admin123  | Administrator | Admin |
| john     | password  | John Doe      | User  |
| alice    | alice123  | Alice Smith   | User  |

### Getting Started

#### 1. Login Process
1. Navigate to http://127.0.0.1:5000
2. You'll be automatically redirected to the login page
3. Enter username and password from demo accounts above
4. Click "Login" button
5. Successful login redirects to the calendar interface

#### 2. Calendar Navigation
- **Current Month**: Displays the current month and year
- **Previous Month**: Click "< Previous" to navigate backward
- **Next Month**: Click "Next >" to navigate forward
- **Today**: Current date is highlighted in a different color
- **Other Month Days**: Grayed out dates from adjacent months

#### 3. Creating Events
1. Click on any calendar date
2. Event creation modal opens
3. Fill in required fields:
   - **Title**: Event name (required)
   - **Description**: Additional details (optional)
   - **Date**: Auto-filled with selected date
   - **Time**: Event time in 24-hour format
4. Click "Save Event" to create
5. Event appears on the calendar and in upcoming events list

#### 4. Managing Events
- **View Events**: Click on existing event titles to view details
- **Edit Events**: Click event to open edit modal
- **Delete Events**: Use delete button in edit modal
- **Upcoming Events**: View chronological list below calendar

#### 5. Logout
- Click "Logout" button in top-right corner
- Session is cleared and redirected to login page

## API Documentation

### Authentication Endpoints

#### POST /login
**Purpose**: Authenticate user and create session
**Body**: Form data with `username` and `password`
**Response**: Redirect to calendar or error message
**Example**:
```bash
curl -d "username=admin&password=admin123" -X POST http://127.0.0.1:5000/login
```

#### GET /logout
**Purpose**: Terminate user session
**Response**: Redirect to login page
**Example**:
```bash
curl http://127.0.0.1:5000/logout
```

### Event Management API

#### GET /api/events
**Purpose**: Get all events for authenticated user
**Headers**: Requires valid session cookie
**Response**: JSON array of user events
**Example**:
```bash
curl -b cookies.txt http://127.0.0.1:5000/api/events
```

#### POST /api/events
**Purpose**: Create new event
**Body**: JSON with title, description, date, time
**Response**: Created event with ID
**Example**:
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"title":"Meeting","description":"Team meeting","date":"2025-09-15","time":"10:00"}' \
     -b cookies.txt http://127.0.0.1:5000/api/events
```

#### PUT /api/events/{id}
**Purpose**: Update existing event
**Body**: JSON with updated event data
**Response**: Updated event object
**Example**:
```bash
curl -X PUT -H "Content-Type: application/json" \
     -d '{"title":"Updated Meeting","description":"Updated description","date":"2025-09-15","time":"11:00"}' \
     -b cookies.txt http://127.0.0.1:5000/api/events/1
```

#### DELETE /api/events/{id}
**Purpose**: Delete event by ID
**Response**: Deletion confirmation message
**Example**:
```bash
curl -X DELETE -b cookies.txt http://127.0.0.1:5000/api/events/1
```

### User Information API

#### GET /api/user
**Purpose**: Get current user information
**Response**: User profile data (no password)
**Example**:
```bash
curl -b cookies.txt http://127.0.0.1:5000/api/user
```

## Database Schema

### Users Table (users.json)
```json
[
  {
    "id": 1,
    "username": "admin",
    "password": "admin123",
    "email": "admin@example.com",
    "full_name": "Administrator"
  }
]
```

**Fields**:
- `id`: Unique user identifier
- `username`: Login username (unique)
- `password`: Plain text password (demo only)
- `email`: User email address
- `full_name`: Display name

### Events Table (events.json)
```json
[
  {
    "id": 1,
    "user_id": 1,
    "title": "Team Meeting",
    "description": "Weekly team standup",
    "date": "2025-09-15",
    "time": "10:00",
    "created_at": "2025-09-11T12:00:00"
  }
]
```

**Fields**:
- `id`: Unique event identifier
- `user_id`: Foreign key to users table
- `title`: Event title/name
- `description`: Optional event details
- `date`: Event date (YYYY-MM-DD format)
- `time`: Event time (HH:MM format)
- `created_at`: Timestamp of creation

## Test Case Creation

### Manual Test Cases

#### Login Functionality Tests

**Test Case 1: Valid Login**
```yaml
Test ID: LOGIN_001
Title: Successful login with valid credentials
Steps:
  1. Navigate to http://127.0.0.1:5000
  2. Enter username: "admin"
  3. Enter password: "admin123"
  4. Click Login button
Expected Result: Redirect to calendar page, show "Welcome, Administrator"
```

**Test Case 2: Invalid Login**
```yaml
Test ID: LOGIN_002
Title: Login failure with invalid credentials
Steps:
  1. Navigate to http://127.0.0.1:5000/login
  2. Enter username: "admin"
  3. Enter password: "wrongpassword"
  4. Click Login button
Expected Result: Stay on login page, show error message
```

**Test Case 3: Empty Form**
```yaml
Test ID: LOGIN_003
Title: Form validation with empty fields
Steps:
  1. Navigate to login page
  2. Leave username empty
  3. Leave password empty
  4. Click Login button
Expected Result: HTML5 validation prevents submission
```

#### Calendar Navigation Tests

**Test Case 4: Month Navigation**
```yaml
Test ID: NAV_001
Title: Navigate to next month
Steps:
  1. Login successfully
  2. Note current month displayed
  3. Click "Next >" button
  4. Verify month changed
Expected Result: Calendar shows next month, month title updates
```

**Test Case 5: Calendar Grid Display**
```yaml
Test ID: NAV_002
Title: Calendar grid structure
Steps:
  1. Login successfully
  2. Verify calendar grid is visible
  3. Check day headers (Sun-Sat)
  4. Verify dates are properly laid out
Expected Result: 7-column grid with proper day headers and dates
```

#### Event Management Tests

**Test Case 6: Create Event**
```yaml
Test ID: EVENT_001
Title: Create new event successfully
Steps:
  1. Login successfully
  2. Click on any calendar date
  3. Fill title: "Test Meeting"
  4. Fill description: "Test description"
  5. Set date and time
  6. Click Save Event
Expected Result: Modal closes, event appears on calendar
```

**Test Case 7: Event Validation**
```yaml
Test ID: EVENT_002
Title: Required field validation
Steps:
  1. Login successfully
  2. Click on calendar date
  3. Leave title field empty
  4. Fill other fields
  5. Click Save Event
Expected Result: Validation error, form not submitted
```

**Test Case 8: Edit Event**
```yaml
Test ID: EVENT_003
Title: Edit existing event
Steps:
  1. Create an event first
  2. Click on the created event
  3. Modify the title
  4. Click Save Event
Expected Result: Event updated with new information
```

### Automated Test Cases

#### YAML Test Plans

The application includes comprehensive YAML test plans for the AI WebTester framework:

- `../examples/plan.calendar_login_test.yaml`: Login functionality testing
- `../examples/plan.calendar_navigation_test.yaml`: UI navigation testing  
- `../examples/plan.calendar_add_events_test.yaml`: Event management testing

#### Creating Custom Test Plans

**Basic Test Plan Structure**:
```yaml
name: "My Custom Test"
description: "Description of what this test validates"

steps:
  - title: "Navigate to application"
    action: "navigate"
    target: "http://127.0.0.1:5000"
  
  - title: "Fill login form"
    action: "fill"
    target: "#username"
    data:
      value: "admin"
  
  - title: "Verify success"
    action: "verify"
    verification:
      text: "Welcome"
```

**Common Test Actions**:
- `navigate`: Go to URL
- `fill`: Enter text in form field
- `click`: Click button or element
- `submit`: Submit form
- `verify`: Check for text or element
- `wait`: Pause for specified seconds

**CSS Selectors Reference**:
- Login form: `#username`, `#password`, `.login-btn`
- Calendar: `#calendarGrid`, `#currentMonth`, `#prevMonth`, `#nextMonth`
- Events: `#eventModal`, `#eventTitle`, `#eventDate`, `#eventTime`
- Navigation: `.calendar-day`, `.logout-btn`

#### Environment Configuration

**Environment File Structure**:
```yaml
name: "Test Environment"
description: "Configuration for test execution"

target:
  base_url: "http://127.0.0.1:5000"
  timeout: 15000

credentials:
  username: "admin"
  password: "admin123"

settings:
  headful: true
  slow_mo: 500
  video: true
  screenshots: true

browser_options:
  viewport:
    width: 1280
    height: 720
```

## Test Execution

### Prerequisites for Testing

#### Install AI WebTester Framework
```bash
# From the parent directory (not calendar_app)
cd ..

# Ensure AI WebTester dependencies are installed
pip install typer playwright openai beautifulsoup4 aiofiles

# Install browser automation
playwright install
```

#### Set Environment Variables
```bash
# Required for AI-powered test generation
export OPENAI_API_KEY="your-api-key-here"
```

### Running Automated Tests

#### Method 1: Use Existing Test Plans

**Login Functionality Test**:
```bash
# From parent directory
python -m cli.main run \
  --plan examples/plan.calendar_login_test.yaml \
  --env examples/env.calendar_login_test.yaml \
  --control-room
```

**Calendar Navigation Test**:
```bash
python -m cli.main run \
  --plan examples/plan.calendar_navigation_test.yaml \
  --env examples/env.calendar_navigation_test.yaml \
  --control-room
```

**Event Management Test**:
```bash
python -m cli.main run \
  --plan examples/plan.calendar_add_events_test.yaml \
  --env examples/env.calendar_add_events_test.yaml \
  --control-room
```

#### Method 2: Generate AI Tests

**Generate Tests for Login Page**:
```bash
python -m cli.main generate http://127.0.0.1:5000/login \
  --description "Comprehensive login security and functionality testing"
```

**Generate Tests for Calendar Interface**:
```bash
# First login manually, then generate tests for logged-in state
python -m cli.main generate http://127.0.0.1:5000/calendar \
  --description "Calendar navigation and event management testing"
```

**Run Generated Tests**:
```bash
python -m cli.main run \
  --plan examples/plan.generated_*.yaml \
  --env examples/env.generated_*.yaml \
  --control-room
```

### Test Execution Options

#### Command Line Parameters
- `--plan`: Path to YAML test plan file
- `--env`: Path to environment configuration file
- `--control-room`: Enable real-time monitoring dashboard
- `--headful`: Show browser during test execution
- `--artifacts-dir`: Directory for test results

#### Real-time Monitoring
When using `--control-room`, visit http://127.0.0.1:8788 to see:
- Live browser screenshots
- Test step progress
- Console logs and errors
- Network requests
- Detailed execution timeline

#### Test Artifacts
After test execution, check the `artifacts/[timestamp]/` directory for:
- `run.json`: Test execution summary
- `events.json`: Detailed step-by-step log
- `trace.zip`: Complete browser execution trace
- `video/`: Screen recordings of test execution
- `screenshot_*.png`: Visual evidence at key points

### Analyzing Test Results

#### Success Indicators
- All test steps complete successfully
- Expected elements are found and verified
- Form submissions work correctly
- Navigation functions properly
- Events are created and persist

#### Common Failure Scenarios
- **Authentication failures**: Check credentials and session handling
- **Element not found**: Verify CSS selectors and page load timing
- **Timeout errors**: Increase wait times or check performance
- **Modal issues**: Ensure proper modal state verification

#### Debugging Failed Tests
1. **Review Video**: Watch screen recording to see what happened
2. **Check Screenshots**: Examine visual state at failure point
3. **Open Trace**: Use `playwright show-trace artifacts/*/trace.zip`
4. **Review Logs**: Check console output and network requests
5. **Manual Verification**: Try steps manually in browser

### Continuous Testing

#### Test Suite Script
```bash
#!/bin/bash
# File: run_all_tests.sh

echo "🧪 Starting Calendar App Test Suite"

# Ensure app is running
echo "📋 Checking application status..."
curl -f http://127.0.0.1:5000/login >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Calendar app not running. Please start it first."
    exit 1
fi

# Run login tests
echo "🔐 Testing login functionality..."
python -m cli.main run \
  --plan examples/plan.calendar_login_test.yaml \
  --env examples/env.calendar_login_test.yaml

# Run navigation tests  
echo "📅 Testing calendar navigation..."
python -m cli.main run \
  --plan examples/plan.calendar_navigation_test.yaml \
  --env examples/env.calendar_navigation_test.yaml

# Run event tests
echo "📝 Testing event management..."
python -m cli.main run \
  --plan examples/plan.calendar_add_events_test.yaml \
  --env examples/env.calendar_add_events_test.yaml

echo "✅ Test suite completed!"
echo "📊 Check artifacts/ directory for detailed results"
```

#### Usage:
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

## Troubleshooting

### Common Issues

#### Application Won't Start
- **Check Python Version**: Ensure Python 3.11+
- **Install Dependencies**: Run `pip install fastapi uvicorn`
- **Port Conflicts**: Kill processes using port 5000
- **File Permissions**: Ensure data files are writable

#### Authentication Problems
- **Session Issues**: Restart application to clear sessions
- **Cookie Problems**: Clear browser cookies
- **Credential Errors**: Verify demo account credentials

#### Calendar Display Issues
- **JavaScript Errors**: Check browser console for errors
- **CSS Loading**: Verify static files are served correctly
- **Date Issues**: Check system date and timezone settings

#### Event Management Problems
- **Modal Not Opening**: Check JavaScript console for errors
- **Events Not Saving**: Verify write permissions on data/events.json
- **Events Not Loading**: Check API endpoint responses

#### Testing Issues
- **Browser Dependencies**: Run `playwright install`
- **Selector Failures**: Update CSS selectors if UI changed
- **Timeout Errors**: Increase wait times in test plans
- **Authentication in Tests**: Ensure login steps work correctly

### Performance Optimization

#### Application Performance
- Use production ASGI server (gunicorn + uvicorn)
- Implement proper database (PostgreSQL, MySQL)
- Add caching for static assets
- Optimize JavaScript bundle size

#### Test Performance
- Run tests in headless mode for speed
- Use parallel test execution
- Optimize wait times in test plans
- Cache browser installations

### Security Considerations

#### Production Deployment
- **Password Hashing**: Implement bcrypt or similar
- **HTTPS**: Use SSL/TLS encryption
- **Session Security**: Use Redis with encrypted sessions
- **Input Validation**: Add server-side validation
- **CSRF Protection**: Implement CSRF tokens
- **Rate Limiting**: Add login attempt limits

#### Demo Security
- This application uses plain text passwords
- Sessions are stored in memory
- No rate limiting or CSRF protection
- Suitable for testing and demonstration only

## Conclusion

This Calendar Application provides a complete example of modern web application development with comprehensive testing capabilities. It demonstrates:

- **Full-stack Architecture**: Frontend, backend, and data layers
- **User Authentication**: Session-based security
- **Interactive UI**: Modern JavaScript and CSS
- **API Design**: RESTful endpoints with proper HTTP methods
- **Test Automation**: Both manual and AI-generated test cases
- **Real-time Monitoring**: Live test execution visibility

The application serves as an excellent foundation for learning web development concepts, testing methodologies, and automation frameworks. It can be extended with additional features like recurring events, email notifications, user registration, and advanced calendar views.

For questions or issues, review the troubleshooting section or examine the test artifacts for detailed execution information.