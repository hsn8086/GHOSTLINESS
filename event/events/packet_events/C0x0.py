from packet.packets.C0x0 import C0x0
from ..operation_events.handshake import HandshakeEvent
from ...base_event import BaseEvent


class C0x0Event(BaseEvent):
    def __init__(self, e_mgr, conn, server, packet: C0x0):
        super().__init__()
        self.server = server
        self.conn = conn
        self._e_mgr = e_mgr
        self.packet = packet

    def run(self):

        self._e_mgr.create_event(HandshakeEvent, (self.conn, self.server, *self.packet.read()))
