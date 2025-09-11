import typer
import time
import asyncio
import json
from pathlib import Path
from typing import Optional

app = typer.Typer(add_completion=False, help="AI WebTester - Automated web application testing framework")

@app.command()
def run(
    plan: Path = typer.Option(..., help="Path to plan YAML"),
    env: Path = typer.Option(..., help="Path to environment YAML"),
    headful: bool = typer.Option(True, help="Open visible browser"),
    control_room: bool = typer.Option(False, help="Enable live Control Room"),
    artifacts_dir: Path = typer.Option(Path("artifacts"), help="Artifacts output dir"),
):
    """Run a test plan with optional Control Room."""
    run_id = time.strftime("%Y%m%dT%H%M%S")
    artifacts_dir = artifacts_dir / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def _run():
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
            run_id=run_id
        )
        result = await graph.run(str(plan), str(env))
        (artifacts_dir / "run.json").write_text(json.dumps(result, indent=2))
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
    run_id: str = typer.Option("", help="Specific run ID for seeded data generation")
):
    """Generate test plan from URL using AI analysis with seeded data generation."""
    async def _generate():
        from orchestrator.test_plan_generator import TestPlanGenerator
        
        # Generate run_id if not provided
        if not run_id:
            import hashlib
            timestamp = int(time.time() * 1000)
            hash_obj = hashlib.md5(str(timestamp).encode())
            generated_run_id = f"gen_{timestamp}_{hash_obj.hexdigest()[:8]}"
        else:
            generated_run_id = run_id
        
        print(f"🔍 Analyzing {url} (Run ID: {generated_run_id})...")
        generator = TestPlanGenerator(run_id=generated_run_id)
        
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
def mock_app():
    """Start the mock demo application."""
    import uvicorn
    from utils.ports import find_free_port
    
    port = find_free_port(start=5000)
    print(f"🚀 Starting mock app on http://127.0.0.1:{port}")
    uvicorn.run("mock_app.app:app", host="127.0.0.1", port=port, reload=True)

if __name__ == "__main__":
    app()