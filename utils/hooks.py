import asyncio
import importlib
import importlib.util
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Optional

logger = logging.getLogger(__name__)


class BaseHook:
    """Base class for optional framework hooks."""

    name = "base"


class HookManager:
    """Loads and executes user-provided hooks for generation and execution flows."""

    def __init__(self, hooks: Optional[Iterable[Any]] = None):
        self.hooks = [hook for hook in (hooks or []) if hook is not None]

    @classmethod
    def load(cls, hook_specs: Optional[str]) -> "HookManager":
        if not hook_specs:
            return cls()

        hooks: List[Any] = []
        for spec in [part.strip() for part in hook_specs.split(",") if part.strip()]:
            module = cls._load_module(spec)
            hooks.extend(cls._extract_hooks(module, spec))

        return cls(hooks)

    @staticmethod
    def _load_module(spec: str) -> ModuleType:
        path = Path(spec)
        if path.exists():
            module_name = f"aiwebtester_hook_{path.stem}_{abs(hash(str(path.resolve())))}"
            module_spec = importlib.util.spec_from_file_location(module_name, path)
            if module_spec is None or module_spec.loader is None:
                raise RuntimeError(f"Could not load hooks from file: {spec}")
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            return module

        return importlib.import_module(spec)

    @classmethod
    def _extract_hooks(cls, module: ModuleType, spec: str) -> List[Any]:
        if hasattr(module, "get_hooks"):
            hook_items = module.get_hooks()
        elif hasattr(module, "HOOKS"):
            hook_items = getattr(module, "HOOKS")
        elif hasattr(module, "hooks"):
            hook_items = getattr(module, "hooks")
        elif hasattr(module, "hook"):
            hook_items = [getattr(module, "hook")]
        else:
            raise RuntimeError(
                f"No hooks found in '{spec}'. Export HOOKS, hooks, hook, or get_hooks()."
            )

        if not isinstance(hook_items, (list, tuple)):
            hook_items = [hook_items]

        normalized = []
        for item in hook_items:
            if isinstance(item, type):
                normalized.append(item())
            else:
                normalized.append(item)
        return normalized

    async def _call(self, hook: Any, method_name: str, *args: Any) -> Any:
        method = getattr(hook, method_name, None)
        if method is None:
            return None

        result = method(*args)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def transform(self, method_name: str, value: Any, context: dict) -> Any:
        for hook in self.hooks:
            result = await self._call(hook, method_name, value, context)
            if result is not None:
                value = result
        return value

    async def notify(self, method_name: str, *args: Any) -> None:
        for hook in self.hooks:
            await self._call(hook, method_name, *args)

    async def execute_step(self, step: dict, executor: Any, context: dict) -> Any:
        for hook in self.hooks:
            result = await self._call(hook, "execute_step", step, executor, context)
            if result is not None:
                return result
        return None

    def has_hooks(self) -> bool:
        return bool(self.hooks)
