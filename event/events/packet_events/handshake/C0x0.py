from event.base_event import BaseEvent
from event.events.operation_events.handshake import HandshakeEvent
from packet.packets.handshake.C0x0 import C0x0


class HandshakeC0x0Event(BaseEvent):
    def __init__(self, e_mgr, conn, addr, server, packet: C0x0):
        super().__init__()
        self.server = server
        self.conn = conn
        self.addr = addr
        self._e_mgr = e_mgr
        self.packet = packet

    def run(self):
        self._e_mgr.create_event(HandshakeEvent, (self.conn, self.addr, self.server, * self.packet.read()))
