from packet.packet_utils.packet_process import S0x0
from ...base_event import BaseEvent

class StatusRequestEvent(BaseEvent):
    def __init__(self, conn, server):
        super().__init__()
        self.server = server
        self.conn = conn
        self.ver = ver
        self.addr = addr
        self.port = port
        self.state = state

    def run(self):
        self.conn.send(S0x0.generate_data(self.server, self.ver).__bytes__())
