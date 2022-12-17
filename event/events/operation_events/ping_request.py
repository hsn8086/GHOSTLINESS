from data_types import Long
from packet.packet_utils.packet_data import PacketGenerator
from packet.packets.status.S0x1 import S0x1
from ...base_event import BaseEvent


class PingRequestEvent(BaseEvent):
    def __init__(self, conn, server, payload):
        super().__init__()
        self.server = server
        self.conn = conn
        self.payload = payload

    def run(self):
        p = S0x1()
        p += Long(self.payload)
        self.conn.send(bytes(p))
