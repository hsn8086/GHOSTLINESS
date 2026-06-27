from ghostliness.cli import main


def test_cli_init_writes_config(tmp_path):
    config_path = tmp_path / "ghostliness.toml"

    assert main(["init", "--config", str(config_path)]) == 0

    assert config_path.exists()
    assert "A GHOSTLINESS server" in config_path.read_text(encoding="utf-8")
