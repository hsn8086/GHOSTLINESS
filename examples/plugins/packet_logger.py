from ghostliness.protocol.registry import PacketDirection


async def on_enable(ctx):
    ctx.protocol.add_packet_listener(log_packet, direction=PacketDirection.SERVERBOUND)


async def log_packet(packet):
    print(f"serverbound {packet.name}: {dict(packet.fields)}")
