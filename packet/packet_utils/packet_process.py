import json
import random

from data_types import ByteArray
from .packet_data import PacketGenerator
from ..raw_packet import RawPacket


class C0x0:
    @staticmethod
    def get_data(packet: RawPacket):
        # Handshake
        # Get the protocol version

        ver = packet.get_varint()

        # Get the address
        address = packet.get_str()

        # Get the port

        port = packet.get_int()

        # Get the status
        status = int(packet.get_byte())
        return address, port, status, ver


class S0x0:
    @staticmethod
    def generate_data(server, ver):

        packet_generator = PacketGenerator(0)

        packet_generator.add(json.dumps(
            {'version': {'name': 'GHOSTLINESS', 'protocol': int(ver)},
             'players': {'max': server.max_players, 'online': server.current_players,
                         'sample': [{
                             'name': 'think_of_death',
                             'id': '4566e69f-c907-48ee-8d71-d7ba5aa00d20'}]},
             'description': {'text': server.motd},
             'favicon': f'data:image/png;base64,{server.icon}',
             'modinfo': {'type': 'GHOSTLINESS', 'modList': []}}))
        return RawPacket(bytes(packet_generator))


class S0x1:
    @staticmethod
    def generate_data(server):
        packet_generator = PacketGenerator(1)
        # Packet ID	State	Bound To	Field Name	        Field Type	Notes
        #                               ID                  String (20) Appears to be empty.
        #                               Public Key Length	VarInt	    Length of Public Key
        # 0x01      Login   Client      Public Key	        Byte Array	Public Key
        #                               Verify Token Length	VarInt	    Length of Verify Token. Always 4 for Notchian
        #                                                               servers.
        #                               Verify Token	    Byte Array	A sequence of random bytes generated by the server.

        packet_generator.add(server.name)
        packet_generator.add(ByteArray(server.pub))
        packet_generator.add(ByteArray(random.randint(268435456, 4294967295).to_bytes(4, 'big')))
        print(packet_generator.datas)
        return RawPacket(bytes(packet_generator))
