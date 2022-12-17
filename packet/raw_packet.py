from socket import socket

from data_types import VarInt


class RawPacket:
    def __init__(self, packet_data):
        if type(packet_data) == socket:
            conn = packet_data
            data = conn.recv(4)
            packet_len = VarInt(data)
            if int(packet_len) + len(packet_len) - 4 > 0:
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

    def get_byte_array(self) -> bytes:
        array_len = int(self.get_varint())
        ba = self.packet_data[:array_len]
        self.packet_data = self.packet_data[array_len:]
        return ba

    def get_str(self) -> str:
        str_len = int(self.get_varint())
        s = self.packet_data[:str_len].decode('utf-8')
        self.packet_data = self.packet_data[str_len:]
        return s

    def get_int(self):
        i = int.from_bytes(self.packet_data[:2], 'big')
        self.packet_data = self.packet_data[2:]
        return i

    def __len__(self):
        return len(self.packet_data)

    def __bytes__(self):
        return self.raw_data
