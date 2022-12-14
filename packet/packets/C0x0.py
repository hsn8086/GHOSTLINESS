from data_types import *
from packet.base_packet import BasePacket


class C0x0(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 0
        self.fields_structure = [VarInt, str, UnsignedShort, int]

    def write(self, protocol_version: int, server_address: str, server_post: int, next_state: int):
        if not 1 <= server_post <= 65535:
            raise ValueError('Invalid port.')
        if not 1 <= next_state <= 2:
            raise ValueError('Invalid state.')
        self.__add__(VarInt(protocol_version))
        self.__add__(server_address)
        self.__add__(UnsignedShort(server_post))
        self.__add__(next_state)

    def read(self):
        return tuple(self.get_data_list())
