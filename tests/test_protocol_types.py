import pytest

from ghostliness.protocol.errors import VarIntTooLongError
from ghostliness.protocol.types import Buffer, Writer, encode_anonymous_nbt, encode_varint


@pytest.mark.parametrize(
    ("value", "raw"),
    [
        (0, b"\x00"),
        (1, b"\x01"),
        (127, b"\x7f"),
        (128, b"\x80\x01"),
        (255, b"\xff\x01"),
        (2147483647, b"\xff\xff\xff\xff\x07"),
        (-1, b"\xff\xff\xff\xff\x0f"),
    ],
)
def test_varint_roundtrip(value, raw):
    assert encode_varint(value) == raw
    assert Buffer(raw).read_varint() == value


def test_varint_rejects_too_long_values():
    with pytest.raises(VarIntTooLongError):
        Buffer(b"\xff\xff\xff\xff\xff\x01").read_varint()


def test_string_roundtrip():
    writer = Writer()
    writer.write_string("GHOSTLINESS")
    assert Buffer(writer.to_bytes()).read_string() == "GHOSTLINESS"


def test_anonymous_nbt_encodes_root_compound_without_name():
    encoded = encode_anonymous_nbt({"text": "hello"})

    assert encoded[0] == 10
    assert b"text" in encoded
