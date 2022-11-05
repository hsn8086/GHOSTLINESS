from threading import Thread

import rsa

from packet.packet_data import *
from packet.packet_process import *
from plugin_manager import *


class Server:
    def __init__(self, name='GHOSTLINESS', motd='A Minecraft Server.', host='127.0.0.1', port=25565, max_players=20):
        self.host = host
        self.port = port
        self.motd = motd
        self.name = name
        self.max_players = max_players
        self.current_players = 0
        self.s = socket()
        self.plugins = PluginManger()
        (public_key, private_key) = rsa.newkeys(1024)
        self.pub = public_key.save_pkcs1('DER')
        self.pri = private_key.save_pkcs1('DER')

    def start(self):
        print("Server started on {}:{}".format(self.host, self.port))
        Thread(target=self.listen_thread, name=self.name, daemon=False).start()

    def stop(self):
        print('server stopped\nname:{}'.format(self.name))

    def listen_thread(self):
        self.s.bind((self.host, self.port))
        self.s.listen(self.max_players)
        while True:
            conn, addr = self.s.accept()
            recv_packet = Packet(conn)
            self.packet_process(conn, addr, recv_packet)
            print('[{}:{}] {}'.format(addr[0], addr[1], ','.join([hex(int(i)) for i in recv_packet.__bytes__()])))

    def packet_process(self, conn, addr, packet: Packet):
        if packet.id.__int__() == 0:
            address, port, status, ver = C2S0x00.get_data(packet)
            packet = S2C0x00.generate_data(self, ver)
            self.plugins.run('on_handshake', conn, addr, int(ver), status, packet)
            if status == 1:
                conn.send(packet.__bytes__())
            elif status == 2:
                conn.send(bytes(S2C0x01.generate_data(self)))
