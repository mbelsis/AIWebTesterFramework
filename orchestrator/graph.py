import asyncio
import json
import time
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

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
        page = None
        sink = None
        steps = []  # Initialize to avoid unbound variable issues
        run_result = None  # CRITICAL FIX: Track run result for finally block
        
        try:
            # Load plan and environment
            plan = self._load_yaml(plan_path)
            env = self._load_yaml(env_path)
            
            # Notify Control Room
            if self.cr:
                await self.cr.send_status(self.run_id, "starting", "Launching browser")

            # Setup browser context with proper cleanup tracking
            from browser.context import create_context
            playwright_instance, browser, context, page, network_tracker, state_capture = await create_context(
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

            end_time = time.time()
            run_result = {
                "run_id": self.run_id,
                "status": "passed",
                "plan_name": plan.get("name", "Unknown"),
                "started_at": started_at,
                "ended_at": end_time,
                "duration_seconds": end_time - started_at,
                "artifacts_dir": self.artifacts_dir,
                "artifacts": [],  # Will be populated after finalization
                "total_steps": len(steps)
            }
            return run_result

        except Exception as e:
            # Log failure
            if sink:
                sink.log_event("test_failed", {"error": str(e)})
                # Capture failure screenshot
                try:
                    if 'page' in locals() and page:
                        screenshot = await page.screenshot()
                        sink.save_screenshot(screenshot, "failure_screenshot.png")
                except Exception:
                    pass
                sink.save_logs()
            
            if self.cr:
                await self.cr.send_status(self.run_id, "failed", f"Test failed: {str(e)}")
            
            end_time = time.time()
            run_result = {
                "run_id": self.run_id,
                "status": "failed",
                "error": str(e),
                "started_at": started_at,
                "ended_at": end_time,
                "duration_seconds": end_time - started_at,
                "artifacts_dir": self.artifacts_dir,
                "artifacts": [],  # Will be populated after finalization
                "total_steps": len(steps) if 'steps' in locals() and steps is not None else 0
            }
            return run_result
        
        finally:
            # CRITICAL FIX: Proper cleanup order with finalization and run.json emission
            finalization_result = None
            try:
                # Step 1: Finalize video/trace (context closure happens here now)
                if context:
                    from browser.context import finalize_video_and_trace
                    finalization_result = await finalize_video_and_trace(context, self.artifacts_dir)
                    
                    # Log finalization results
                    if sink:
                        sink.log_event("finalization_completed", finalization_result)
                    
                    if finalization_result["status"] not in ["success", "success_with_warnings"]:
                        logger.warning(f"Video/trace finalization had issues: {finalization_result['errors']}")
                
                # Step 2: Close remaining browser resources (context already closed in finalization)
                if browser:
                    await browser.close()
                if playwright_instance:
                    await playwright_instance.stop()
                    
                # Step 3: CRITICAL FIX - Update artifacts after finalization and emit run.json
                if sink and run_result:
                    # Update artifacts list after finalization
                    run_result["artifacts"] = sink.get_artifact_files()
                    
                    # Generate comprehensive run summary AND minimal run.json
                    self._save_run_summary(sink, finalization_result, run_result)
                elif sink:
                    # Fallback for cases where run_result wasn't set
                    logger.warning("No run result available - creating minimal fallback")
                    fallback_result = {
                        "run_id": self.run_id,
                        "status": "unknown",
                        "plan_name": "Unknown",
                        "started_at": started_at,
                        "ended_at": time.time(),
                        "duration_seconds": time.time() - started_at
                    }
                    self._save_run_summary(sink, finalization_result, fallback_result)
                    
            except Exception as cleanup_error:
                logger.error(f"Cleanup error: {cleanup_error}")
                if sink:
                    sink.log_event("cleanup_error", {"error": str(cleanup_error)})
                print(f"Cleanup error: {cleanup_error}")

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"YAML file is empty or invalid: {path}")
        return data
    
    def _save_run_summary(self, sink, finalization_result: Optional[Dict[str, Any]] = None, run_result: Optional[Dict[str, Any]] = None):
        """Generate and save comprehensive run summary JSON and minimal run.json."""
        try:
            # Get all artifacts from sink
            all_artifacts = sink.get_artifact_files() if sink else []
            
            # Categorize artifacts by type
            categorized_artifacts = {
                "videos": [f for f in all_artifacts if f.endswith(('.webm', '.mp4'))],
                "traces": [f for f in all_artifacts if f.endswith('.zip')],
                "screenshots": [f for f in all_artifacts if f.endswith('.png')],
                "logs": [f for f in all_artifacts if f.endswith('.json')],
                "other": [f for f in all_artifacts if not any(f.endswith(ext) for ext in ['.webm', '.mp4', '.zip', '.png', '.json'])]
            }
            
            # Create comprehensive run summary
            run_summary = {
                "run_id": self.run_id,
                "artifacts_path": self.artifacts_dir,
                "evidence_files": all_artifacts,
                "categorized_artifacts": categorized_artifacts,
                "total_artifact_count": len(all_artifacts),
                "generated_at": time.time()
            }
            
            # Include finalization results if available
            if finalization_result:
                run_summary["finalization"] = finalization_result
                
                # Extract video and trace information from finalization results
                if "artifacts" in finalization_result:
                    finalization_artifacts = finalization_result["artifacts"]
                    if "videos" in finalization_artifacts:
                        run_summary["video_details"] = finalization_artifacts["videos"]
                    if "trace" in finalization_artifacts:
                        run_summary["trace_details"] = finalization_artifacts["trace"]
            
            # Save comprehensive run summary to artifacts directory
            summary_path = Path(self.artifacts_dir) / "run_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(run_summary, f, indent=2)
            
            logger.info(f"Run summary saved to {summary_path}")
            
            # CRITICAL FIX: Also emit minimal run.json as required
            if run_result:
                minimal_run = {
                    "run_id": run_result.get("run_id", self.run_id),
                    "status": run_result.get("status", "unknown"),
                    "plan_name": run_result.get("plan_name", "Unknown"),
                    "started_at": run_result.get("started_at", time.time()),
                    "ended_at": run_result.get("ended_at", time.time()),
                    "duration_seconds": run_result.get("duration_seconds", 0)
                }
                
                run_json_path = Path(self.artifacts_dir) / "run.json"
                with open(run_json_path, 'w') as f:
                    json.dump(minimal_run, f, indent=2)
                
                logger.info(f"Minimal run.json saved to {run_json_path}")
            else:
                logger.warning("No run result provided - minimal run.json not generated")
            
            # Also log the summary creation
            if sink:
                sink.log_event("run_summary_generated", {
                    "summary_path": str(summary_path),
                    "total_artifacts": len(all_artifacts),
                    "finalization_status": finalization_result.get("status") if finalization_result else "unknown"
                })
                
        except Exception as e:
            logger.error(f"Error generating run summary: {e}")
            if sink:
                sink.log_event("run_summary_error", {"error": str(e)})