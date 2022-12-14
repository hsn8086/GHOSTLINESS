import socket

from ...base_event import BaseEvent


class HandshakeEvent(BaseEvent):
    def __init__(self, conn, caddr, server, ver, addr, port, state):
        super().__init__()
        self.server = server
        self.conn = conn
        self.ver = ver
        self.addr = addr
        self.caddr = caddr
        self.port = port
        self.state = state

    def run(self):
        self.server.client_ver_dict[str(self.caddr)] = self.ver
        if self.state == 1:
            self.conn: socket.socket
            # self.conn.
            # self.conn.send(S0x0.generate_data(self.server, self.ver).__bytes__())
            self.server.client_state_dict[str(self.caddr)] = 'status'

        elif self.state == 2:
            # print(','.join([hex(int(i)) for i in bytes(S2C0x01.generate_data(self))]))
            # print(str(bytes(S2C0x01.generate_data(self))))
            # pk = S0x1.generate_data(self.server)
            self.server.client_state_dict[str(self.caddr)] = 'login'
            '''print('str1', pk.get_str())
            print('ba1', pk.get_byte_array())
            # print('pb1',[int(i ) for i in self.pub])

            print('ba2', pk.get_byte_array())'''
            # p1 = packet.packets.login.S0x1.S0x1()
            # p1.from_raw_packet(S0x1.generate_data(self.server))
            # print(p1)
            # self.conn.send(p1.__bytes__())
