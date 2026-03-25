# Jenkins Integration

## Overview

AI WebTester can be integrated into a Jenkins CI/CD pipeline because it is a CLI-driven Python framework.

Jenkins is responsible for:
- provisioning the build agent
- installing dependencies
- injecting secrets
- starting or targeting the application under test
- archiving artifacts

AI WebTester is responsible for:
- analyzing the target application
- generating test plans
- executing browser automation
- collecting screenshots, traces, videos, and logs

## Requirements

Your Jenkins agent should provide:
- Python 3.11 or newer
- network access to the application under test
- permission to write the Jenkins workspace
- enough disk space for Playwright and test artifacts

For AI-assisted generation, also provide:
- `OPENAI_API_KEY`

## What You Can Run In Jenkins

### Fixed regression plans

Use `run` when you already have YAML plans. In a real pipeline, replace the example files with your own checked-in plan and environment files:

```bash
python -m cli.main run --plan tests/ai/plan.login.yaml --env tests/ai/env.ci.yaml
```

### AI-assisted plan creation

Use `generate` when you want the framework to inspect a page and create a plan:

```bash
python -m cli.main generate https://app.example.com/login --description "Test login flow"
```

### Autonomous exploration

Use `explore` when you want the framework to crawl and test a larger part of the app:

```bash
python -m cli.main explore https://app.example.com/login --username qa-user --password TestPass123!
```

## Optional Hooks

If your application has custom flows or selectors, you can attach a hook module:

```bash
python -m cli.main generate https://app.example.com/login --hooks myapp.testing.hooks
python -m cli.main run --plan examples/plan.generated_login.yaml --env examples/env.generated_login.yaml --hooks myapp.testing.hooks
```

See [hooks.md](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/hooks.md) for the supported hook points.

## Recommended Jenkins Flow

1. Check out the repository.
2. Install Python dependencies.
3. Install Playwright Chromium.
4. Start the target application, or point to a deployed environment.
5. Run `generate`, `explore`, or `run`.
6. Archive `artifacts/**`.

## Notes

- This framework currently uses Chromium-based Playwright execution.
- Artifact archiving is important because test evidence is one of the main outputs of the framework.
- If `OPENAI_API_KEY` is missing, the generator can fall back to non-AI plan generation in supported paths.
- For long-lived regression suites, it is usually better to generate once, review the plan, and then run the saved YAML in Jenkins.

## Included Example

This folder also includes a sample [Jenkinsfile](/C:/Users/mbelsis/Documents/GitHub/AIWebTesterFramework/docs/jenkins/Jenkinsfile) that:
- installs dependencies
- installs Playwright Chromium
- exposes `AIWEBTEST_PLAN`, `AIWEBTEST_ENV`, and `AIWEBTEST_EXTRA_ARGS` as Jenkins parameters
- runs the framework against whichever plan and environment file your pipeline provides
- archives artifacts

The defaults still point to the demo files so the example runs out of the box, but that is only a placeholder.

In a user pipeline, the normal flow is:

1. Build and deploy the user's application, or start it in the Jenkins workspace.
2. Wait until the target URL is reachable.
3. Run AI WebTester with the team's own `plan` and `env` YAML files.
4. Archive `artifacts/**`.

Example:

```groovy
stage('Run AI WebTester') {
  steps {
    script {
      if (isUnix()) {
        sh 'python3 -m cli.main run --plan tests/ai/plan.login.yaml --env tests/ai/env.ci.yaml --no-headful'
      } else {
        bat 'python -m cli.main run --plan tests/ai/plan.login.yaml --env tests/ai/env.ci.yaml --no-headful'
      }
    }
  }
}
```

Adjust the commands to match your agent OS, application startup, and deployment flow.
