from data_types import ByteArray
from packet.base_packet import BasePacket


class S0x1(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 1
        self.fields_structure = [str, ByteArray, ByteArray]
