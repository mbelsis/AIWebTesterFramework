from pathlib import Path

import pytest

from orchestrator.test_plan_generator import TestPlanGenerator as PlanGenerator
from utils.hooks import HookManager


class TestHookManager:
    @pytest.mark.asyncio
    async def test_transform_applies_sync_and_async_hooks_in_order(self):
        class FirstHook:
            def after_generate(self, plan, context):
                plan["name"] = "first"
                return plan

        class SecondHook:
            async def after_generate(self, plan, context):
                plan["description"] = context["marker"]
                return plan

        manager = HookManager([FirstHook(), SecondHook()])
        plan = await manager.transform("after_generate", {"name": "base"}, {"marker": "second"})

        assert plan["name"] == "first"
        assert plan["description"] == "second"

    def test_loads_hooks_from_python_file(self):
        hook_file = Path.cwd() / "tests" / "fixtures" / "sample_hooks.py"
        manager = HookManager.load(str(hook_file))

        assert manager.has_hooks() is True


class TestGeneratorHooks:
    @pytest.mark.asyncio
    async def test_environment_hook_can_modify_generated_env(self):
        class EnvHook:
            async def after_generate_env(self, env_config, context):
                env_config["credentials"]["username"] = "hooked-user"
                env_config["settings"]["headful"] = False
                return env_config

        generator = PlanGenerator(run_id="test-run", hook_manager=HookManager([EnvHook()]))
        env_config = await generator._generate_environment_config(
            "https://example.com/login",
            {
                "title": "Login",
                "structure": {"page_type": "login", "forms": []},
                "elements": [],
            },
        )

        assert env_config["credentials"]["username"] == "hooked-user"
        assert env_config["settings"]["headful"] is False
