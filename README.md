# GHOSTLINESS

GHOSTLINESS is a Python Minecraft Java Edition server framework.

This rewrite intentionally replaces the old proof-of-concept code with a `uv` managed package, an asyncio server core, a data-driven protocol layer, and a ProtocolLib-inspired packet listener API for Python plugins.

## Current target

- Minecraft Java Edition release target: `26.2`
- Server mode: framework-first playable skeleton
- Auth modes: `offline`, `online`, or `both`
- Runtime model: `asyncio`
- Package manager: `uv`

The protocol registry is versioned so packet IDs and schemas can be updated in one place as the official game releases change.

## Commands

```bash
uv sync
uv run ghostliness init
uv run ghostliness run --config ghostliness.toml
uv run pytest
uv run ruff check .
uv run ty check
```

For a local client smoke test, set `[world] generator = "flat"` in
`ghostliness.toml`, then start the server and join `127.0.0.1:25565` with a
Minecraft Java 26.2 client. The default `void` generator is still useful for
protocol debugging because it sends empty terrain.

## Plugin shape

Plugins may be loaded from Python entry points in the `ghostliness.plugins` group or from local plugin files configured in `ghostliness.toml`.

```python
async def on_enable(ctx):
    ctx.events.subscribe("player_join", handle_join)

async def handle_join(event):
    await event.player.send_chat("Welcome")
```
