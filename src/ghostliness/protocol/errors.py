class ProtocolError(Exception):
    """Base protocol error."""


class VarIntTooLongError(ProtocolError):
    """Raised when a VarInt exceeds the Java Edition maximum length."""


class PacketDecodeError(ProtocolError):
    """Raised when a packet cannot be decoded from a frame."""


class UnknownPacketError(PacketDecodeError):
    """Raised when no registered packet matches a packet ID."""
