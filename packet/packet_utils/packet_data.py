from data_types import VarInt, ByteArray


class PacketGenerator:
    def __init__(self, packet_id):
        self.packet_id = packet_id
        self.datas = []

    @staticmethod
    def str(packet_data):
        return

    def add(self, packet_data, packet_type=None):
        if packet_type is None:
            self.datas.append({'type': type(packet_data), 'data': packet_data})
        else:
            self.datas.append({'type': packet_type, 'data': packet_data})

    def __bytes__(self):
        bytes_datas = bytes([])
        for d in self.datas:
            d_type = d['type']
            d_data = d['data']
            if d_type == bool:
                if d_data:
                    bytes_datas += bytes([1])
                else:
                    bytes_datas += bytes([0])
            elif d_type == bytes:
                bytes_datas += d_data
            elif d_type == int or d_type == VarInt:
                bytes_datas += bytes(d_data)
            elif d_type == str:
                bytes_datas += bytes(VarInt(len(d_data))) + bytes(d_data, 'utf-8')
            elif d_type == ByteArray:
                bytes_datas += bytes(VarInt(len(d_data))) + bytes(d_data)

        bytes_datas = bytes(VarInt(self.packet_id)) + bytes_datas

        return bytes(VarInt(len(bytes_datas))) + bytes_datas


