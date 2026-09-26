"""
Header Codec - HPACK-lite Static Table & Length-Prefixed Encoding
"""

import struct
from .constants import STATIC_HEADER_TABLE, REVERSE_HEADER_TABLE


def encode_headers(headers: list[tuple[str, str]] | dict[str, str]) -> bytes:
    """
    Encode a list of (name, value) tuples into binary HPACK-lite format.
    
    Format:
      - Indexed Name: [0x80 | index (1B)] + [val_len (2B uint16_be)] + [val_bytes]
      - Literal Name: [0x00 (1B)] + [name_len (2B uint16_be)] + [name_bytes] + [val_len (2B uint16_be)] + [val_bytes]
    """
    if isinstance(headers, dict):
        headers = list(headers.items())

    buf = bytearray()
    for name, val in headers:
        name_lower = name.strip().lower()
        val_str = str(val)
        val_bytes = val_str.encode("utf-8")

        if name_lower in REVERSE_HEADER_TABLE:
            index = REVERSE_HEADER_TABLE[name_lower]
            descriptor = 0x80 | (index & 0x7F)
            buf.append(descriptor)
            buf.extend(struct.pack(">H", len(val_bytes)))
            buf.extend(val_bytes)
        else:
            buf.append(0x00)  # Literal name descriptor
            name_bytes = name_lower.encode("utf-8")
            buf.extend(struct.pack(">H", len(name_bytes)))
            buf.extend(name_bytes)
            buf.extend(struct.pack(">H", len(val_bytes)))
            buf.extend(val_bytes)

    return bytes(buf)


def decode_headers(data: bytes) -> list[tuple[str, str]]:
    """
    Decode binary HPACK-lite header payload into a list of (name, value) tuples.
    """
    headers = []
    idx = 0
    total_len = len(data)

    while idx < total_len:
        descriptor = data[idx]
        idx += 1

        if descriptor & 0x80:
            # Indexed Header Name
            table_idx = descriptor & 0x7F
            if table_idx not in STATIC_HEADER_TABLE:
                raise ValueError(f"Invalid static header table index: {table_idx}")
            name = STATIC_HEADER_TABLE[table_idx]

            if idx + 2 > total_len:
                raise ValueError("Truncated header value length in indexed header")
            (val_len,) = struct.unpack(">H", data[idx : idx + 2])
            idx += 2

            if idx + val_len > total_len:
                raise ValueError("Truncated header value bytes in indexed header")
            val = data[idx : idx + val_len].decode("utf-8", errors="replace")
            idx += val_len

            headers.append((name, val))

        elif descriptor == 0x00:
            # Literal Header Name
            if idx + 2 > total_len:
                raise ValueError("Truncated header name length in literal header")
            (name_len,) = struct.unpack(">H", data[idx : idx + 2])
            idx += 2

            if idx + name_len > total_len:
                raise ValueError("Truncated header name bytes in literal header")
            name = data[idx : idx + name_len].decode("utf-8", errors="replace").lower()
            idx += name_len

            if idx + 2 > total_len:
                raise ValueError("Truncated header value length in literal header")
            (val_len,) = struct.unpack(">H", data[idx : idx + 2])
            idx += 2

            if idx + val_len > total_len:
                raise ValueError("Truncated header value bytes in literal header")
            val = data[idx : idx + val_len].decode("utf-8", errors="replace")
            idx += val_len

            headers.append((name, val))

        else:
            raise ValueError(f"Invalid header descriptor byte: 0x{descriptor:02x}")

    return headers
