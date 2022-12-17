from packet.packets.handshake.C0x0 import C0x0
from event.events.operation_events.status_request import StatusRequestEvent
from event.base_event import BaseEvent


class StatusC0x0Event(BaseEvent):
    def __init__(self, e_mgr, conn, addr, server, packet: C0x0):
        super().__init__()
        self.server = server
        self.conn = conn
        self._e_mgr = e_mgr
        self.packet = packet
        self.addr = addr

    def run(self):
        self._e_mgr.create_event(StatusRequestEvent, (self.conn, self.addr,self.server, *self.packet.read()))
