import typer
import time
import asyncio
import json
from pathlib import Path
from typing import Optional

from utils.hooks import HookManager

app = typer.Typer(add_completion=False, help="AI WebTester - Automated web application testing framework")

@app.command()
def run(
    plan: Path = typer.Option(..., help="Path to plan YAML"),
    env: Path = typer.Option(..., help="Path to environment YAML"),
    headful: bool = typer.Option(True, help="Open visible browser"),
    control_room: bool = typer.Option(False, help="Enable live Control Room"),
    artifacts_dir: Path = typer.Option(Path("artifacts"), help="Artifacts output dir"),
    hooks: Optional[str] = typer.Option(
        None,
        help="Comma-separated hook module names or file paths",
    ),
):
    """Run a test plan with optional Control Room."""
    run_id = time.strftime("%Y%m%dT%H%M%S")
    artifacts_dir = artifacts_dir / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def _run():
        hook_manager = HookManager.load(hooks)
        cr = None
        if control_room:
            from orchestrator.control_room import ControlRoom
            cr = ControlRoom()  # Will use dynamic port detection
            cr.start_in_background()
            print(f"Control Room ➜ {cr.get_url()}")

        from orchestrator.graph import TestGraph
        graph = TestGraph(
            artifacts_dir=str(artifacts_dir),
            headful=headful,
            control_room=cr,
            run_id=run_id,
            hook_manager=hook_manager,
        )
        try:
            result = await graph.run(str(plan), str(env))
        except Exception as e:
            result = {"status": "failed", "error": str(e)}

        # run.json is written by TestGraph's finally block; only write here as
        # a fallback if the file wasn't created (e.g. early crash before finally).
        run_json = artifacts_dir / "run.json"
        if not run_json.exists() and result:
            run_json.write_text(json.dumps(result, indent=2))
        print(f"Test run completed. Results saved to {artifacts_dir}")

    asyncio.run(_run())

@app.command()
def control_room():
    """Start the Control Room web interface."""
    from orchestrator.control_room import ControlRoom
    cr = ControlRoom()  # Will use dynamic port detection
    print(f"🎛️  Starting Control Room dashboard on {cr.get_url()}")
    cr.start()

@app.command()
def generate(
    url: str = typer.Argument(..., help="URL to analyze and generate test plan for"),
    description: str = typer.Option("", help="Description of what to test"),
    output_dir: Path = typer.Option(Path("examples"), help="Output directory for generated files"),
    headful: bool = typer.Option(False, help="Show browser during analysis"),
    interactive: bool = typer.Option(False, help="Interactive mode with prompts"),
    run_id: str = typer.Option("", help="Specific run ID for seeded data generation"),
    hooks: Optional[str] = typer.Option(
        None,
        help="Comma-separated hook module names or file paths",
    ),
):
    """Generate test plan from URL using AI analysis with seeded data generation."""
    async def _generate():
        from orchestrator.test_plan_generator import TestPlanGenerator
        hook_manager = HookManager.load(hooks)
        
        # Generate run_id if not provided
        if not run_id:
            import hashlib
            timestamp = int(time.time() * 1000)
            hash_obj = hashlib.md5(str(timestamp).encode())
            generated_run_id = f"gen_{timestamp}_{hash_obj.hexdigest()[:8]}"
        else:
            generated_run_id = run_id
        
        print(f"🔍 Analyzing {url} (Run ID: {generated_run_id})...")
        generator = TestPlanGenerator(run_id=generated_run_id, hook_manager=hook_manager)
        
        if interactive:
            result = await generator.interactive_generate(url)
        else:
            result = await generator.generate_from_url(
                url=url,
                test_description=description, 
                output_dir=str(output_dir),
                headful=headful
            )
            
            print(f"✅ Generated test plan: {result['plan_file']}")
            print(f"✅ Generated environment: {result['env_file']}")
            print(f"🌱 Seeded data generation using Run ID: {generated_run_id}")
            print(f"\n🏃 Run your test:")
            print(f"python -m cli.main run --plan {result['plan_file']} --env {result['env_file']} --control-room")
    
    asyncio.run(_generate())

@app.command()
def explore(
    url: str = typer.Argument(..., help="Base URL of the application to explore"),
    username: Optional[str] = typer.Option(None, help="Login username"),
    password: Optional[str] = typer.Option(None, help="Login password"),
    cookie_name: Optional[str] = typer.Option(None, "--cookie-name", help="Session cookie name"),
    cookie_value: Optional[str] = typer.Option(None, "--cookie-value", help="Session cookie value"),
    login_url: Optional[str] = typer.Option(None, "--login-url", help="Login page URL (auto-detected if omitted)"),
    max_depth: int = typer.Option(5, help="Maximum crawl depth"),
    modules: Optional[str] = typer.Option(None, help="Comma-separated module names to focus on"),
    headful: bool = typer.Option(True, help="Show browser during exploration"),
    no_tests: bool = typer.Option(False, "--no-tests", help="Skip test generation and execution (crawl only)"),
    crawl_only: bool = typer.Option(False, "--crawl-only", help="Crawl and generate tests but don't execute them"),
    control_room: bool = typer.Option(False, help="Enable live Control Room"),
    artifacts_dir: Path = typer.Option(Path("artifacts"), help="Artifacts output dir"),
    hooks: Optional[str] = typer.Option(
        None,
        help="Comma-separated hook module names or file paths",
    ),
):
    """Autonomously explore, map, and test a web application."""
    run_id = f"explore_{time.strftime('%Y%m%dT%H%M%S')}"
    artifacts_dir = artifacts_dir / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    module_filter = [m.strip() for m in modules.split(",")] if modules else None
    generate_tests = not no_tests
    execute_tests = generate_tests and not crawl_only

    async def _explore():
        hook_manager = HookManager.load(hooks)
        cr = None
        if control_room:
            from orchestrator.control_room import ControlRoom
            cr = ControlRoom()
            cr.start_in_background()
            print(f"Control Room -> {cr.get_url()}")

        from orchestrator.explorer import ExplorationOrchestrator
        orchestrator = ExplorationOrchestrator(
            artifacts_dir=str(artifacts_dir),
            headful=headful,
            run_id=run_id,
            control_room=cr,
            hook_manager=hook_manager,
        )

        try:
            result = await orchestrator.explore(
                base_url=url,
                username=username,
                password=password,
                cookie_name=cookie_name,
                cookie_value=cookie_value,
                login_url=login_url,
                max_depth=max_depth,
                module_filter=module_filter,
                generate_tests=generate_tests,
                execute_tests=execute_tests,
            )

            print(f"\nExploration complete:")
            print(f"  Pages discovered: {result.pages_discovered}")
            print(f"  Console errors:   {len(result.console_errors)}")
            print(f"  Network errors:   {len(result.network_errors)}")
            if result.tests_executed:
                print(f"  Tests passed:     {result.tests_passed}/{result.tests_executed}")
            print(f"  Duration:         {result.duration_seconds:.1f}s")
            print(f"  Results:          {artifacts_dir}")

        except Exception as e:
            print(f"Exploration failed: {e}")

    asyncio.run(_explore())


@app.command()
def mock_app():
    """Start the mock demo application."""
    import uvicorn
    from utils.ports import find_free_port

    port = find_free_port(start=5000)
    print(f"Starting mock app on http://127.0.0.1:{port}")
    uvicorn.run("mock_app.app:app", host="127.0.0.1", port=port, reload=True)

if __name__ == "__main__":
    app()
