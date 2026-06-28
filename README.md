# GHOSTLINESS

GHOSTLINESS is an experimental Minecraft Java Edition server framework written
in Python. It is a ground-up asyncio server rewrite with a versioned protocol
registry, a small runtime simulation, world storage, and a ProtocolLib-inspired
packet listener API for plugins.

The project is not a production-ready vanilla replacement yet. It is currently
useful for protocol research, client smoke tests, plugin API experiments, and
incremental server gameplay work.

## Current Status

- Minecraft target: Java Edition `26.2`, protocol `776`
- Runtime: `asyncio`
- Package manager: `uv`
- Python: `>=3.12`
- Type checker: `ty`
- Logging: `loguru`, writing to `logs/ghostliness.log`
- Auth modes: `offline`, `online`, or `both`
- World generators: `void` and `flat`
- World storage: GHOSTLINESS JSON chunks

Implemented gameplay is intentionally narrow but test-covered:

- handshake, status, login, configuration, and play entry
- chunk streaming for void and flat worlds
- player position, look, input, sprint/sneak state, and multiplayer visibility
- basic block breaking, placement, persistence, and rollback
- hotbar-only inventory sync
- item entities, block drops, player item drop, pickup, merge, despawn, and
  simple current-world physics
- local plugin loading and packet listeners

## Quick Start

Install dependencies:

```bash
uv sync
```

Write a default config:

```bash
uv run ghostliness init
```

For an easier client smoke test, edit `ghostliness.toml` and use a flat world:

```toml
[world]
generator = "flat"
```

Start the server:

```bash
uv run ghostliness run --config ghostliness.toml
```

Then join from a Minecraft Java `26.2` client at:

```text
127.0.0.1:25565
```

The default config binds to localhost and uses offline auth, so it is intended
for local development only.

## Configuration

`ghostliness init` writes `ghostliness.toml` from
`ghostliness.example.toml`.

Important fields:

```toml
[server]
host = "127.0.0.1"
port = 25565
motd = "A GHOSTLINESS server"
max_players = 20
view_distance = 2

[auth]
mode = "offline"

[world]
name = "world"
path = "worlds/world"
storage = "ghostliness"
generator = "void"

[plugins]
enabled = true
paths = []
```

Use `generator = "void"` for protocol/debug work and `generator = "flat"` for
basic in-client movement, block, and item testing.

## Development

Run the full validation set:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest
UV_CACHE_DIR=.uv-cache uv run ruff check .
UV_CACHE_DIR=.uv-cache uv run ty check
```

Useful focused test commands:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_framing.py
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_runtime.py
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_entities.py
```

The protocol layer lives in `src/ghostliness/protocol/versions/`. Packet IDs,
packet codecs, entity type IDs, and metadata serializer IDs should be kept
version-local there.

## Plugins

Plugins can be loaded from Python package entry points in the
`ghostliness.plugins` group or from local files listed in `ghostliness.toml`.

Example local plugin:

```python
from ghostliness.protocol.registry import PacketDirection


async def on_enable(ctx):
    ctx.protocol.add_packet_listener(log_packet, direction=PacketDirection.SERVERBOUND)


async def log_packet(packet):
    print(f"serverbound {packet.name}: {dict(packet.fields)}")
```

Enable it:

```toml
[plugins]
enabled = true
paths = ["examples/plugins/packet_logger.py"]
```

List configured local plugins:

```bash
uv run ghostliness plugins list
```

## Repository Layout

- `src/ghostliness/cli.py`: command line entry point
- `src/ghostliness/server/`: server core, connections, runtime, player/entity
  state
- `src/ghostliness/protocol/`: packet framing, registry, protocol codecs
- `src/ghostliness/world.py`: in-memory chunk and world model
- `src/ghostliness/world_storage.py`: chunk persistence
- `src/ghostliness/items.py` and `src/ghostliness/blocks.py`: current item and
  block registries
- `tests/`: protocol, runtime, world, inventory, and entity tests
- `docs/minecraft_server_parity_plan.md`: long-term parity roadmap

## Known Limits

GHOSTLINESS currently implements only a tiny subset of vanilla behavior. Major
missing areas include full registries, survival timing, movement collision for
players, full inventory/container transactions, mobs, redstone, fluids,
lighting updates, Anvil world storage, commands, permissions, and entity
persistence.

Treat new protocol or gameplay work as version-sensitive. Prefer verifying
packet layouts against the official client/server classes or another
authoritative source before changing protocol constants.
