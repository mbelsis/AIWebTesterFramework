# Hooks

## Overview

AI WebTester supports **framework hooks** that let an application team shape generated tests and extend step execution without forking the framework.

These hooks are useful when your application has:
- domain-specific workflows
- stable selectors the framework would not infer on its own
- seeded login or setup flows
- generated plans that need cleanup or normalization before execution
- custom actions that are specific to your product

## Why Hooks Exist

Out of the box, AI WebTester can:
- analyze pages
- infer selectors
- generate test plans
- execute standard actions such as `navigate`, `fill`, `click`, `submit`, `wait`, and `verify`

That is good enough for many apps, but real systems often need application-specific knowledge.

Hooks let your app provide that knowledge in a controlled way.

## Supported Hooks

### `after_analyze(page_analysis, context)`

Runs after page analysis is complete.

Use it to:
- add application metadata
- inject domain hints into page analysis
- normalize noisy HTML-derived data before plan generation

Return:
- updated `page_analysis` dict

### `before_generate(page_analysis, context)`

Runs before a test plan is generated.

Use it to:
- enrich the page analysis with app-specific hints
- mark important elements
- add generation guidance based on page type or route

Return:
- updated `page_analysis` dict

### `before_ai_prompt(prompt, context)`

Runs before the explorer sends an AI prompt for per-page test generation.

Use it to:
- add domain instructions
- require use of `data-testid`
- prioritize specific user journeys

Return:
- updated prompt string

### `after_generate(plan, context)`

Runs after a plan is generated, whether it came from AI generation or fallback generation.

Use it to:
- rewrite brittle selectors
- insert setup or teardown steps
- add stronger verification
- normalize plan naming

Return:
- updated `plan` dict

### `after_generate_env(env_config, context)`

Runs after the environment file is generated.

Use it to:
- inject test credentials
- turn headful mode off
- add app-specific test data
- override base URLs or timeouts

Return:
- updated `env_config` dict

### `before_step(step, context)`

Runs before a test step executes.

Use it to:
- rewrite custom actions into built-in actions
- swap selectors
- inject dynamic values

Return:
- updated `step` dict

### `execute_step(step, executor, context)`

Runs before the executor falls back to built-in actions.

Use it to implement a **custom action** without modifying the framework.

If this hook returns a non-`None` value, the framework treats the step as handled by the hook and skips the built-in action dispatcher.

Use it to:
- log in with a seeded session
- create domain objects through hidden UI flows
- run application-specific setup actions

Return:
- any non-`None` value to mark the step as handled

### `after_step(result, context)`

Runs after a step completes successfully.

Use it to:
- collect custom telemetry
- attach extra metadata
- track action coverage

Return:
- updated `result` dict, if needed

### `on_step_failure(step, error, context)`

Runs when a step fails.

Use it to:
- add app-specific diagnostics
- trigger extra logging
- capture business-context details for failed flows

Return:
- nothing required

## Context Payloads

The `context` dict varies by hook, but typically includes fields like:
- `run_id`
- `base_url`
- `step_index`
- `resolved_target`
- `test_description`
- `generation_source`
- `page`
- `page_analysis`

Hooks should treat missing keys as normal and code defensively.

## How To Integrate Hooks In Your App

Create a Python file in your application repository, for example `app_test_hooks.py`:

```python
class AppHook:
    def after_generate(self, plan, context):
        plan["name"] = f"MyApp - {plan.get('name', 'Generated Plan')}"
        plan["steps"].append(
            {
                "title": "Verify dashboard shell",
                "action": "verify",
                "verification": {"selector": "[data-testid='app-shell']"},
            }
        )
        return plan

    def before_step(self, step, context):
        if step.get("target") == "#submit":
            step["target"] = "[data-testid='primary-submit']"
        return step

    async def execute_step(self, step, executor, context):
        if step.get("action") != "seed_login":
            return None

        await executor._navigate("/login")
        await executor._fill("[name='username']", "qa-user")
        await executor._fill("[name='password']", "TestPass123!")
        await executor._submit("[data-testid='login-submit']")
        return {"handled": True}


HOOKS = [AppHook()]
```

Then pass it to the framework:

### Generate

```bash
python -m cli.main generate https://app.example.com/login \
  --hooks ./app_test_hooks.py
```

### Explore

```bash
python -m cli.main explore https://app.example.com/login \
  --username qa-user \
  --password TestPass123! \
  --hooks ./app_test_hooks.py
```

### Run

```bash
python -m cli.main run \
  --plan examples/plan.generated_login.yaml \
  --env examples/env.generated_login.yaml \
  --hooks ./app_test_hooks.py
```

You can also pass a Python module path instead of a file path:

```bash
python -m cli.main generate https://app.example.com --hooks myapp.testing.hooks
```

## Export Formats

Your hook module can expose hooks in any of these ways:

```python
HOOKS = [MyHook()]
```

```python
hooks = [MyHook()]
```

```python
hook = MyHook()
```

```python
def get_hooks():
    return [MyHook()]
```

## Recommended Patterns

Use hooks for:
- application-specific selectors
- custom login/setup actions
- generated-plan cleanup
- stronger verification for business flows

Avoid using hooks for:
- generic framework fixes that should live in the core codebase
- large business workflows that belong in explicit YAML plans
- logic that depends on fragile text matching when stable selectors exist

## Practical Strategy

A good adoption path is:
1. Run `generate` or `explore` without hooks first.
2. Inspect the generated plan.
3. Add hooks only where your app has stable conventions the framework cannot infer reliably.
4. Use `execute_step` only for genuinely app-specific actions.

That keeps the framework generic while still giving your application enough control to improve automated test creation and execution.
