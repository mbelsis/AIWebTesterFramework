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
            cr = ControlRoom()
            cr.start_in_background()
            print(f"Control Room ➜ http://127.0.0.1:8788")

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
    cr = ControlRoom()
    cr.start()

@app.command()
def mock_app():
    """Start the mock demo application."""
    import uvicorn
    uvicorn.run("mock_app.app:app", host="127.0.0.1", port=5000, reload=True)

if __name__ == "__main__":
    app()