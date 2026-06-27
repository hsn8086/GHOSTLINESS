from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from ghostliness.config import GhostlinessConfig, write_default_config
from ghostliness.logging import configure_logging
from ghostliness.server import GhostlinessServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghostliness")
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="write a default ghostliness.toml")
    init.add_argument("--config", default="ghostliness.toml")

    run = subparsers.add_parser("run", help="run the server")
    run.add_argument("--config", default="ghostliness.toml")

    plugins = subparsers.add_parser("plugins", help="plugin commands")
    plugin_subparsers = plugins.add_subparsers(dest="plugin_command", required=True)
    plugin_subparsers.add_parser("list", help="list configured local plugins")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log_path = configure_logging(str(args.log_level))

    if args.command == "init":
        path = Path(args.config)
        if path.exists():
            parser.error(f"{path} already exists")
        write_default_config(path)
        print(f"wrote {path}")
        return 0

    if args.command == "run":
        config = GhostlinessConfig.load(Path(args.config))
        server = GhostlinessServer(config)
        print(f"logging to {log_path}")
        try:
            asyncio.run(server.serve_forever())
        except KeyboardInterrupt:
            return 130
        return 0

    if args.command == "plugins" and args.plugin_command == "list":
        config = GhostlinessConfig.load(Path("ghostliness.toml"))
        for plugin_path in config.plugins.paths:
            print(plugin_path)
        return 0

    parser.error("unknown command")
    return 2
