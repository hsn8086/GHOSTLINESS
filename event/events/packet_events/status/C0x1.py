from packet.packets.handshake.C0x0 import C0x0
from event.events.operation_events.ping_request import PingRequestEvent
from event.base_event import BaseEvent


class StatusC0x1Event(BaseEvent):
    def __init__(self, e_mgr, conn, addr, server, packet: C0x0):
        super().__init__()
        self.server = server
        self.conn = conn
        self.addr = addr
        self._e_mgr = e_mgr
        self.packet = packet

    def run(self):
        self._e_mgr.create_event(PingRequestEvent, (self.conn, self.server, *self.packet.read()))
