import asyncio
import json
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class TestGraph:
    def __init__(self, artifacts_dir: str, headful: bool, control_room, run_id: str):
        self.artifacts_dir = artifacts_dir
        self.headful = headful
        self.cr = control_room
        self.run_id = run_id

    async def run(self, plan_path: str, env_path: str) -> Dict[str, Any]:
        """Execute the test plan"""
        try:
            # Load plan and environment
            plan = self._load_yaml(plan_path)
            env = self._load_yaml(env_path)
            
            # Notify Control Room
            if self.cr:
                await self.cr.send_status(self.run_id, "starting", "Launching browser")

            # Setup browser context
            from browser.context import create_context
            browser, context, page = await create_context(
                headful=self.headful, 
                artifacts_dir=self.artifacts_dir
            )

            # Setup evidence collection
            from evidence.sink import EvidenceSink
            sink = EvidenceSink(self.artifacts_dir)

            # Setup executor
            from orchestrator.executor import Executor
            executor = Executor(page, context, sink, self.cr, self.run_id)

            if self.cr:
                await self.cr.send_status(self.run_id, "running", "Executing test plan")

            # Execute steps
            steps = plan.get("steps", [])
            for idx, step in enumerate(steps):
                await executor.run_step(idx, step)

            # Finalize
            await context.tracing.stop(path=str(Path(self.artifacts_dir) / "trace.zip"))
            await context.close()
            await browser.close()

            if self.cr:
                await self.cr.send_status(self.run_id, "passed", "Test completed successfully")

            return {
                "run_id": self.run_id,
                "status": "passed",
                "plan_name": plan.get("name", "Unknown"),
                "started_at": time.time(),
                "artifacts_dir": self.artifacts_dir
            }

        except Exception as e:
            if self.cr:
                await self.cr.send_status(self.run_id, "failed", f"Test failed: {str(e)}")
            
            return {
                "run_id": self.run_id,
                "status": "failed",
                "error": str(e),
                "started_at": time.time(),
                "artifacts_dir": self.artifacts_dir
            }

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)