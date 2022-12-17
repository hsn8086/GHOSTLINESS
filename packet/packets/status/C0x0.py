from packet.base_packet import BasePacket


class C0x0(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 0
        self.fields_structure = []