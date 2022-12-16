import importlib
import logging

from packet.raw_packet import RawPacket
from ..base_event import BaseEvent


class PacketRecvEvent(BaseEvent):
    def __init__(self, e_mgr, conn, server, raw_packet: RawPacket):
        super().__init__()
        self.conn = conn
        self.server = server
        try:
            packet_module = importlib.import_module(f'packet.packets.C0x{str(raw_packet.id)}')
            self.packet = getattr(packet_module, f'C0x{str(raw_packet.id)}')()
            self.packet.from_raw_packet(raw_packet)
            logging.getLogger(__name__).debug(self.packet)
            event_module = importlib.import_module(f'event.events.packet_events.C0x{str(self.packet.packet_id)}')
            self.event = getattr(event_module, f'C0x{str(self.packet.packet_id)}Event')
            self._e_mgr = e_mgr
        except:
            self.cancel = True

    def run(self):
        self._e_mgr.create_event(self.event, (self._e_mgr, self.conn, self.server, self.packet))
