from data_types import Byte, Array
from packet.base_packet import BasePacket


class S0x24(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 24
        self.fields_structure = [int, bool, Byte, Byte, Array(str), ]
