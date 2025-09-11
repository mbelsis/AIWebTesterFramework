#!/usr/bin/env python3
"""
AI WebTester - Quick test runner
This script provides a simple way to run the AI WebTester with the demo application.
"""

import asyncio
import json
import time
from pathlib import Path
from orchestrator.graph import TestGraph
from orchestrator.control_room import ControlRoom

PLAN = "examples/plan.demo_create_employee.yaml"
ENV = "examples/env.local.yaml"

async def main():
    """Run a quick test with the demo application"""
    run_id = time.strftime("%Y%m%dT%H%M%S")
    artifacts = Path("artifacts") / run_id
    artifacts.mkdir(parents=True, exist_ok=True)

    print("Starting AI WebTester demo...")
    print(f"Run ID: {run_id}")
    print(f"Artifacts will be saved to: {artifacts}")

    # Start Control Room
    cr = ControlRoom()
    cr.start_in_background()
    print("Control Room ➜ http://127.0.0.1:8788")

    # Create and run test (headless mode for better compatibility)
    graph = TestGraph(str(artifacts), headful=False, control_room=cr, run_id=run_id)
    result = await graph.run(PLAN, ENV)
    
    # Save results
    (artifacts / "run.json").write_text(json.dumps(result, indent=2))
    
    print(f"\nTest completed with status: {result['status']}")
    print(f"Results saved to: {artifacts / 'run.json'}")
    
    if result["status"] == "passed":
        print("✅ All tests passed!")
    else:
        print("❌ Test failed:", result.get("error", "Unknown error"))

if __name__ == "__main__":
    asyncio.run(main())