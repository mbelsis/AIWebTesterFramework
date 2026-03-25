"""
Tests for the Executor step actions and the Step data class.
These tests use mock Playwright objects to validate logic without needing a real browser.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.executor import Executor, Step
from utils.hooks import HookManager


# ── Step dataclass ────────────────────────────────────────────────────────────

class TestStep:
    def test_defaults(self):
        s = Step({})
        assert s.title == "Untitled Step"
        assert s.action == ""
        assert s.target == ""
        assert s.data == {}
        assert s.verification == {}

    def test_from_dict(self):
        s = Step({
            "title": "Fill email",
            "action": "fill",
            "target": "#email",
            "data": {"value": "a@b.com"},
            "verification": {"text": "ok"},
        })
        assert s.title == "Fill email"
        assert s.action == "fill"
        assert s.data["value"] == "a@b.com"


# ── Executor helpers ──────────────────────────────────────────────────────────

def _make_executor(page=None, context=None, sink=None, cr=None, hook_manager=None):
    """Build an Executor with mocked dependencies."""
    if page is None:
        page = MagicMock()
    page.on = MagicMock()  # prevent listener registration errors
    page.evaluate = AsyncMock(return_value="")
    if context is None:
        context = MagicMock()
    if sink is None:
        sink = MagicMock()
        sink.log_event = MagicMock()
        sink.save_screenshot = MagicMock()
    return Executor(page, context, sink, cr, run_id="test-run", hook_manager=hook_manager)


class TestResolveTarget:
    def test_absolute_url_unchanged(self):
        ex = _make_executor()
        assert ex._resolve_target("https://app.com/page", "https://base.com") == "https://app.com/page"

    def test_relative_path_combined_with_base(self):
        ex = _make_executor()
        assert ex._resolve_target("/dashboard", "https://base.com") == "https://base.com/dashboard"

    def test_base_trailing_slash_stripped(self):
        ex = _make_executor()
        assert ex._resolve_target("/page", "https://base.com/") == "https://base.com/page"

    def test_css_selector_returned_as_is(self):
        ex = _make_executor()
        assert ex._resolve_target("#submit-btn", "https://base.com") == "#submit-btn"

    def test_empty_base_url(self):
        ex = _make_executor()
        assert ex._resolve_target("/page", "") == "/page"


class TestNavigateAction:
    @pytest.mark.asyncio
    async def test_navigate_calls_goto(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._navigate("https://app.com")
        page.goto.assert_called_once_with("https://app.com")
        page.wait_for_load_state.assert_any_call("domcontentloaded")


class TestClickAction:
    @pytest.mark.asyncio
    async def test_click_waits_and_clicks(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._click("#btn")
        page.wait_for_selector.assert_called_once_with("#btn", timeout=10000)
        page.click.assert_called_once_with("#btn")


class TestFillAction:
    @pytest.mark.asyncio
    async def test_fill_waits_and_fills(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._fill("#email", "test@example.com")
        page.wait_for_selector.assert_called_once_with("#email", timeout=10000)
        page.fill.assert_called_once_with("#email", "test@example.com")


class TestSubmitAction:
    @pytest.mark.asyncio
    async def test_submit_clicks_and_waits(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._submit("button[type='submit']")
        page.wait_for_selector.assert_called_once_with("button[type='submit']", timeout=10000)
        page.click.assert_called_once_with("button[type='submit']")
        page.wait_for_load_state.assert_any_call("domcontentloaded")


class TestWaitAction:
    @pytest.mark.asyncio
    async def test_wait_sleeps(self):
        ex = _make_executor()
        start = asyncio.get_event_loop().time()
        await ex._wait(0.1)
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed >= 0.09


class TestVerifyAction:
    @pytest.mark.asyncio
    async def test_verify_text(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._verify({"text": "Welcome"})
        page.wait_for_selector.assert_called_once_with("text=Welcome")

    @pytest.mark.asyncio
    async def test_verify_selector(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._verify({"selector": "#dashboard"})
        page.wait_for_selector.assert_called_once_with("#dashboard")

    @pytest.mark.asyncio
    async def test_verify_both(self):
        page = AsyncMock()
        ex = _make_executor(page=page)
        await ex._verify({"text": "Hello", "selector": ".msg"})
        assert page.wait_for_selector.call_count == 2


class TestRunStep:
    @pytest.mark.asyncio
    async def test_unknown_action_raises(self):
        page = AsyncMock()
        sink = MagicMock()
        sink.log_event = MagicMock()
        sink.save_screenshot = MagicMock()
        ex = _make_executor(page=page, sink=sink)

        with pytest.raises(ValueError, match="Unknown action"):
            await ex.run_step(0, {"title": "Bad", "action": "fly", "target": ""}, "")

    @pytest.mark.asyncio
    async def test_step_logs_events(self):
        page = AsyncMock()
        sink = MagicMock()
        sink.log_event = MagicMock()
        ex = _make_executor(page=page, sink=sink)

        await ex.run_step(0, {"title": "Wait", "action": "wait", "data": {"seconds": 0.01}}, "")

        # Should have logged step_started and step_completed
        event_types = [call.args[0] for call in sink.log_event.call_args_list]
        assert "step_started" in event_types
        assert "step_completed" in event_types


class TestHookedExecution:
    @pytest.mark.asyncio
    async def test_before_step_hook_can_rewrite_step(self):
        class RewriteHook:
            def before_step(self, step, context):
                step["action"] = "fill"
                step["target"] = "#email"
                step["data"] = {"value": "hook@example.com"}
                return step

        page = AsyncMock()
        ex = _make_executor(page=page, hook_manager=HookManager([RewriteHook()]))

        await ex.run_step(0, {"title": "Hooked", "action": "custom_fill"}, "")

        page.fill.assert_called_once_with("#email", "hook@example.com")

    @pytest.mark.asyncio
    async def test_execute_step_hook_can_handle_custom_action(self):
        class CustomActionHook:
            async def execute_step(self, step, executor, context):
                if step.get("action") != "seed_login":
                    return None
                await executor._fill("#username", "alice")
                return {"status": "passed", "handled_by": "CustomActionHook"}

        page = AsyncMock()
        ex = _make_executor(page=page, hook_manager=HookManager([CustomActionHook()]))

        await ex.run_step(0, {"title": "Seed login", "action": "seed_login"}, "")

        page.fill.assert_called_once_with("#username", "alice")

    @pytest.mark.asyncio
    async def test_failure_hook_runs_on_step_error(self):
        failures = []

        class FailureHook:
            def on_step_failure(self, step, error, context):
                failures.append((step["title"], str(error)))

        page = AsyncMock()
        ex = _make_executor(page=page, hook_manager=HookManager([FailureHook()]))

        with pytest.raises(ValueError, match="Unknown action"):
            await ex.run_step(0, {"title": "Bad", "action": "nope"}, "")

        assert failures == [("Bad", "Unknown action: nope")]
