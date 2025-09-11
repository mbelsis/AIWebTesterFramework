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
        started_at = time.time()
        playwright_instance = None
        browser = None
        context = None
        sink = None
        
        try:
            # Load plan and environment
            plan = self._load_yaml(plan_path)
            env = self._load_yaml(env_path)
            
            # Notify Control Room
            if self.cr:
                await self.cr.send_status(self.run_id, "starting", "Launching browser")

            # Setup browser context with proper cleanup tracking
            from browser.context import create_context
            playwright_instance, browser, context, page = await create_context(
                headful=self.headful, 
                artifacts_dir=self.artifacts_dir,
                env_config=env
            )

            # Setup evidence collection
            from evidence.sink import EvidenceSink
            sink = EvidenceSink(self.artifacts_dir)
            sink.log_event("test_started", {"plan_name": plan.get("name", "Unknown"), "env": env.get("name", "Unknown")})

            # Setup executor
            from orchestrator.executor import Executor
            executor = Executor(page, context, sink, self.cr, self.run_id)

            if self.cr:
                await self.cr.send_status(self.run_id, "running", "Executing test plan")

            # Execute steps
            steps = plan.get("steps", [])
            for idx, step in enumerate(steps):
                await executor.run_step(idx, step, env.get("target", {}).get("base_url", ""))

            # Save evidence
            if sink:
                sink.log_event("test_completed", {"status": "passed", "total_steps": len(steps)})
                sink.save_logs()

            if self.cr:
                await self.cr.send_status(self.run_id, "passed", "Test completed successfully")

            return {
                "run_id": self.run_id,
                "status": "passed",
                "plan_name": plan.get("name", "Unknown"),
                "started_at": started_at,
                "ended_at": time.time(),
                "artifacts_dir": self.artifacts_dir,
                "artifacts": sink.get_artifact_files() if sink else []
            }

        except Exception as e:
            # Log failure
            if sink:
                sink.log_event("test_failed", {"error": str(e)})
                # Capture failure screenshot
                try:
                    if 'page' in locals() and page:
                        screenshot = await page.screenshot()
                        sink.save_screenshot(screenshot, "failure_screenshot.png")
                except:
                    pass
                sink.save_logs()
            
            if self.cr:
                await self.cr.send_status(self.run_id, "failed", f"Test failed: {str(e)}")
            
            return {
                "run_id": self.run_id,
                "status": "failed",
                "error": str(e),
                "started_at": started_at,
                "ended_at": time.time(),
                "artifacts_dir": self.artifacts_dir,
                "artifacts": sink.get_artifact_files() if sink else []
            }
        
        finally:
            # Ensure proper cleanup
            try:
                if context:
                    await context.tracing.stop(path=str(Path(self.artifacts_dir) / "trace.zip"))
                    await context.close()
                if browser:
                    await browser.close()
                if playwright_instance:
                    await playwright_instance.stop()
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)