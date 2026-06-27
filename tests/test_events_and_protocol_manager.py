from ghostliness.events import EventBus
from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.manager import ListenerPriority, ProtocolManager
from ghostliness.protocol.registry import PacketDirection
from ghostliness.protocol.versions import JAVA_26_2


async def test_event_bus_orders_by_priority():
    calls = []
    bus = EventBus()
    bus.subscribe("x", lambda event: calls.append(("low", event)), priority=0)
    bus.subscribe("x", lambda event: calls.append(("high", event)), priority=10)

    await bus.publish("x", "event")

    assert calls == [("high", "event"), ("low", "event")]


async def test_protocol_manager_can_modify_and_cancel_packet():
    manager = ProtocolManager()
    packet = PacketContainer(JAVA_26_2.get_by_name("clientbound.system_chat"), {"content": {}})

    async def mutate(container):
        container.fields["content"] = {"text": "changed"}

    def cancel(container):
        container.cancelled = True

    manager.add_packet_listener(mutate, direction=PacketDirection.CLIENTBOUND)
    manager.add_packet_listener(
        cancel,
        direction=PacketDirection.CLIENTBOUND,
        priority=ListenerPriority.LOW,
    )

    result = await manager.notify(packet, PacketDirection.CLIENTBOUND)

    assert result.fields["content"] == {"text": "changed"}
    assert result.cancelled is True
