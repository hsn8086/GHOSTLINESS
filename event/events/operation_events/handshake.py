import json

from event.base_event import BaseEvent
from packet.packet_utils.packet_process import S0x0, S0x1



class HandshakeEvent(BaseEvent):
    def __init__(self, conn,server, ver, addr, port, state):
        super().__init__()
        self.server=server
        self.conn = conn
        self.ver = ver
        self.addr = addr
        self.port = port
        self.state = state

    def run(self):
        if self.state == 1:
            self.conn.send(S0x0.generate_data(self.server, self.ver).__bytes__())
        elif self.state == 2:
            # print(','.join([hex(int(i)) for i in bytes(S2C0x01.generate_data(self))]))
            # print(str(bytes(S2C0x01.generate_data(self))))
            pk = S0x1.generate_data(self.server)

            '''print('str1', pk.get_str())
            print('ba1', pk.get_byte_array())
            # print('pb1',[int(i ) for i in self.pub])

            print('ba2', pk.get_byte_array())'''

            self.conn.send(bytes(S0x1.generate_data(self)))
