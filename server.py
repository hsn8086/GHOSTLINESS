import base64
import os.path
from threading import Thread

from OpenSSL import crypto
from OpenSSL.crypto import *

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
        pk = crypto.PKey()
        pk.generate_key(TYPE_RSA, 1024)

        self.pub = dump_publickey(FILETYPE_ASN1, pk)
        self.pri = dump_privatekey(FILETYPE_ASN1, pk)
        '''(public_key, private_key) = rsa.newkeys(1024, poolsize=8)
        self.pub = public_key.save_pkcs1('DER')
        self.pri = private_key.save_pkcs1('DER')'''

        if os.path.exists('icon.png'):
            with open('icon.png', 'rb') as f:
                self.icon = base64.b64encode(f.read()).decode('utf8')
        else:
            self.icon = ''

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

            self.plugins.run('on_handshake', conn, addr, int(ver), status, packet)
            if status == 1:
                conn.send(S2C0x00.generate_data(self, ver).__bytes__())
            elif status == 2:
                pass
                # print(','.join([hex(int(i)) for i in bytes(S2C0x01.generate_data(self))]))
                # print(str(bytes(S2C0x01.generate_data(self))))
                '''pk=S2C0x01.generate_data(self)
                print('str1',pk.get_str())
                print('ba1',pk.get_byte_array())
                print('pb1',[int(i ) for i in self.pub])

                print('ba2',pk.get_byte_array())'''
                conn.send(bytes(S2C0x01.generate_data(self)))
