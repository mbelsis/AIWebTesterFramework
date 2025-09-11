import asyncio
import time
import json
import logging
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

logger = logging.getLogger(__name__)

class Step:
    def __init__(self, data: Dict[str, Any]):
        self.title = data.get("title", "Untitled Step")
        self.action = data.get("action", "")
        self.target = data.get("target", "")
        self.data = data.get("data", {})
        self.verification = data.get("verification", {})

class Executor:
    def __init__(self, page, context, sink, control_room, run_id: str):
        self.page = page
        self.context = context
        self.sink = sink
        self.cr = control_room
        self.run_id = run_id
        self._step_active = False
        
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
        
        # Setup browser event listeners
        self.page.on("console", self._on_console)
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

    def _on_console(self, msg):
        if not self.cr: return
        
        # Apply redaction to console message
        console_text = msg.text
        if self.redactor and self.redactor.is_enabled():
            try:
                console_text = self.redactor.redact_text(console_text, ContentType.TEXT)
            except Exception as e:
                logger.error(f"Error redacting console message: {e}")
        
        asyncio.create_task(self.cr.send_log(
            self.run_id, msg.type, "console", console_text, time.time()
        ))

    def _on_request(self, req):
        if not self.cr: return
        
        # Apply redaction to request URL and method
        request_url = req.url
        if self.redactor and self.redactor.is_enabled():
            try:
                request_url = self.redactor.redact_url(request_url)
            except Exception as e:
                logger.error(f"Error redacting request URL: {e}")
        
        asyncio.create_task(self.cr.send_log(
            self.run_id, "info", "network", f"→ {req.method} {request_url}", time.time()
        ))

    def _on_response(self, resp):
        if not self.cr: return
        
        # Apply redaction to response URL
        response_url = resp.url
        if self.redactor and self.redactor.is_enabled():
            try:
                response_url = self.redactor.redact_url(response_url)
            except Exception as e:
                logger.error(f"Error redacting response URL: {e}")
        
        asyncio.create_task(self.cr.send_log(
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
        """Execute a single test step"""
        step = Step(step_data)
        self._step_active = True
        
        # Log step start to evidence
        self.sink.log_event("step_started", {"index": idx, "title": step.title, "action": step.action})
        
        if self.cr:
            await self.cr.send_step(self.run_id, idx, step.title, "executing")
        
        thumb_task = asyncio.create_task(self._thumb_loop()) if self.cr else None

        try:
            # Execute the step based on action type
            target = self._resolve_target(step.target, base_url)
            
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
            
            if self.cr:
                await self.cr.send_log(
                    self.run_id, "info", "agent", f"Step {idx}: {step.title} completed", time.time()
                )
                await self.cr.send_step(self.run_id, idx, step.title, "passed")

        except Exception as e:
            # Log failed step and capture screenshot
            self.sink.log_event("step_failed", {"index": idx, "title": step.title, "error": str(e)})
            
            try:
                screenshot = await self.page.screenshot()
                filename = f"step_{idx}_failure.png"
                self.sink.save_screenshot(screenshot, filename)
            except:
                pass
            
            error_msg = f"Step failed: {str(e)}"
            if self.cr:
                await self.cr.send_log(self.run_id, "error", "agent", error_msg, time.time())
                await self.cr.send_step(self.run_id, idx, step.title, "failed", str(e))
            raise
        finally:
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
        await self.page.wait_for_load_state("networkidle")

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
        await self.page.wait_for_load_state("networkidle")

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