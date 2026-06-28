# Minecraft Server Parity Long-Term Plan

This document tracks the long-term plan for turning GHOSTLINESS into a practical
Minecraft Java server framework with behavior close to a vanilla server. The
target is not a byte-for-byte clone of Mojang's server internals. The target is a
clean Python implementation that can accept vanilla clients, preserve worlds,
run gameplay systems, and expose stable extension APIs.

Current baseline:

- Target client: Minecraft Java 26.2.
- Runtime: asyncio.
- Package manager: uv.
- Type checker: ty.
- Server state: login, configuration, play entry, flat chunks, movement,
  keepalive, initial block breaking, and JSON chunk persistence.

## Phase 0: Project Discipline

- [ ] Keep every protocol version in its own module and avoid leaking packet IDs
  into runtime logic.
- [ ] Keep `uv run pytest`, `uv run ruff check .`, and `uv run ty check` passing
  after every feature slice.
- [ ] Add a compatibility matrix documenting tested client versions, protocol
  numbers, and known broken flows.
- [ ] Add a changelog for protocol changes and save-format changes.
- [ ] Add `docs/` entries for server startup, client smoke testing, protocol
  debugging, and world reset procedures.
- [ ] Keep generated local worlds out of source control unless a fixture world is
  intentionally added under `tests/fixtures/`.
- [ ] Define stability labels for APIs: internal, experimental, plugin-stable.
- [ ] Add issue templates for protocol gaps, world bugs, and gameplay bugs.

## Phase 1: Protocol Foundation

- [ ] Generate or verify packet ID tables from the 26.2 client/server mapping
  data before adding new packets.
- [ ] Document the source used for every non-trivial packet layout: Mojang
  mapping, local `javap`, ProtocolLib, or live packet capture.
- [ ] Add protocol tests for every newly registered packet ID.
- [ ] Add decode tests using real client payloads whenever a packet was found in
  logs.
- [ ] Add encode tests for every clientbound packet used during login,
  configuration, play initialization, chunk streaming, inventory, entities, and
  gameplay feedback.
- [ ] Add structured unknown-packet logging with state, direction, packet ID,
  payload length, and raw payload hex capped to a safe size.
- [ ] Add an opt-in packet capture mode that writes framed serverbound and
  clientbound packets to a local debug file.
- [ ] Add a small protocol inspection command to list registered packets for a
  version.
- [ ] Separate packet schema definitions from packet encode/decode helpers once
  the 26.2 module becomes too large.
- [ ] Add a clear policy for unsupported packets: decode-and-ignore for harmless
  play packets, disconnect for malformed critical packets.
- [ ] Implement full serverbound play packet coverage for common vanilla client
  actions.
- [ ] Implement full clientbound play packet coverage required by world, entity,
  inventory, chat, and gameplay systems.
- [ ] Support compression thresholds exactly as vanilla clients expect.
- [ ] Support encryption and online-mode authentication when online mode is
  enabled.
- [ ] Add packet ordering tests for login, configuration, and enter-play flows.
- [ ] Add regression tests for all client disconnects discovered during manual
  testing.

## Phase 2: Login, Configuration, and Session Lifecycle

- [ ] Finish offline, online, and mixed authentication modes.
- [ ] Validate username and UUID handling against vanilla behavior.
- [ ] Implement secure profile property forwarding in online mode.
- [ ] Add server list ping favicon support.
- [ ] Add player capacity handling and friendly disconnect messages.
- [ ] Add duplicate-login handling for the same UUID.
- [ ] Add player session state transitions: handshaking, status, login,
  configuration, joining, spawned, loaded, disconnecting.
- [ ] Add server shutdown flow that disconnects players with a reason.
- [ ] Add configurable MOTD, icon, max players, view distance, simulation
  distance, compression, and online mode.
- [ ] Add per-player locale, view distance, skin parts, main hand, and chat
  preference tracking from client settings packets.
- [ ] Add keepalive timeout enforcement.
- [ ] Add teleport confirmation timeout and retry behavior.

## Phase 3: World Model and Storage

- [ ] Define a durable world save format with explicit format versioning.
- [ ] Add world metadata: seed, generator, spawn, time, weather, game rules, and
  dimension registry.
- [ ] Split chunk storage from chunk runtime state.
- [ ] Add chunk dirty tracking and periodic async saving.
- [ ] Add safe flush on player disconnect and server shutdown.
- [ ] Add backup and migration tooling for save format changes.
- [ ] Support negative chunk coordinates and region-style path partitioning.
- [ ] Add block state palettes instead of storing every block as full JSON.
- [ ] Store biomes per section.
- [ ] Store heightmaps persistently or rebuild them deterministically.
- [ ] Store block entities.
- [ ] Store entities.
- [ ] Store scheduled block ticks and fluid ticks.
- [ ] Store world border.
- [ ] Store scoreboard and team data.
- [ ] Add tests for chunk serialization, migration, corruption handling, and
  partial save recovery.

## Phase 4: Chunk Encoding and Streaming

- [ ] Keep chunk section encoding compliant with 26.2 palettes and biome data.
- [ ] Verify light masks and light arrays against vanilla expectations.
- [ ] Implement incremental chunk loading around the player.
- [ ] Implement chunk unload packets when the player moves out of range.
- [ ] Implement view-distance changes from settings or server config.
- [ ] Add chunk ticketing for spawn chunks and player chunks.
- [ ] Add a chunk send queue with backpressure.
- [ ] Honor client chunk batch feedback.
- [ ] Avoid blocking the event loop while generating or encoding chunks.
- [ ] Cache encoded chunks when safe and invalidate on block changes.
- [ ] Send block updates for single block changes.
- [ ] Send section or chunk updates for bulk changes.
- [ ] Add integration tests for initial chunk radius, movement across chunk
  borders, unload behavior, and changed block persistence.

## Phase 5: Terrain Generation

- [ ] Keep `void` generator for protocol debugging.
- [ ] Keep `flat` generator for deterministic smoke testing.
- [ ] Add configurable superflat layers.
- [ ] Add seeded heightmap terrain generator.
- [ ] Add biome assignment.
- [ ] Add bedrock, stone, dirt, grass, water, and simple cave rules.
- [ ] Add ore generation.
- [ ] Add trees and simple vegetation.
- [ ] Add structures only after chunk storage and block entities are stable.
- [ ] Define generator interface for plugins.
- [ ] Add deterministic tests for generator output by seed and chunk coordinate.
- [ ] Add visual/manual test procedure for generated worlds with vanilla client.

## Phase 6: Blocks and Fluids

- [ ] Build a block registry containing vanilla block IDs, state IDs, properties,
  hardness, collision, light emission, and item drops.
- [ ] Generate registry data from authoritative sources where practical.
- [ ] Implement block lookup by protocol state ID and namespaced ID.
- [ ] Implement block placement with face, cursor position, hand, and held item.
- [ ] Implement block breaking with survival timing and creative instant break.
- [ ] Implement correct acknowledgement and rollback behavior for rejected block
  changes.
- [ ] Implement block drops.
- [ ] Implement collision checks for placement and movement.
- [ ] Implement interactable blocks: doors, trapdoors, buttons, levers, chests,
  crafting tables, furnaces, beds, signs, and containers.
- [ ] Implement block entities for chests, signs, furnaces, and command-block-like
  future extension points.
- [ ] Implement fluids: water placement, flow, source updates, and basic lava.
- [ ] Implement scheduled block ticks.
- [ ] Add block update propagation to nearby players.
- [ ] Add tests for block state mapping, placement rules, breaking rules,
  persistence, and client-visible updates.

## Phase 7: Entity System

- [ ] Add an entity ID allocator and UUID mapping.
- [ ] Add base entity model: type, position, rotation, velocity, metadata,
  passengers, equipment, and tracked state.
- [ ] Add player entity spawning for other players.
- [ ] Add entity tracker by chunk and view distance.
- [ ] Add clientbound spawn, remove, move, rotate, teleport, metadata, velocity,
  equipment, and animation packets.
- [ ] Add serverbound interaction with entities.
- [ ] Add item entities.
- [ ] Add falling blocks.
- [ ] Add projectiles.
- [ ] Add basic mobs after the entity tracker is stable.
- [ ] Add entity persistence.
- [ ] Add entity collision and broad-phase lookup.
- [ ] Add tests for spawn/despawn visibility, movement replication, metadata
  updates, and persistence.

## Phase 8: Player Simulation

- [ ] Track position, rotation, on-ground state, pose, sprinting, sneaking, and
  swimming flags.
- [ ] Validate movement packets enough to prevent impossible coordinates and NaN
  values.
- [ ] Implement respawn flow.
- [ ] Implement health, food, saturation, experience, level, and game mode.
- [ ] Implement damage events and death screen.
- [ ] Implement spawn position and bed spawn.
- [ ] Implement inventory, hotbar, selected slot, offhand, armor, and cursor
  item.
- [ ] Implement item pickup.
- [ ] Implement item drop.
- [ ] Implement use item and use item on block.
- [ ] Implement basic combat interaction.
- [ ] Implement player abilities for survival, creative, spectator, and flying.
- [ ] Add anti-crash validation for invalid client movement and interaction
  packets.
- [ ] Add tests for player state updates, respawn, inventory mutation, and item
  use.

## Phase 9: Inventory, Items, and Menus

- [ ] Build item registry with vanilla item IDs, stack sizes, components, and
  basic use behavior.
- [ ] Implement slot encoding for 26.2 item stacks and components.
- [ ] Implement player inventory synchronization.
- [ ] Implement set selected hotbar slot.
- [ ] Implement click window handling.
- [ ] Implement carried cursor stack.
- [ ] Implement creative inventory actions.
- [ ] Implement containers: chest, crafting table, furnace, and player inventory.
- [ ] Implement menu open, close, slot update, carried item update, and property
  update packets.
- [ ] Implement crafting recipes.
- [ ] Implement smelting recipes.
- [ ] Implement item durability and damage.
- [ ] Add tests for slot encoding, inventory transactions, rejected clicks,
  crafting, and persistence.

## Phase 10: Chat, Commands, and Permissions

- [ ] Implement system chat and player chat paths.
- [ ] Implement command parsing with Brigadier-compatible suggestions where
  possible.
- [ ] Send command tree packets to the client.
- [ ] Add built-in commands: `help`, `list`, `say`, `tell`, `tp`, `gamemode`,
  `give`, `time`, `weather`, `stop`, `save-all`, and `reload`.
- [ ] Add console command input.
- [ ] Add permission model with operators and plugin-defined permissions.
- [ ] Add command events for plugins.
- [ ] Add message formatting and translatable components.
- [ ] Add signed chat support only if required for selected online-mode behavior.
- [ ] Add tests for command parsing, permission checks, command packet encoding,
  and plugin command registration.

## Phase 11: Game Rules, Time, Weather, and Difficulty

- [ ] Store and broadcast world time.
- [ ] Implement day-night cycle.
- [ ] Implement weather state and weather packets.
- [ ] Implement difficulty and difficulty lock.
- [ ] Add common game rules: keep inventory, do daylight cycle, do mob spawning,
  do tile drops, random tick speed, command block output, and spawn radius.
- [ ] Implement world border packets and enforcement.
- [ ] Add sleep voting or vanilla-like sleeping behavior.
- [ ] Add tests for game rule persistence and client-visible state updates.

## Phase 12: Vanilla Gameplay Systems

- [ ] Implement survival block breaking speed.
- [ ] Implement tool effectiveness.
- [ ] Implement harvest requirements.
- [ ] Implement basic damage sources.
- [ ] Implement fall damage.
- [ ] Implement drowning, fire, lava, and void damage.
- [ ] Implement hunger and natural regeneration.
- [ ] Implement experience orbs.
- [ ] Implement item drops from blocks and entities.
- [ ] Implement crafting and furnace loops.
- [ ] Implement redstone only after block updates and scheduled ticks are stable.
- [ ] Implement mobs after entity AI, navigation, and persistence foundations are
  ready.
- [ ] Add scenario tests for common survival loops: mine, pick up, craft, place,
  damage, die, respawn.

## Phase 13: Plugin Framework

- [ ] Stabilize plugin lifecycle: load, enable, disable, reload, error isolation.
- [ ] Add plugin metadata format.
- [ ] Add dependency ordering for plugins.
- [ ] Add event priority and cancellation semantics.
- [ ] Add packet listener API inspired by ProtocolLib while staying Pythonic.
- [ ] Add scheduler API for delayed and repeating tasks.
- [ ] Add command registration API.
- [ ] Add world API for block get/set, chunk access, and entity spawn.
- [ ] Add player API for chat, teleport, inventory, permissions, and game mode.
- [ ] Add persistent plugin data storage.
- [ ] Add sandbox or trust model documentation for local plugins.
- [ ] Add example plugins for welcome chat, command registration, block logging,
  and simple mini-game behavior.
- [ ] Add plugin integration tests with a fake connection.

## Phase 14: Performance and Concurrency

- [ ] Profile login, chunk encoding, packet encode/decode, and block changes.
- [ ] Keep expensive chunk generation and encoding off the hot network path.
- [ ] Add bounded queues for outgoing packets.
- [ ] Add per-connection write backpressure handling.
- [ ] Add metrics for tick time, packet counts, chunk queue length, online
  players, and save latency.
- [ ] Add runtime watchdog for event-loop stalls.
- [ ] Add memory limits for packet payloads and plugin-generated data.
- [ ] Add stress tests for many fake clients.
- [ ] Add benchmarks for VarInt, NBT, chunk encoding, and packet routing.
- [ ] Decide whether to introduce worker threads or processes for generation and
  compression after profiling.

## Phase 15: Testing Strategy

- [ ] Keep unit tests for protocol primitives and packet schemas.
- [ ] Keep unit tests for world model and storage.
- [ ] Add integration tests for full login-to-play handshake with fake streams.
- [ ] Add replay tests from captured client packet sequences.
- [ ] Add manual smoke test checklist for vanilla client.
- [ ] Add golden tests for encoded packets where protocol layouts are stable.
- [ ] Add fuzz tests for VarInt, frame decoding, NBT, and malformed packets.
- [ ] Add regression tests for every client log or server log failure fixed.
- [ ] Add a headless or scripted client test path if a reliable client automation
  option becomes available.
- [ ] Add CI job running pytest, ruff, ty, and package build through uv.

## Phase 16: Operations

- [ ] Add production config file schema documentation.
- [ ] Add log rotation and retention defaults.
- [ ] Add structured log fields for connection ID, player UUID, world, chunk,
  packet, and plugin.
- [ ] Add debug modes for protocol, world generation, chunk send, and plugin
  events.
- [ ] Add graceful shutdown and save-all command.
- [ ] Add crash report generation for unhandled exceptions.
- [ ] Add admin guide for upgrading server versions and migrating worlds.
- [ ] Add Docker or systemd examples only after the local workflow is stable.
- [ ] Add backup and restore documentation.

## Phase 17: Version Updates

- [ ] Track Mojang release versions and protocol numbers.
- [ ] Add a repeatable process for adding a new protocol version module.
- [ ] Extract packet registration order from the official client/server classes.
- [ ] Diff packet layouts across versions.
- [ ] Add compatibility tests for at least the current target version and the
  next target version during upgrades.
- [ ] Keep deprecated protocol modules until explicitly removed.
- [ ] Document save compatibility separately from protocol compatibility.

## Definition of Practical Vanilla Parity

- [ ] A vanilla client can join without custom mods.
- [ ] A player can move, look, break, place, pick up items, use inventory, chat,
  run commands, die, respawn, and reconnect.
- [ ] Chunks load and unload correctly while walking.
- [ ] World changes persist across restarts.
- [ ] Multiple players can see each other and shared world changes.
- [ ] Core survival loop works: gather blocks, craft basic items, place blocks,
  take damage, and recover or die.
- [ ] Plugins can observe and modify common gameplay without patching internals.
- [ ] Logs and packet captures are good enough to debug client disconnects.
- [ ] Tests cover protocol, world, runtime, storage, and plugin behavior.

## Near-Term Recommended Order

- [ ] Finish common serverbound play packet coverage discovered by client logs.
- [ ] Add right-click block placement using the current flat world.
- [ ] Add selected hotbar slot and minimal inventory state.
- [ ] Add item stack encode/decode for held items.
- [ ] Add chunk unload and moving chunk window.
- [ ] Add basic block registry generated or verified from official data.
- [ ] Add player-to-player visibility and entity spawn packets.
- [ ] Add save format versioning before expanding persistence further.
- [ ] Add replay tests from the packet sequences already seen during local 26.2
  client testing.
