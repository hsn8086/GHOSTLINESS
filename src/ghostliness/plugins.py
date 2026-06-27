from __future__ import annotations

import importlib.metadata
import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

from ghostliness.events import EventBus
from ghostliness.protocol.manager import ProtocolManager

if TYPE_CHECKING:
    from ghostliness.server.core import GhostlinessServer


@dataclass(slots=True)
class PluginContext:
    server: GhostlinessServer
    events: EventBus
    protocol: ProtocolManager

    @property
    def runtime(self):
        return self.server.runtime

    @property
    def world(self):
        return self.server.world


@dataclass(slots=True)
class LoadedPlugin:
    name: str
    module: ModuleType


class PluginLoader:
    def __init__(self, server: GhostlinessServer) -> None:
        self.server = server
        self.loaded: list[LoadedPlugin] = []

    async def load_all(self, paths: tuple[str, ...]) -> None:
        ctx = PluginContext(
            server=self.server,
            events=self.server.events,
            protocol=self.server.protocol,
        )
        for entry_point in importlib.metadata.entry_points(group="ghostliness.plugins"):
            plugin = LoadedPlugin(entry_point.name, entry_point.load())
            await self._enable(plugin, ctx)
        for raw_path in paths:
            plugin = self._load_path(Path(raw_path))
            await self._enable(plugin, ctx)

    async def disable_all(self) -> None:
        ctx = PluginContext(
            server=self.server,
            events=self.server.events,
            protocol=self.server.protocol,
        )
        for plugin in reversed(self.loaded):
            hook = getattr(plugin.module, "on_disable", None)
            if hook is not None:
                await _maybe_await(hook(ctx))

    def _load_path(self, path: Path) -> LoadedPlugin:
        if not path.exists():
            raise FileNotFoundError(path)
        module_name = f"ghostliness_local_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load plugin from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return LoadedPlugin(path.stem, module)

    async def _enable(self, plugin: LoadedPlugin, ctx: PluginContext) -> None:
        load = getattr(plugin.module, "on_load", None)
        if load is not None:
            await _maybe_await(load(ctx))
        enable = getattr(plugin.module, "on_enable", None)
        if enable is not None:
            await _maybe_await(enable(ctx))
        self.loaded.append(plugin)


async def _maybe_await(value: Any) -> None:
    if inspect.isawaitable(value):
        await value
