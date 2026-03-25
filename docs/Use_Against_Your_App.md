# Use AI WebTester Against Your App

## What This Guide Is For

This guide is for the simple case:

- you have a web app
- you want AI WebTester to test it
- you are **not** using CI/CD yet
- you want the easiest path

You can use AI WebTester on your own machine first, then later move it into GitHub Actions, Jenkins, or another pipeline if you want.

## What AI WebTester Can Do

AI WebTester can help you in 3 main ways:

1. **Generate a test plan for one page**
2. **Run a saved test plan**
3. **Explore your app automatically and test many pages**

If you are new, start with **Generate** or **Explore**.

## Before You Start

You need:

- Python 3.11 or newer
- your app running locally or available at a URL
- terminal access

If you want AI-assisted generation, you also need:

- an OpenAI API key

## Step 1: Install AI WebTester

From the project folder, run:

```bash
pip install -e ".[dev]"
playwright install --with-deps chromium
```

This installs:

- the Python dependencies
- the Chromium browser used by the framework

## Step 2: Add Your OpenAI API Key (Optional but Recommended)

If you want the framework to generate smarter test plans, set your API key.

### Linux / macOS

```bash
export OPENAI_API_KEY="your-key-here"
```

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="your-key-here"
```

If you do **not** set the key, some flows can still work using fallback logic, but AI-generated plans will be more limited.

## Step 3: Pick The Easiest Starting Point

### Option A: Test One Page With AI Generation

This is the best first step for most people.

Example:

```bash
python -m cli.main generate https://your-app.com/login --description "Test the login page"
```

What this does:

- opens the page
- looks at forms, buttons, and inputs
- creates a test plan file
- creates an environment file

After that, run the generated plan:

```bash
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room
```

What `--control-room` does:

- starts a local dashboard
- lets you watch the test while it runs

## Option B: Explore More Of Your App Automatically

If your app has login and several pages, try `explore`.

Example:

```bash
python -m cli.main explore https://your-app.com/login --username "myuser" --password "mypassword" --control-room
```

What this does:

- logs in
- crawls the app
- finds forms and important pages
- creates tests
- runs them
- saves artifacts

This is a good choice if you want a quick first pass over the app without writing YAML manually.

## Option C: Run A Plan You Already Have

If you already have a YAML plan, run it directly:

```bash
python -m cli.main run --plan your-plan.yaml --env your-env.yaml --control-room
```

## Common Real-World Scenarios

### My app is on localhost

Example:

```bash
python -m cli.main generate http://127.0.0.1:3000/login --description "Test local login"
```

### My app requires login

Use `explore` with username and password:

```bash
python -m cli.main explore https://your-app.com/login --username "testuser" --password "testpass"
```

### My app already has a valid session cookie

Use the cookie instead of login credentials:

```bash
python -m cli.main explore https://your-app.com/dashboard --cookie-name "session" --cookie-value "your-cookie-value"
```

### I only want to watch generation, not execution

Use:

```bash
python -m cli.main generate https://your-app.com --headful
```

### I want to explore the app but not run tests yet

Use:

```bash
python -m cli.main explore https://your-app.com/login --username "user" --password "pass" --crawl-only
```

This is useful if you first want to understand what the framework discovered.

## Where The Results Go

AI WebTester saves results into the `artifacts/` folder.

You will usually find:

- `run.json`
- `events.json`
- `trace.zip`
- screenshots
- video files

These files help you understand:

- what the test did
- what passed
- what failed
- what the browser looked like

## The Simplest Good Workflow

If you are unsure what to do, use this workflow:

1. Start your app
2. Run `generate` on the most important page
3. Run the generated plan with `--control-room`
4. Look at `artifacts/`
5. If that works, try `explore`

Example:

```bash
python -m cli.main generate https://your-app.com/login --description "Test login"
python -m cli.main run --plan examples/plan.generated_*.yaml --env examples/env.generated_*.yaml --control-room
```

## If Your App Has Special Logic

Some apps need custom help, for example:

- unusual selectors
- multi-step login
- app-specific setup
- custom buttons or flows

In that case, you can use **hooks**.

Hooks let your app teach the framework extra rules.

Example:

```bash
python -m cli.main generate https://your-app.com/login --hooks ./app_test_hooks.py
```

Read [hooks.md](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/hooks.md) if you need that.

If you are new, do **not** start with hooks. First try the basic flow.

## Troubleshooting

### Command fails because Playwright is missing

Run:

```bash
playwright install --with-deps chromium
```

### AI generation is weak or unavailable

Check that your API key is set:

### Linux / macOS

```bash
echo $OPENAI_API_KEY
```

### Windows PowerShell

```powershell
echo $env:OPENAI_API_KEY
```

### Login does not work

Try:

- checking the login URL
- using a test user
- using a session cookie instead
- trying `generate` on the login page first

### The generated plan is close, but not perfect

That is normal.

Start by:

- opening the generated YAML
- adjusting selectors or verification steps
- running it again

Later, if needed, add hooks.

## Best Advice For Beginners

- Start small
- Test one page first
- Use `--control-room`
- Check the `artifacts/` folder
- Do not try to automate the whole app on the first run

## Related Docs

- [hooks.md](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/hooks.md)
- [Automated-Testing.md](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/Automated-Testing.md)
- [GitHub Actions CI/CD doc](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/GitHub_Actions/CI_CD_Pipeline.md)
- [Jenkins guide](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/jenkins/Jenkins.md)
