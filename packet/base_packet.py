from copy import copy

from data_types import *
from packet.raw_packet import RawPacket


class BasePacket:
    def __init__(self):
        self.fields_structure = []
        self.fields_count = 0
        self.packet_id = 0
        self.datas = bytes()

    def from_raw_packet(self, raw_packet: RawPacket):
        self.datas = raw_packet.packet_data

    def __iadd__(self, other):
        d_type = self.fields_structure[self.fields_count]
        if type(other) != d_type:
            raise TypeError(f'The field should be "{d_type}" and not "{type(other)}"!')
        if d_type == bool:
            if other:
                add_data = bytes([1])
            else:
                add_data = bytes([0])
        elif d_type == bytes:
            add_data = other
        elif d_type == int or d_type == VarInt:
            add_data = bytes(other)
        elif d_type == str:
            add_data = bytes(VarInt(len(other))) + bytes(other, 'utf-8')
        elif d_type == ByteArray:
            add_data = bytes(VarInt(len(other))) + bytes(other)
        else:
            add_data = bytes(other)
        self.datas += add_data
        self.fields_count += 1

    def compile(self):
        rt_packet = bytes(VarInt(self.packet_id)) + self.datas
        return bytes(VarInt(len(rt_packet))) + rt_packet

    def __getattr__(self, item):
        if type(item) != int:
            raise TypeError('The subscript must be int.')
        if item > len(self.fields_structure):
            raise AttributeError('Subscript exceeds the length of the array.')
        return self.get_data_list()[item]

    def get_data_list(self) -> list:
        datas = copy(self.datas)
        rt_list = []
        for i in self.fields_structure:
            if i == VarInt:
                rt = VarInt(datas)
                datas = datas[len(rt):]

            elif i == bytes:
                rt = datas[0]
                datas = datas[1:]

            elif i == ByteArray:
                array_len = int(self.get_varint())
                rt = datas[:array_len]
                datas = datas[array_len:]

            elif i == str:
                str_len = VarInt(datas)
                datas = datas[len(str_len):]

                str_len=int(str_len)

                rt = datas[:str_len].decode('utf-8')
                datas = datas[str_len:]

            elif i == int:
                rt = int.from_bytes(datas[:2], 'big')
                datas = datas[2:]
            elif i == UnsignedShort:
                rt = int.from_bytes(datas[:2], 'big', signed=False)
                datas = datas[2:]
            else:
                raise TypeError('Unrecognizable type.')
            rt_list.append(rt)
        return rt_list

    def __bytes__(self):
        return self.compile()

    def read(self):
        return tuple(self.get_data_list())

    @staticmethod
    def _write_check(*args):
        pass

    def write(self, *args):
        wc = self._write_check(*args)
        if wc:
            raise wc
        for i in args:
            self.__iadd__(i)
