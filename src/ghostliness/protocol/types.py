from __future__ import annotations

import struct
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import nbtlib

from ghostliness.protocol.errors import PacketDecodeError, VarIntTooLongError

MAX_VARINT_BYTES = 5
MAX_VARLONG_BYTES = 10


def encode_varint(value: int) -> bytes:
    value &= 0xFFFFFFFF
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode_varint_from(read_byte: Callable[[], int]) -> int:
    result = 0
    for num_read in range(MAX_VARINT_BYTES):
        byte = read_byte()
        result |= (byte & 0x7F) << (7 * num_read)
        if not byte & 0x80:
            if result & (1 << 31):
                result -= 1 << 32
            return result
    raise VarIntTooLongError("VarInt exceeds 5 bytes")


def encode_varlong(value: int) -> bytes:
    value &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode_varlong_from(read_byte: Callable[[], int]) -> int:
    result = 0
    for num_read in range(MAX_VARLONG_BYTES):
        byte = read_byte()
        result |= (byte & 0x7F) << (7 * num_read)
        if not byte & 0x80:
            if result & (1 << 63):
                result -= 1 << 64
            return result
    raise VarIntTooLongError("VarLong exceeds 10 bytes")


@dataclass(slots=True)
class Buffer:
    data: bytes
    pos: int = 0

    @property
    def remaining(self) -> int:
        return len(self.data) - self.pos

    def read(self, length: int) -> bytes:
        if length < 0:
            raise PacketDecodeError("cannot read a negative length")
        end = self.pos + length
        if end > len(self.data):
            raise PacketDecodeError("packet ended unexpectedly")
        value = self.data[self.pos : end]
        self.pos = end
        return value

    def read_byte(self) -> int:
        return self.read(1)[0]

    def read_bool(self) -> bool:
        return self.read_byte() != 0

    def read_unsigned_byte(self) -> int:
        return self.read_byte()

    def read_short(self) -> int:
        return struct.unpack(">h", self.read(2))[0]

    def read_unsigned_short(self) -> int:
        return struct.unpack(">H", self.read(2))[0]

    def read_int(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def read_long(self) -> int:
        return struct.unpack(">q", self.read(8))[0]

    def read_float(self) -> float:
        return struct.unpack(">f", self.read(4))[0]

    def read_double(self) -> float:
        return struct.unpack(">d", self.read(8))[0]

    def read_varint(self) -> int:
        return decode_varint_from(self.read_byte)

    def read_varlong(self) -> int:
        return decode_varlong_from(self.read_byte)

    def read_string(self, max_chars: int = 32767) -> str:
        length = self.read_varint()
        if length < 0:
            raise PacketDecodeError("negative string length")
        raw = self.read(length)
        value = raw.decode("utf-8")
        if len(value) > max_chars:
            raise PacketDecodeError("string exceeds protocol limit")
        return value

    def read_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=self.read(16))

    def read_position(self) -> tuple[int, int, int]:
        value = int.from_bytes(self.read(8), "big", signed=False)
        x = _sign_extend(value >> 38, 26)
        z = _sign_extend((value >> 12) & 0x3FFFFFF, 26)
        y = _sign_extend(value & 0xFFF, 12)
        return x, y, z

    def ensure_consumed(self) -> None:
        if self.remaining:
            raise PacketDecodeError(f"{self.remaining} trailing bytes in packet")


class Writer:
    def __init__(self) -> None:
        self._data = bytearray()

    def write(self, value: bytes) -> None:
        self._data.extend(value)

    def write_byte(self, value: int) -> None:
        self._data.append(value & 0xFF)

    def write_bool(self, value: bool) -> None:
        self.write_byte(1 if value else 0)

    def write_unsigned_byte(self, value: int) -> None:
        self.write_byte(value)

    def write_short(self, value: int) -> None:
        self.write(struct.pack(">h", value))

    def write_unsigned_short(self, value: int) -> None:
        self.write(struct.pack(">H", value))

    def write_int(self, value: int) -> None:
        self.write(struct.pack(">i", value))

    def write_long(self, value: int) -> None:
        self.write(struct.pack(">q", value))

    def write_float(self, value: float) -> None:
        self.write(struct.pack(">f", value))

    def write_double(self, value: float) -> None:
        self.write(struct.pack(">d", value))

    def write_varint(self, value: int) -> None:
        self.write(encode_varint(value))

    def write_varlong(self, value: int) -> None:
        self.write(encode_varlong(value))

    def write_string(self, value: str) -> None:
        raw = value.encode("utf-8")
        self.write_varint(len(raw))
        self.write(raw)

    def write_uuid(self, value: uuid.UUID) -> None:
        self.write(value.bytes)

    def write_position(self, x: int, y: int, z: int) -> None:
        value = ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF)
        self.write(value.to_bytes(8, "big", signed=False))

    def write_byte_array(self, value: bytes) -> None:
        self.write_varint(len(value))
        self.write(value)

    def write_string_array(self, values: list[str] | tuple[str, ...]) -> None:
        self.write_varint(len(values))
        for value in values:
            self.write_string(value)

    def write_anonymous_nbt(self, value: Any) -> None:
        self.write(encode_anonymous_nbt(value))

    def write_optional_anonymous_nbt(self, value: Any | None) -> None:
        self.write_bool(value is not None)
        if value is not None:
            self.write_anonymous_nbt(value)

    def to_bytes(self) -> bytes:
        return bytes(self._data)


def encode_anonymous_nbt(value: Any) -> bytes:
    tag = to_nbt_tag(value)
    payload = BytesIO()
    tag.write(payload)
    tag_id = tag.tag_id
    if tag_id is None:
        raise TypeError(f"{type(tag).__name__} does not have an NBT tag id")
    return bytes([int(tag_id)]) + payload.getvalue()


def to_nbt_tag(value: Any) -> nbtlib.tag.Base:
    if isinstance(value, nbtlib.tag.Base):
        return value
    if isinstance(value, dict):
        return nbtlib.Compound({str(key): to_nbt_tag(item) for key, item in value.items()})
    if isinstance(value, list):
        if not value:
            return nbtlib.List[nbtlib.Compound]([])
        first_type = type(to_nbt_tag(value[0]))
        return nbtlib.List[first_type]([to_nbt_tag(item) for item in value])
    if isinstance(value, bool):
        return nbtlib.Byte(1 if value else 0)
    if isinstance(value, int):
        if -(2**31) <= value <= 2**31 - 1:
            return nbtlib.Int(value)
        return nbtlib.Long(value)
    if isinstance(value, float):
        return nbtlib.Double(value)
    if isinstance(value, str):
        return nbtlib.String(value)
    raise TypeError(f"cannot convert {type(value).__name__} to NBT")


def _sign_extend(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return (value ^ sign_bit) - sign_bit
