from socket import socket

from communication_types import VarInt


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

        bytes_datas = bytes([self.packet_id]) + bytes_datas

        return bytes(VarInt(len(bytes_datas))) + bytes_datas


class Packet:
    def __init__(self, packet_data):
        if type(packet_data) == socket:
            conn = packet_data
            data = conn.recv(4)
            packet_len = VarInt(data)

            data += conn.recv(int(packet_len) + len(packet_len) - 4)
            self.raw_data = data

        elif type(packet_data) == bytes:
            self.raw_data = packet_data
        else:
            self.raw_data = bytes(packet_data)
        self.packet_data = self.raw_data

        self.len = VarInt(self.packet_data)
        self.packet_data = self.packet_data[len(self.len):int(self.len) + len(self.len)]

        self.id = VarInt(self.packet_data)
        self.packet_data = self.packet_data[len(self.id):]

    def get_varint(self):
        i = VarInt(self.packet_data)
        self.packet_data = self.packet_data[len(i):]
        return i

    def get_byte(self):
        b = self.packet_data[0]
        self.packet_data = self.packet_data[1:]
        return b

    def get_str(self):
        i = VarInt(self.packet_data)
        self.packet_data = self.packet_data[len(i):]
        s = self.packet_data[:int(i)].decode('utf-8')
        self.packet_data = self.packet_data[int(i):]
        return s

    def get_int(self):
        i = int.from_bytes(self.packet_data[:2], 'big')
        self.packet_data = self.packet_data[2:]
        return i

    def __len__(self):
        return len(self.packet_data)

    def __bytes__(self):
        return self.raw_data
