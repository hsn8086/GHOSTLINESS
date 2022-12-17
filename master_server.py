import base64
import os.path
import threading
from socket import socket
from threading import Thread

from OpenSSL import crypto
from OpenSSL.crypto import *

from event.event_manager import EventManager
from event.events.packet_event import PacketRecvEvent
from packet.raw_packet import RawPacket
from plugin_manager import *


class MasterServer:
    def __init__(self, name='GHOSTLINESS', motd='A Minecraft Server.', host='127.0.0.1', port=25565, max_players=20):
        self.host = host
        self.port = port
        self.motd = motd
        self.name = name
        self.max_players = max_players
        self.current_players = 0
        self.s = socket()

        self.client_state_dict = {}
        self.client_ver_dict={}

        self.logger = logging.getLogger(__name__)
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
        self.event_manager = EventManager()
        self.plugin_manager = PluginManger(self)

    def start(self):
        self.logger.info('Loading plugins...')
        self.plugin_manager.load_all()
        self.logger.info('Plugin all loaded!')

        self.logger.info(f"Server started on {self.host}:{self.port}.")
        t = Thread(target=self.listen_thread, name=self.name, daemon=True)
        t.start()
        loop = True
        while loop:
            try:
                t.join(timeout=1)
            except KeyboardInterrupt:
                loop = False
        self.stop()

    def stop(self):
        self.logger.info('server stopped.')

    def listen_thread(self):
        self.s.bind((self.host, self.port))
        self.s.listen(2000)
        while True:
            conn, addr = self.s.accept()

            t = threading.Thread(target=self.client_recv_thread, args=(conn, addr), daemon=True)
            t.start()

    def client_recv_thread(self, conn, addr):
        loop = True
        while loop:
            if str(addr) not in self.client_state_dict:
                self.client_state_dict[str(addr)] = 'handshake'
            try:
                recv_packet = RawPacket(conn)
                self.event_manager.create_event(PacketRecvEvent, (self.event_manager, conn, addr, self, recv_packet))
                # self.packet_process(conn, addr, recv_packet)
                # print('[{}:{}] {}'.format(addr[0], addr[1], ','.join([hex(int(i)) for i in recv_packet.__bytes__()])))
            except ConnectionAbortedError:
                loop = False
