# Testing Replit Applications with AI WebTester Framework

## Overview

This guide shows you how to use the AI WebTester Framework to comprehensively test your applications running in the Replit environment, including GRC tools, web applications, and any other browser-accessible software.

## Getting Your Application URL

### Method 1: Environment Variables
In your current Repl, you can access your domain:
```bash
echo $REPLIT_DOMAINS
```

### Method 2: From Other Repls
- Navigate to your target application's Repl
- Copy the URL from the webview panel
- URLs typically follow the pattern: `https://YOUR-REPL-ID.replit.dev` or `https://YOUR-REPL-ID.replit.app`

### Method 3: Using REPL_ID
```bash
echo $REPL_ID
# Use this ID to construct: https://REPL-ID.replit.dev
```

## Configuration Setup

### Step 1: Update Test Configuration
Replace the placeholder URLs in the test files with your actual application URL:

```bash
# For GRC tools or similar applications
sed -i 's/YOUR-GRC-REPL-URL.replit.dev/your-actual-app-url.replit.dev/g' examples/plan.grc_tool_test.yaml
sed -i 's/YOUR-GRC-REPL-URL.replit.dev/your-actual-app-url.replit.dev/g' examples/env.grc_tool.yaml
```

### Step 2: Customize Test Credentials (Optional)
Edit `examples/env.grc_tool.yaml` to include your application's specific test data:

```yaml
grc_tool:
  base_url: "https://your-app.replit.dev"
  test_credentials:
    username: "your-test-username"
    password: "your-test-password"
  
  test_data:
    # Customize based on your application
    department: "IT Security"
    category: "Operational Risk"
    framework: "ISO 27001"
```

## Testing Methods

### Option 1: Basic Automated Testing

**Command:**
```bash
python -m cli.main run --plan examples/plan.grc_tool_test.yaml --env examples/env.grc_tool.yaml
```

**What it does:**
- Runs automated browser tests against your application
- Captures screenshots and videos
- Generates detailed test reports
- Records performance metrics

### Option 2: Real-Time Control Room Monitoring ⭐ (Recommended)

**Command:**
```bash
python -m cli.main run --plan examples/plan.grc_tool_test.yaml --env examples/env.grc_tool.yaml --control-room
```

**Benefits:**
- Real-time test monitoring dashboard
- Live WebSocket updates
- Interactive test control (approve/reject/stop)
- Live status and progress tracking

**Access:** Open the provided Control Room URL (typically `http://localhost:8080`) in your browser

### Option 3: AI-Powered Test Generation 🤖

**Command:**
```bash
python -m cli.main generate --url https://your-app.replit.dev --output-dir custom-tests
```

**Features:**
- Automatically analyzes your application
- Generates comprehensive test plans
- Discovers forms, buttons, and interactive elements
- Creates custom test scenarios

## Test Coverage

### Authentication & Access
- ✅ Homepage loading verification
- ✅ Login form detection and testing
- ✅ Authentication flow validation
- ✅ Session management testing

### Application-Specific Features
For GRC tools, the framework tests:
- ✅ **Risk Management** - Risk assessment interfaces
- ✅ **Compliance** - Audit controls and policy management
- ✅ **Governance** - Board oversight and framework features

### User Interface Testing
- ✅ Navigation menu functionality
- ✅ Form interactions and submissions
- ✅ Data table and grid interfaces
- ✅ Button and link responsiveness
- ✅ Page transitions and redirects

### Performance & Reliability
- ✅ Page load times
- ✅ Network request monitoring
- ✅ Console error detection
- ✅ Memory usage tracking

## Security & Compliance Features

### Automatic Data Redaction
The framework automatically redacts sensitive information from all test artifacts:

- **Email addresses** → `[REDACTED_EMAIL]`
- **Passwords** → `[REDACTED_PASSWORD]`  
- **API keys** → `[REDACTED_API_KEY]`
- **Tokens** → `[REDACTED_TOKEN]`
- **Credit card numbers** → `[REDACTED_CREDIT_CARD]`
- **Social Security numbers** → `[REDACTED_SSN]`

### Compliance-Ready Reports
- Audit-trail documentation
- Secure artifact storage
- Privacy-compliant test data handling
- Enterprise-grade security standards

## Test Outputs

After running tests, you'll receive:

### Visual Evidence
- **Video recordings** of entire test sessions
- **Screenshots** at each test step
- **Before/after comparisons**

### Technical Reports
- **Console logs** (with sensitive data redacted)
- **Network activity logs**
- **Performance metrics** and timing data
- **Error reports** with stack traces

### Test Documentation
- **Step-by-step execution logs**
- **Pass/fail status** for each test case
- **Detailed error descriptions**
- **Recommendations** for improvements

## Customizing Tests for Your Application

### Creating Custom Test Plans

1. **Copy the base template:**
```bash
cp examples/plan.grc_tool_test.yaml examples/plan.my_app_test.yaml
```

2. **Modify test steps** for your specific application:
```yaml
steps:
  - title: "Navigate to my app feature"
    action: "navigate"
    target: "https://my-app.replit.dev/specific-page"
  
  - title: "Test my custom functionality"
    action: "click"
    target: ".my-custom-button"
```

### Application-Specific Configurations

#### For E-commerce Applications
```yaml
test_data:
  product_name: "Test Product"
  price: "29.99"
  category: "Electronics"
```

#### For CRM Systems
```yaml
test_data:
  customer_name: "John Doe"
  company: "Test Company"
  email: "test@example.com"
```

#### For Project Management Tools
```yaml
test_data:
  project_name: "Test Project"
  task_title: "Sample Task"
  due_date: "2024-12-31"
```

## Troubleshooting

### Common Issues

**Issue:** "Target element not found"
**Solution:** Update CSS selectors in your test plan to match your application's HTML structure

**Issue:** "Page load timeout"
**Solution:** Increase timeout values in the environment configuration:
```yaml
timeout:
  default: 15000
  page_load: 45000
```

**Issue:** "Authentication failed"
**Solution:** Verify test credentials in `env.yaml` and ensure they match your application's requirements

### Getting Help

1. **Check test logs** for detailed error messages
2. **Review screenshots** to see what the browser captured
3. **Examine console logs** for JavaScript errors
4. **Use Control Room** for real-time debugging

## Advanced Features

### Multi-Environment Testing
Test the same application across different environments:

```bash
# Test staging environment
python -m cli.main run --plan examples/plan.my_app_test.yaml --env examples/env.staging.yaml

# Test production environment  
python -m cli.main run --plan examples/plan.my_app_test.yaml --env examples/env.production.yaml
```

### Batch Testing
Run multiple test suites:

```bash
# Test multiple applications
for app in grc-tool crm-system ecommerce-site; do
  python -m cli.main run --plan examples/plan.$app.yaml --env examples/env.$app.yaml
done
```

### Continuous Integration
Integrate with your CI/CD pipeline:

```yaml
# In your .github/workflows/test.yml
- name: Run AI WebTester
  run: |
    python -m cli.main run --plan examples/plan.my_app.yaml --env examples/env.ci.yaml
    
- name: Upload test artifacts
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: artifacts/
```

## Best Practices

### Test Design
- **Start simple** with basic navigation tests
- **Build incrementally** adding more complex scenarios
- **Use descriptive titles** for each test step
- **Include verification steps** to confirm expected outcomes

### Security
- **Never commit real credentials** to test files
- **Use environment variables** for sensitive configuration
- **Review test artifacts** before sharing to ensure no sensitive data leaked

### Maintenance
- **Update test plans** when your application changes
- **Review and clean up** test artifacts regularly
- **Monitor test performance** and optimize slow tests

---

## Quick Start Checklist

- [ ] Get your Replit application URL
- [ ] Update test configuration files with your URL
- [ ] Choose testing method (Basic/Control Room/AI-generated)
- [ ] Run your first test
- [ ] Review test results and artifacts
- [ ] Customize test plans for your specific needs
- [ ] Set up regular testing schedule

**Ready to start testing your Replit applications with enterprise-grade automation and security!**