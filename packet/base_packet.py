from copy import copy

from data_types import *
from .raw_packet import RawPacket


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
        return self

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
                array_len = VarInt(datas)
                datas = datas[len(array_len):]

                array_len = int(array_len)
                rt = datas[:array_len]
                datas = datas[array_len:]

            elif i == str:
                str_len = VarInt(datas)
                datas = datas[len(str_len):]

                str_len = int(str_len)

                rt = datas[:str_len].decode('utf-8')
                datas = datas[str_len:]

            elif i == int:
                rt = int.from_bytes(datas[:4], 'big')
                datas = datas[4:]
            elif i == UnsignedShort:
                rt = int.from_bytes(datas[:2], 'big', signed=False)
                datas = datas[2:]
            elif i == Long:
                rt = int.from_bytes(datas[:8], 'big', signed=False)
                datas = datas[8:]
            else:
                raise TypeError('Unrecognizable type.')
            rt_list.append(rt)
        return rt_list

    def get_data_list_raw(self) -> list:
        datas = copy(self.datas)
        rt_list = []
        for i in self.fields_structure:
            if i == VarInt:
                temp = VarInt(datas)
                rt = datas[:len(temp)]
                datas = datas[len(temp):]

            elif i == bytes:

                rt = datas[:1]
                datas = datas[1:]

            elif i == ByteArray:
                array_len = VarInt(datas)
                datas = datas[len(array_len):]

                array_len = int(array_len)
                rt = datas[:array_len]
                datas = datas[array_len:]

            elif i == str:
                str_len = VarInt(datas)
                datas = datas[len(str_len):]

                str_len = int(str_len)

                rt = datas[:str_len]
                datas = datas[str_len:]

            elif i == int:
                rt = datas[:4]
                datas = datas[4:]
            elif i == UnsignedShort:

                rt = datas[:2]
                datas = datas[2:]
            elif i == Long:
                rt = datas[:8]
                datas = datas[8:]
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

    def __str__(self):
        display_list_raw = []
        display_list = []
        display_type_list = []

        data_list_raw = self.get_data_list_raw()
        data_list = self.get_data_list()

        for idx in range(len(data_list)):
            raw_data = data_list_raw[idx]
            data = data_list[idx]
            d_type = self.fields_structure[idx]

            d_type = f'{d_type.__name__}({len(raw_data)})'
            raw_data = ','.join([hex(k)[2:] for k in raw_data])
            data = str(data)

            max_len = max(len(data), len(raw_data), len(d_type))

            data += (max_len - len(data)) * ' '
            raw_data += (max_len - len(raw_data)) * ' '
            d_type += (max_len - len(d_type)) * ' '

            display_list.append(data)
            display_list_raw.append(raw_data)
            display_type_list.append(d_type)

        return \
            f'Packet: {type(self).__name__}  PacketID: {self.packet_id}\n' \
            f'types:    |{"|".join(display_type_list)}|\n' \
            f'raw_data: |{"|".join(display_list_raw)}|\n' \
            f'data:     |{"|".join(display_list)}|'
