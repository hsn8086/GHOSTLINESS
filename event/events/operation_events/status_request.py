from packet.packet_utils.packet_process import S0x0
from ...base_event import BaseEvent


class StatusRequestEvent(BaseEvent):
    def __init__(self, conn, caddr, server):
        super().__init__()
        self.server = server
        self.conn = conn
        self.caddr = caddr

    def run(self):
        self.conn.send(S0x0.generate_data(self.server, self.server.client_ver_dict[str(self.caddr)]).__bytes__())
