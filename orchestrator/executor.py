import asyncio
import time
import json
import logging
import copy
from typing import Dict, Any, Optional

# Import redaction utilities for secure test execution logging
try:
    from utils.redaction import get_redactor, ContentType
    REDACTION_AVAILABLE = True
except ImportError:
    from enum import Enum
    REDACTION_AVAILABLE = False
    
    class ContentType(Enum):
        TEXT = "text"
    
    def get_redactor():
        return None

# Import watchdog utilities for stuck-screen detection and recovery
try:
    from utils.watchdog import Watchdog, RecoveryStrategy
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    
    class Watchdog:
        def __init__(self, *args, **kwargs):
            pass
        async def start_monitoring(self, *args, **kwargs):
            pass
        async def stop_monitoring(self):
            pass
        def track_network_request(self, *args):
            pass
        def is_monitoring(self):
            return False

logger = logging.getLogger(__name__)

class Step:
    def __init__(self, data: Dict[str, Any]):
        self.title = data.get("title", "Untitled Step")
        self.action = data.get("action", "")
        self.target = data.get("target", "")
        self.data = data.get("data", {})
        self.verification = data.get("verification", {})

class Executor:
    def __init__(self, page, context, sink, control_room, run_id: str, hook_manager=None):
        self.page = page
        self.context = context
        self.sink = sink
        self.cr = control_room
        self.run_id = run_id
        self._step_active = False
        self.hook_manager = hook_manager
        
        # Initialize redaction if available
        self.redactor = None
        if REDACTION_AVAILABLE:
            try:
                self.redactor = get_redactor()
                if self.redactor and self.redactor.is_enabled():
                    logger.info("Security redaction enabled for test execution")
            except Exception as e:
                logger.warning(f"Failed to initialize redactor in executor: {e}")
                self.redactor = None
        
        # Initialize watchdog if available
        self.watchdog = None
        if WATCHDOG_AVAILABLE:
            try:
                self.watchdog = Watchdog(sink=self.sink)
                logger.info("Watchdog system initialized for stuck-screen detection")
            except Exception as e:
                logger.warning(f"Failed to initialize watchdog in executor: {e}")
                self.watchdog = None
        
        # Setup browser event listeners
        self.page.on("console", self._on_console)
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

    def _safe_create_task(self, coro):
        """Create an asyncio task only if an event loop is running."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            # No running event loop — skip the async send
            logger.debug("No running event loop; skipping async task creation")

    def _on_console(self, msg):
        if not self.cr: return

        # Apply redaction to console message
        console_text = msg.text
        if self.redactor and self.redactor.is_enabled():
            try:
                console_text = self.redactor.redact_text(console_text, ContentType.TEXT)
            except Exception as e:
                logger.error(f"Error redacting console message: {e}")

        self._safe_create_task(self.cr.send_log(
            self.run_id, msg.type, "console", console_text, time.time()
        ))

    def _on_request(self, req):
        # Track request with watchdog if available
        if self.watchdog:
            self.watchdog.track_network_request("request")

        if not self.cr: return

        # Apply redaction to request URL and method
        request_url = req.url
        if self.redactor and self.redactor.is_enabled():
            try:
                request_url = self.redactor.redact_url(request_url)
            except Exception as e:
                logger.error(f"Error redacting request URL: {e}")

        self._safe_create_task(self.cr.send_log(
            self.run_id, "info", "network", f"→ {req.method} {request_url}", time.time()
        ))

    def _on_response(self, resp):
        # Track response with watchdog if available
        if self.watchdog:
            self.watchdog.track_network_request("response")

        if not self.cr: return

        # Apply redaction to response URL
        response_url = resp.url
        if self.redactor and self.redactor.is_enabled():
            try:
                response_url = self.redactor.redact_url(response_url)
            except Exception as e:
                logger.error(f"Error redacting response URL: {e}")

        self._safe_create_task(self.cr.send_log(
            self.run_id, "info", "network", f"← {resp.status} {response_url}", time.time()
        ))

    async def _thumb_loop(self):
        """Throttled screenshot loop while step is active"""
        last = 0
        while self._step_active:
            now = time.time()
            if now - last > 0.6:
                try:
                    png = await self.page.screenshot(full_page=False)
                    if self.cr:
                        await self.cr.send_thumb_png(self.run_id, png, ts=now)
                except Exception:
                    pass
                last = now
            await asyncio.sleep(0.05)

    async def run_step(self, idx: int, step_data: Dict[str, Any], base_url: str = ""):
        """Execute a single test step with watchdog monitoring"""
        step_payload = copy.deepcopy(step_data)
        hook_context = {
            "step_index": idx,
            "base_url": base_url,
            "run_id": self.run_id,
        }
        if self.hook_manager:
            step_payload = await self.hook_manager.transform("before_step", step_payload, hook_context)

        step = Step(step_payload)
        self._step_active = True
        
        # Log step start to evidence
        self.sink.log_event("step_started", {"index": idx, "title": step.title, "action": step.action})
        
        if self.cr:
            await self.cr.send_step(self.run_id, idx, step.title, "executing")
        
        thumb_task = asyncio.create_task(self._thumb_loop()) if self.cr else None
        
        # Start watchdog monitoring if available
        watchdog_monitoring = False
        if self.watchdog:
            try:
                await self.watchdog.start_monitoring(self.page, self.context, self.run_id)
                watchdog_monitoring = True
                logger.debug(f"Watchdog monitoring started for step {idx}: {step.title}")
            except Exception as e:
                logger.warning(f"Failed to start watchdog monitoring for step {idx}: {e}")

        try:
            # Execute the step based on action type
            target = self._resolve_target(step.target, base_url)
            hook_context["resolved_target"] = target

            handled_result = None
            if self.hook_manager:
                handled_result = await self.hook_manager.execute_step(step_payload, self, hook_context)
             
            if handled_result is None:
                if step.action == "navigate":
                    await self._navigate(target)
                elif step.action == "click":
                    await self._click(target)
                elif step.action == "fill":
                    await self._fill(target, step.data.get("value", ""))
                elif step.action == "submit":
                    await self._submit(target)
                elif step.action == "wait":
                    await self._wait(step.data.get("seconds", 1))
                elif step.action == "verify":
                    await self._verify(step.verification)
                else:
                    raise ValueError(f"Unknown action: {step.action}")

            # Log successful step
            self.sink.log_event("step_completed", {"index": idx, "title": step.title, "status": "passed"})
            if self.hook_manager:
                result_payload = {
                    "status": "passed",
                    "index": idx,
                    "title": step.title,
                    "action": step.action,
                    "target": target,
                    "handled_by_hook": handled_result is not None,
                }
                await self.hook_manager.transform("after_step", result_payload, hook_context)
             
            if self.cr:
                await self.cr.send_log(
                    self.run_id, "info", "agent", f"Step {idx}: {step.title} completed", time.time()
                )
                await self.cr.send_step(self.run_id, idx, step.title, "passed")

        except Exception as e:
            # Check if this was a watchdog-detected stuck state
            is_stuck_state = self.watchdog and not self.watchdog.is_monitoring() and hasattr(e, '__cause__')
            
            # Log failed step and capture screenshot
            self.sink.log_event("step_failed", {
                "index": idx, 
                "title": step.title, 
                "error": str(e),
                "stuck_state_detected": is_stuck_state
            })
            
            try:
                screenshot = await self.page.screenshot()
                filename = f"step_{idx}_failure.png"
                self.sink.save_screenshot(screenshot, filename)
            except Exception:
                pass

            error_msg = f"Step failed: {str(e)}"
            if self.cr:
                await self.cr.send_log(self.run_id, "error", "agent", error_msg, time.time())
                await self.cr.send_step(self.run_id, idx, step.title, "failed", str(e))
            if self.hook_manager:
                await self.hook_manager.notify("on_step_failure", step_payload, e, hook_context)
            raise
        finally:
            # Stop watchdog monitoring
            if watchdog_monitoring and self.watchdog:
                try:
                    await self.watchdog.stop_monitoring()
                    logger.debug(f"Watchdog monitoring stopped for step {idx}")
                except Exception as e:
                    logger.warning(f"Error stopping watchdog monitoring: {e}")
            
            self._step_active = False
            if thumb_task:
                thumb_task.cancel()

    def _resolve_target(self, target: str, base_url: str) -> str:
        """Resolve target URL with base_url if needed"""
        if target.startswith("http"):
            return target
        if base_url and target.startswith("/"):
            return base_url.rstrip("/") + target
        return target
    
    async def _navigate(self, url: str):
        """Navigate to URL"""
        await self.page.goto(url)
        await self.page.wait_for_load_state("domcontentloaded")
        # Brief settle wait — networkidle is too brittle for SPAs/analytics
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass  # Timeout is acceptable — page is interactive after domcontentloaded

    async def _click(self, selector: str):
        """Click element"""
        # Wait for selector to be available
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.click(selector)
        await asyncio.sleep(0.5)  # Brief pause after click

    async def _fill(self, selector: str, value: str):
        """Fill form field"""
        # Wait for selector to be available
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.fill(selector, value)

    async def _submit(self, selector: str):
        """Submit form"""
        # Wait for selector to be available
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.click(selector)
        await self.page.wait_for_load_state("domcontentloaded")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

    async def _wait(self, seconds: float):
        """Wait for specified time"""
        await asyncio.sleep(seconds)

    async def _verify(self, verification: Dict[str, Any]):
        """Verify page state"""
        if "text" in verification:
            await self.page.wait_for_selector(f"text={verification['text']}")
        if "selector" in verification:
            await self.page.wait_for_selector(verification["selector"])

    async def require_approval(self, reason: str) -> bool:
        """Request user approval for destructive actions"""
        if not self.cr:
            return True
        
        await self.cr.send_status(self.run_id, "awaiting_approval", reason)
        cmd = await self.cr.wait_for_control(self.run_id, {"approve", "reject", "stop"})
        
        if cmd.get("cmd") == "approve":
            await self.cr.send_status(self.run_id, "running", "Approved")
            return True
        elif cmd.get("cmd") == "reject":
            await self.cr.send_status(self.run_id, "paused", "Rejected by user")
            return False
        else:
            await self.cr.send_status(self.run_id, "cancelled", "Stopped by user")
            raise RuntimeError("Run stopped by user")
