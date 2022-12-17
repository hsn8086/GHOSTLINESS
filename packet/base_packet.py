from copy import copy
from uuid import UUID

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
        add_data = self._add(other, d_type)
        self.datas += add_data
        self.fields_count += 1
        return self

    def _add(self, value, d_type):

        if d_type == bool:
            if value:
                add_data = bytes([1])
            else:
                add_data = bytes([0])
        elif d_type == Byte:
            add_data = value[0]
        elif d_type == int or d_type == VarInt:
            add_data = bytes(value)
        elif d_type == str:
            add_data = bytes(VarInt(len(value))) + bytes(value, 'utf-8')
        elif d_type == ByteArray or d_type == bytes:
            add_data = bytes(VarInt(len(value))) + bytes(value)
        elif d_type == UUID:
            add_data = bytes(VarInt(len(str(value)))) + bytes(str(value), 'utf-8')
        elif d_type == Array:
            add_data = bytes(VarInt(len(value)))
            for i in value:
                add_data += self._add(i, type(i))
        else:
            add_data = bytes(value)
        return add_data

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
            rt, cut_len = self._get(datas, i)
            datas = datas[cut_len:]
            rt_list.append(rt)

        return rt_list

    def _get(self, datas, d_type):
        if d_type == VarInt:
            rt = VarInt(datas)
            return rt, len(rt)

        elif d_type == Byte:
            rt = datas[:1]
            return rt, 1

        elif d_type == ByteArray or d_type == bytes:
            array_len = VarInt(datas)
            cut_len = len(array_len)

            array_len = int(array_len)
            rt = datas[cut_len:cut_len + array_len]
            cut_len += array_len
            return rt, cut_len

        elif d_type == str or d_type == UUID:
            str_len = VarInt(datas)
            cut_len = len(str_len)

            str_len = int(str_len)

            rt = datas[cut_len:cut_len + str_len].decode('utf-8')
            cut_len += str_len
            return rt, cut_len

        elif d_type == int:
            rt = int.from_bytes(datas[:4], 'big')
            return rt, 4
        elif d_type == UnsignedShort:
            rt = int.from_bytes(datas[:2], 'big', signed=False)
            return rt, 2
        elif d_type == Long:
            rt = int.from_bytes(datas[:8], 'big', signed=False)
            return rt, 8

        elif d_type == bool:
            rt = (datas[:1] == 0x01)
            return rt, 1
        elif d_type == Array:
            array_len = VarInt(datas)
            l1 = len(array_len)

            array_len = int(array_len)
            rt_list = []
            for _ in range(array_len):
                rt, cl = self._get(d_type, type(d_type))
                rt_list.append(rt)
                l1 += cl

            return '[' + ','.join(rt_list) + ']', l1
        else:
            raise TypeError('Unrecognizable type.')

    def get_data_list_raw(self) -> list:
        datas = copy(self.datas)
        rt_list = []
        for i in self.fields_structure:
            rt, cut_len = self._get_raw(datas, i)
            datas = datas[cut_len:]
            rt_list.append(rt)
        return rt_list

    def _get_raw(self, datas, d_type):
        if d_type == VarInt:
            temp = VarInt(datas)
            rt = datas[:len(temp)]
            return rt, len(temp)

        elif d_type == Byte:
            temp = datas[:1]
            return temp, 1

        elif d_type == ByteArray or d_type == bytes:
            array_len = VarInt(datas)
            cut_len = len(array_len)

            array_len = int(array_len)
            rt = datas[:array_len]
            cut_len += array_len
            return rt, cut_len

        elif d_type == str or d_type == UUID:
            str_len = VarInt(datas)
            cut_len = len(str_len)

            str_len = int(str_len)

            rt = datas[:str_len]
            cut_len += str_len
            return rt, cut_len

        elif d_type == int:
            rt = datas[:4]
            return rt, 4
        elif d_type == UnsignedShort:
            rt = datas[:2]
            return rt, 2
        elif d_type == Long:
            rt = datas[:8]
            return rt, 8

        elif d_type == bool:
            rt = datas[:1]
            return rt, 1
        elif d_type == Array:
            array_len = VarInt(datas)
            l1 = len(array_len)

            array_len = int(array_len)
            rt = bytes([])
            for _ in range(array_len):
                temp, cl = self._get_raw(d_type, type(d_type))
                l1 += cl
                rt += temp

            return rt, l1
        else:
            raise TypeError('Unrecognizable type.')

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
