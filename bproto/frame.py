"""
Frame Serialization, Deserialization, and Socket I/O
"""

import struct
from typing import Optional
from .constants import (
    FRAME_HEADER_SIZE,
    FRAME_TYPE_HEADERS,
    FRAME_TYPE_DATA,
    FRAME_TYPE_PING,
    FRAME_TYPE_RST_STREAM,
    FRAME_TYPE_GOAWAY,
    FLAG_NONE,
)

KNOWN_FRAME_TYPES = {
    FRAME_TYPE_HEADERS: "HEADERS",
    FRAME_TYPE_DATA: "DATA",
    FRAME_TYPE_PING: "PING",
    FRAME_TYPE_RST_STREAM: "RST_STREAM",
    FRAME_TYPE_GOAWAY: "GOAWAY",
}


class Frame:
    """
    Represents an HTTP-in-Binary frame.
    
    Header structure (9 bytes):
      [0..2] : 24-bit Payload Length (Big-Endian)
      [3]    : 8-bit Frame Type
      [4]    : 8-bit Flags
      [5..8] : 32-bit Stream ID (1 bit reserved + 31 bits ID)
    """

    def __init__(self, type_: int, flags: int = FLAG_NONE, stream_id: int = 1, payload: bytes = b""):
        self.type = type_
        self.flags = flags
        self.stream_id = stream_id & 0x7FFFFFFF
        self.payload = payload

    @property
    def payload_length(self) -> int:
        return len(self.payload)

    @property
    def type_name(self) -> str:
        return KNOWN_FRAME_TYPES.get(self.type, f"UNKNOWN(0x{self.type:02x})")

    def is_known_type(self) -> bool:
        return self.type in KNOWN_FRAME_TYPES

    def pack_header(self) -> bytes:
        length = self.payload_length
        if length > 0xFFFFFF:
            raise ValueError(f"Payload length {length} exceeds maximum allowed 24-bit size (16,777,215 bytes)")

        b0 = (length >> 16) & 0xFF
        b1 = (length >> 8) & 0xFF
        b2 = length & 0xFF

        header = bytearray([b0, b1, b2, self.type & 0xFF, self.flags & 0xFF])
        header.extend(struct.pack(">I", self.stream_id & 0x7FFFFFFF))
        return bytes(header)

    def pack(self) -> bytes:
        return self.pack_header() + self.payload

    @classmethod
    def unpack_header(cls, header_bytes: bytes) -> tuple[int, int, int, int]:
        """
        Unpack 9-byte frame header.
        Returns (payload_length, type, flags, stream_id)
        """
        if len(header_bytes) != FRAME_HEADER_SIZE:
            raise ValueError(f"Header bytes must be exactly {FRAME_HEADER_SIZE} bytes, got {len(header_bytes)}")

        length = (header_bytes[0] << 16) | (header_bytes[1] << 8) | header_bytes[2]
        type_ = header_bytes[3]
        flags = header_bytes[4]
        (stream_id,) = struct.unpack(">I", header_bytes[5:9])
        stream_id &= 0x7FFFFFFF

        return length, type_, flags, stream_id

    def __repr__(self):
        return f"<Frame type={self.type_name} flags=0x{self.flags:02x} stream_id={self.stream_id} payload_len={self.payload_length}>"


def recv_exact(sock, n: int) -> Optional[bytes]:
    """Helper to read exactly n bytes from a socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            if len(buf) == 0:
                return None  # Socket EOF
            raise ConnectionError(f"Connection closed prematurely (got {len(buf)}/{n} bytes)")
        buf.extend(chunk)
    return bytes(buf)


def read_frame(sock, skip_unknown: bool = True) -> Optional[Frame]:
    """
    Read a single Frame from socket.
    If skip_unknown=True and an unknown frame type is received, read & discard payload,
    then read next frame cleanly.
    """
    while True:
        header_bytes = recv_exact(sock, FRAME_HEADER_SIZE)
        if header_bytes is None:
            return None  # Connection closed gracefully

        payload_len, type_, flags, stream_id = Frame.unpack_header(header_bytes)
        payload = b""
        if payload_len > 0:
            payload_bytes = recv_exact(sock, payload_len)
            if payload_bytes is None:
                raise ConnectionError("Connection closed while reading frame payload")
            payload = payload_bytes

        frame = Frame(type_=type_, flags=flags, stream_id=stream_id, payload=payload)

        if not frame.is_known_type() and skip_unknown:
            # Skip unknown frame cleanly (Protocol specification requirement)
            continue

        return frame


def write_frame(sock, frame: Frame) -> None:
    """Send a Frame over socket."""
    sock.sendall(frame.pack())
