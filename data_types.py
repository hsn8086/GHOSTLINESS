class VarInt:
    def __init__(self, value):
        if type(value) != bytes:
            self.value = bytes(self.value_of(value))
            if len(self.value) == 0:
                self.value = bytes([0])
        else:
            self.value = value
        self.__compile__()

    @staticmethod
    def value_of(value):
        if type(value) == int:
            return_list = []
            while value > 0:
                if value > 127:
                    return_list.append(value % 128 + 128)
                    value //= 128
                else:
                    return_list.append(value)
                    value = 0

            return VarInt(bytes(return_list))
        elif type(value) == str:
            return VarInt(bytes(value, 'utf-8'))
        elif type(value) == VarInt:
            return VarInt(value.__bytes__())
        elif type(value) == list:
            return VarInt(bytes(value))

    def __compile__(self):
        d = 128
        i = -1

        while d >= 128:
            i += 1
            d = self.value[i] if len(self.value) > 0 else 0

        self.value = self.value[:i + 1]

    def __len__(self):
        return len(self.value)

    def __neg__(self):
        return VarInt(-self.__int__())

    def __pos__(self):
        return self

    def __abs__(self):
        return VarInt(abs(self.__int__()))

    def __lt__(self, other):
        if type(other) == VarInt:
            return self.__int__() < other.to_int()
        else:
            return self.__int__() < other

    def __le__(self, other):
        if type(other) == VarInt:
            return self.__int__() <= other.to_int()
        else:
            return self.__int__() <= other

    def __gt__(self, other):
        if type(other) == VarInt:
            return self.__int__() > other.to_int()
        else:
            return self.__int__() > other

    def __ge__(self, other):
        if type(other) == VarInt:
            return self.__int__() >= other.to_int()
        else:
            return self.__int__() >= other

    def __add__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() + other.to_int())
        else:
            return VarInt(self.__int__() + other)

    def __radd__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() + other.to_int())
        else:
            return VarInt(self.__int__() + other)

    def __sub__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() - other.to_int())
        else:
            return VarInt(self.__int__() - other)

    def __rsub__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() - other.to_int())
        else:
            return VarInt(other.to_int() - self)

    def __mul__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() * other.to_int())
        else:
            return VarInt(self.__int__() * other)

    def __rmul__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() * other.to_int())
        else:
            return VarInt(self.__int__() * other)

    def __truediv__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() / other.to_int())
        else:
            return VarInt(self.__int__() / other)

    def __rtruediv__(self, other):
        if type(other) == VarInt:
            return VarInt(other.to_int() / self.__int__())
        else:
            return VarInt(other.to_int() / self)

    def __floordiv__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() // other.to_int())
        else:
            return VarInt(self.__int__() // other)

    def __rfloordiv__(self, other):
        if type(other) == VarInt:
            return VarInt(other.to_int() // self.__int__())
        else:
            return VarInt(other.to_int() // self)

    def __mod__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() % other.to_int())
        else:
            return VarInt(self.__int__() % other)

    def __rmod__(self, other):
        if type(other) == VarInt:
            return VarInt(other.to_int() % self.__int__())
        else:
            return VarInt(other.to_int() % self)

    def __pow__(self, other):
        if type(other) == VarInt:
            return VarInt(self.__int__() ** other.to_int())
        else:
            return VarInt(self.__int__() ** other)

    def __rpow__(self, other):
        if type(other) == VarInt:
            return VarInt(other.to_int() ** self.__int__())
        else:
            return VarInt(other.to_int() ** self)

    def __iadd__(self, other):
        self.value = self.__add__(other).__bytes__()
        return self

    def __isub__(self, other):
        self.value = self.__sub__(other).__bytes__()
        return self

    def __imul__(self, other):
        self.value = self.__mul__(other).__bytes__()
        return self

    def __itruediv__(self, other):
        self.value = self.__truediv__(other).__bytes__()
        return self

    def __ifloordiv__(self, other):
        self.value = self.__floordiv__(other).__bytes__()
        return self

    def __imod__(self, other):
        self.value = self.__mod__(other).__bytes__()
        return self

    def __ipow__(self, other):
        self.value = self.__pow__(other).__bytes__()
        return self

    def __int__(self):
        return_int = 0
        for i in self.value[::-1]:
            if i > 128:
                return_int *= 128
                return_int += i - 128
            else:
                return_int = i
        return return_int

    def __str__(self):
        return str(self.__int__())

    def __bytes__(self):
        return self.value

    def __hex__(self):
        return hex(self.__int__())

    def __oct__(self):
        return oct(self.__int__())


class UnsignedShort(int):
    def __bytes__(self):
        int.to_bytes(self, 2, "big", signed=False)


class Long(int):
    def __bytes__(self):
        return int.to_bytes(self, 8, "big", signed=True)


class Byte(bytes):
    ...


class ByteArray(bytes):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


if __name__ == '__main__':
    pass
