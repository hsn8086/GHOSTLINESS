from ghostliness.config import GhostlinessConfig


def test_missing_config_uses_defaults(tmp_path):
    config = GhostlinessConfig.load(tmp_path / "missing.toml")
    assert config.server.host == "127.0.0.1"
    assert config.auth.mode == "offline"


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
