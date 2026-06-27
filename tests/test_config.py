from ghostliness.config import GhostlinessConfig


def test_missing_config_uses_defaults(tmp_path):
    config = GhostlinessConfig.load(tmp_path / "missing.toml")
    assert config.server.host == "127.0.0.1"
    assert config.auth.mode == "offline"
    assert config.world.name == "world"
    assert config.world.path == "worlds/world"
    assert config.world.storage == "ghostliness"


def test_config_loads_plugin_paths(tmp_path):
    path = tmp_path / "ghostliness.toml"
    path.write_text(
        """
[plugins]
paths = ["examples/plugins/packet_logger.py"]
""",
        encoding="utf-8",
    )

    config = GhostlinessConfig.load(path)

    assert config.plugins.paths == ("examples/plugins/packet_logger.py",)


def test_config_loads_world_storage_settings(tmp_path):
    path = tmp_path / "ghostliness.toml"
    path.write_text(
        """
[world]
name = "dev"
path = "worlds/dev"
storage = "ghostliness"
generator = "flat"
""",
        encoding="utf-8",
    )

    config = GhostlinessConfig.load(path)

    assert config.world.name == "dev"
    assert config.world.path == "worlds/dev"
    assert config.world.storage == "ghostliness"
    assert config.world.generator == "flat"
