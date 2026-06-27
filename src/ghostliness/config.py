from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 25565
    motd: str = "A GHOSTLINESS server"
    max_players: int = 20
    view_distance: int = 2
    online_mode: bool = False


@dataclass(frozen=True, slots=True)
class AuthConfig:
    mode: str = "offline"


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    compression_threshold: int = -1


@dataclass(frozen=True, slots=True)
class WorldConfig:
    name: str = "world"
    path: str = "worlds/world"
    storage: str = "ghostliness"
    generator: str = "void"


@dataclass(frozen=True, slots=True)
class PluginConfig:
    enabled: bool = True
    paths: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class GhostlinessConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)

    @classmethod
    def load(cls, path: Path) -> GhostlinessConfig:
        if not path.exists():
            return cls()
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        server = ServerConfig(**data.get("server", {}))
        auth = AuthConfig(**data.get("auth", {}))
        network = NetworkConfig(**data.get("network", {}))
        world = WorldConfig(**data.get("world", {}))
        plugin_data = data.get("plugins", {})
        plugins = PluginConfig(
            enabled=bool(plugin_data.get("enabled", True)),
            paths=tuple(str(path) for path in plugin_data.get("paths", [])),
        )
        return cls(server=server, auth=auth, network=network, world=world, plugins=plugins)


def write_default_config(path: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "ghostliness.example.toml"
    if source.exists():
        shutil.copyfile(source, path)
        return
    path.write_text(
        """[server]
host = "127.0.0.1"
port = 25565
motd = "A GHOSTLINESS server"
max_players = 20
view_distance = 2

[auth]
mode = "offline"

[network]
compression_threshold = -1

[world]
name = "world"
path = "worlds/world"
storage = "ghostliness"
generator = "void"

[plugins]
enabled = true
paths = []
""",
        encoding="utf-8",
    )
