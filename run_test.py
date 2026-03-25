#!/usr/bin/env python3
"""
AI WebTester - Quick test runner
This script provides a simple way to run the AI WebTester with the demo application.
It auto-starts the mock application if it isn't already running.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

from utils.ports import find_free_port

PLAN = "examples/plan.demo_create_employee.yaml"
ENV = "examples/env.local.yaml"
MOCK_APP_HEALTH_TIMEOUT = 30  # seconds


def _check_mock_app(port: int) -> bool:
    """Check if the mock app is responding on the given port."""
    try:
        resp = urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
        return resp.status == 200
    except (URLError, OSError):
        return False


def _start_mock_app() -> tuple:
    """Start the mock app in a subprocess and return (process, port)."""
    port = find_free_port(start=5000)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_app.app:app",
         "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for the app to become healthy
    print(f"Starting mock app on port {port}...")
    deadline = time.time() + MOCK_APP_HEALTH_TIMEOUT
    while time.time() < deadline:
        if _check_mock_app(port):
            print(f"Mock app ready at http://127.0.0.1:{port}")
            return proc, port
        if proc.poll() is not None:
            raise RuntimeError(f"Mock app process exited with code {proc.returncode}")
        time.sleep(0.5)

    proc.terminate()
    raise RuntimeError(f"Mock app did not become healthy within {MOCK_APP_HEALTH_TIMEOUT}s")


async def main():
    """Run a quick test with the demo application"""
    run_id = time.strftime("%Y%m%dT%H%M%S")
    artifacts = Path("artifacts") / run_id
    artifacts.mkdir(parents=True, exist_ok=True)

    print("Starting AI WebTester demo...")
    print(f"Run ID: {run_id}")
    print(f"Artifacts will be saved to: {artifacts}")

    # Auto-start mock app if not already running
    mock_proc = None
    mock_port = 5000
    if _check_mock_app(mock_port):
        print(f"Mock app already running on port {mock_port}")
    else:
        mock_proc, mock_port = _start_mock_app()

    # Start Control Room
    from orchestrator.control_room import ControlRoom
    cr = ControlRoom()
    cr.start_in_background()
    print(f"Control Room -> {cr.get_url()}")

    # Create and run test (headless mode for better compatibility)
    from orchestrator.graph import TestGraph
    graph = TestGraph(str(artifacts), headful=False, control_room=cr, run_id=run_id)
    try:
        result = await graph.run(PLAN, ENV)
    except Exception as e:
        result = {"status": "failed", "error": str(e)}

    # Save results (only if graph.py's finally block didn't already write it)
    run_json = artifacts / "run.json"
    if not run_json.exists() and result:
        run_json.write_text(json.dumps(result, indent=2))

    status = result.get("status", "unknown") if result else "unknown"
    print(f"\nTest completed with status: {status}")
    print(f"Results saved to: {artifacts / 'run.json'}")

    if status == "passed":
        print("All tests passed!")
    else:
        print("Test failed:", result.get("error", "Unknown error") if result else "Unknown error")

    # Cleanup: stop mock app if we started it
    if mock_proc:
        mock_proc.terminate()
        mock_proc.wait(timeout=5)
        print("Mock app stopped.")


if __name__ == "__main__":
    asyncio.run(main())
