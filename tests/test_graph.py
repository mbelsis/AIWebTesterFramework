"""
Tests for TestGraph — the core test execution orchestrator.
Uses mocks to test the orchestration logic without needing a real browser.
"""

import pytest
import yaml
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator.graph import TestGraph


@pytest.fixture
def work_dir():
    """Create a temp directory that works on Windows."""
    d = Path(tempfile.mkdtemp(prefix="aitest_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def plan_file(work_dir):
    plan = {
        "name": "Test Plan",
        "description": "Unit test plan",
        "steps": [
            {"title": "Wait briefly", "action": "wait", "data": {"seconds": 0.01}},
        ],
    }
    p = work_dir / "plan.yaml"
    p.write_text(yaml.dump(plan))
    return str(p)


@pytest.fixture
def env_file(work_dir):
    env = {
        "name": "Test Env",
        "target": {"base_url": "http://127.0.0.1:5000", "timeout": 5000},
        "settings": {"headful": False, "slow_mo": 0, "video": False},
    }
    p = work_dir / "env.yaml"
    p.write_text(yaml.dump(env))
    return str(p)


@pytest.fixture
def artifacts_dir(work_dir):
    d = work_dir / "artifacts"
    d.mkdir()
    return str(d)


class TestGraphLoadYaml:
    def test_loads_valid_yaml(self, plan_file, artifacts_dir):
        graph = TestGraph(artifacts_dir, headful=False, control_room=None, run_id="test")
        data = graph._load_yaml(plan_file)
        assert data["name"] == "Test Plan"
        assert len(data["steps"]) == 1

    def test_raises_on_empty_yaml(self, work_dir, artifacts_dir):
        empty = work_dir / "empty.yaml"
        empty.write_text("")
        graph = TestGraph(artifacts_dir, headful=False, control_room=None, run_id="test")
        with pytest.raises(ValueError, match="empty or invalid"):
            graph._load_yaml(str(empty))

    def test_raises_on_missing_file(self, artifacts_dir):
        graph = TestGraph(artifacts_dir, headful=False, control_room=None, run_id="test")
        with pytest.raises(FileNotFoundError):
            graph._load_yaml("/nonexistent/path.yaml")


class TestGraphRun:
    @pytest.mark.asyncio
    async def test_run_produces_result_dict(self, plan_file, env_file, artifacts_dir):
        """Test that run() returns a properly structured result, using mocked browser."""
        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"png")
        mock_page.on = MagicMock()  # Use sync MagicMock for event listeners
        mock_page.url = "http://localhost:5000"
        mock_page.evaluate = AsyncMock(return_value="")  # Return string not coroutine
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()

        with patch("browser.context.create_context") as mock_create:
            mock_create.return_value = (
                mock_playwright, mock_browser, mock_context,
                mock_page, None, None,
            )

            with patch("browser.context.finalize_video_and_trace") as mock_finalize:
                mock_finalize.return_value = {"status": "success", "errors": [], "artifacts": {}}

                # Disable watchdog to avoid serialization issues with mock page
                with patch("orchestrator.executor.WATCHDOG_AVAILABLE", False):
                    graph = TestGraph(artifacts_dir, headful=False, control_room=None, run_id="test-run")
                    result = await graph.run(plan_file, env_file)

        assert result is not None
        assert result["status"] == "passed"
        assert result["run_id"] == "test-run"
        assert result["total_steps"] == 1
        assert "duration_seconds" in result
