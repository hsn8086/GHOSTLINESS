from __future__ import annotations

import asyncio
import zlib

from ghostliness.protocol.containers import PacketContainer
from ghostliness.protocol.errors import PacketDecodeError
from ghostliness.protocol.registry import PacketDirection, PacketRegistry, PacketState, PacketType
from ghostliness.protocol.types import Buffer, Writer, decode_varint_from, encode_varint


async def read_varint_from_stream(reader: asyncio.StreamReader) -> int:
    async def read_one() -> int:
        raw = await reader.readexactly(1)
        return raw[0]

    result = 0
    for num_read in range(5):
        byte = await read_one()
        result |= (byte & 0x7F) << (7 * num_read)
        if not byte & 0x80:
            if result & (1 << 31):
                result -= 1 << 32
            return result
    raise PacketDecodeError("VarInt exceeds 5 bytes")


async def read_frame(reader: asyncio.StreamReader) -> bytes:
    length = await read_varint_from_stream(reader)
    if length < 0:
        raise PacketDecodeError("negative packet length")
    return await reader.readexactly(length)


def decode_frame(
    registry: PacketRegistry,
    state: PacketState,
    direction: PacketDirection,
    frame: bytes,
    compression_threshold: int = -1,
) -> PacketContainer:
    payload = _decompress_payload(frame, compression_threshold)
    buffer = Buffer(payload)
    packet_id = buffer.read_varint()
    packet_type = registry.get(state, direction, packet_id)
    raw_payload = payload[buffer.pos :]
    if packet_type.decoder is None:
        fields: dict[str, object] = {}
    else:
        fields = packet_type.decoder(Buffer(raw_payload))
    return PacketContainer(packet_type=packet_type, fields=fields, raw_payload=raw_payload)


def encode_frame(packet: PacketContainer, compression_threshold: int = -1) -> bytes:
    payload = encode_payload(packet.packet_type, dict(packet.fields))
    if compression_threshold >= 0:
        if len(payload) >= compression_threshold:
            body = encode_varint(len(payload)) + zlib.compress(payload)
        else:
            body = encode_varint(0) + payload
    else:
        body = payload
    return encode_varint(len(body)) + body


def encode_payload(packet_type: PacketType, fields: dict[str, object]) -> bytes:
    writer = Writer()
    writer.write_varint(packet_type.packet_id)
    if packet_type.encoder is not None:
        packet_type.encoder(writer, fields)
    return writer.to_bytes()


def _decompress_payload(frame: bytes, compression_threshold: int) -> bytes:
    if compression_threshold < 0:
        return frame
    buffer = Buffer(frame)
    data_length = buffer.read_varint()
    compressed = buffer.read(buffer.remaining)
    if data_length == 0:
        return compressed
    payload = zlib.decompress(compressed)
    if len(payload) != data_length:
        raise PacketDecodeError("decompressed payload length mismatch")
    return payload


def read_varint_from_bytes(data: bytes) -> tuple[int, int]:
    buffer = Buffer(data)
    return decode_varint_from(buffer.read_byte), buffer.pos
