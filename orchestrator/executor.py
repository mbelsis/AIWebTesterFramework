import asyncio
import time
import json
from typing import Dict, Any, Optional

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
        
        # Setup browser event listeners
        self.page.on("console", self._on_console)
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

    def _on_console(self, msg):
        if not self.cr: return
        asyncio.create_task(self.cr.send_log(
            self.run_id, msg.type, "console", msg.text, time.time()
        ))

    def _on_request(self, req):
        if not self.cr: return
        asyncio.create_task(self.cr.send_log(
            self.run_id, "info", "network", f"→ {req.method} {req.url}", time.time()
        ))

    def _on_response(self, resp):
        if not self.cr: return
        asyncio.create_task(self.cr.send_log(
            self.run_id, "info", "network", f"← {resp.status} {resp.url}", time.time()
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

    async def run_step(self, idx: int, step_data: Dict[str, Any]):
        """Execute a single test step"""
        step = Step(step_data)
        self._step_active = True
        
        if self.cr:
            await self.cr.send_step(self.run_id, idx, step.title, "executing")
        
        thumb_task = asyncio.create_task(self._thumb_loop()) if self.cr else None

        try:
            # Execute the step based on action type
            if step.action == "navigate":
                await self._navigate(step.target)
            elif step.action == "click":
                await self._click(step.target)
            elif step.action == "fill":
                await self._fill(step.target, step.data.get("value", ""))
            elif step.action == "submit":
                await self._submit(step.target)
            elif step.action == "wait":
                await self._wait(step.data.get("seconds", 1))
            elif step.action == "verify":
                await self._verify(step.verification)
            else:
                raise ValueError(f"Unknown action: {step.action}")

            # Log successful step
            if self.cr:
                await self.cr.send_log(
                    self.run_id, "info", "agent", f"Step {idx}: {step.title} completed", time.time()
                )
                await self.cr.send_step(self.run_id, idx, step.title, "passed")

        except Exception as e:
            error_msg = f"Step failed: {str(e)}"
            if self.cr:
                await self.cr.send_log(self.run_id, "error", "agent", error_msg, time.time())
                await self.cr.send_step(self.run_id, idx, step.title, "failed", str(e))
            raise
        finally:
            self._step_active = False
            if thumb_task:
                thumb_task.cancel()

    async def _navigate(self, url: str):
        """Navigate to URL"""
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

    async def _click(self, selector: str):
        """Click element"""
        await self.page.click(selector)
        await asyncio.sleep(0.5)  # Brief pause after click

    async def _fill(self, selector: str, value: str):
        """Fill form field"""
        await self.page.fill(selector, value)

    async def _submit(self, selector: str):
        """Submit form"""
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