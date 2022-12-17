from uuid import UUID

from data_types import VarInt
from packet.base_packet import BasePacket


class S0x2(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 2
        self.fields_structure = [UUID, str, VarInt, str, str, bool, str]
