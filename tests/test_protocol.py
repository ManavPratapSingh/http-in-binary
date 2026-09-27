"""
Unit Tests for HTTP-in-Binary Frame Serialization and Header Compression (HPACK-lite)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bproto import (
    Frame,
    FRAME_HEADER_SIZE,
    FRAME_TYPE_HEADERS,
    FRAME_TYPE_DATA,
    FLAG_END_STREAM,
    FLAG_END_HEADERS,
    encode_headers,
    decode_headers,
    STATIC_HEADER_TABLE,
)


class TestFrameSerialization(unittest.TestCase):

    def test_frame_header_pack_unpack(self):
        payload = b"Hello Binary World!"
        frame = Frame(
            type_=FRAME_TYPE_HEADERS,
            flags=FLAG_END_HEADERS | FLAG_END_STREAM,
            stream_id=42,
            payload=payload,
        )

        packed = frame.pack()
        self.assertEqual(len(packed), FRAME_HEADER_SIZE + len(payload))

        # Unpack header
        hdr_bytes = packed[:FRAME_HEADER_SIZE]
        p_len, type_, flags, stream_id = Frame.unpack_header(hdr_bytes)

        self.assertEqual(p_len, len(payload))
        self.assertEqual(type_, FRAME_TYPE_HEADERS)
        self.assertEqual(flags, FLAG_END_HEADERS | FLAG_END_STREAM)
        self.assertEqual(stream_id, 42)

    def test_max_24bit_payload_boundary(self):
        # 16,777,215 (0xFFFFFF) is max allowed payload length
        frame = Frame(type_=FRAME_TYPE_DATA, stream_id=1, payload=b"\x00" * 100)
        hdr = frame.pack_header()
        p_len, type_, flags, stream_id = Frame.unpack_header(hdr)
        self.assertEqual(p_len, 100)


class TestHeaderCodec(unittest.TestCase):

    def test_encode_decode_indexed_headers(self):
        original_headers = [
            (":method", "GET"),
            (":path", "/index.html"),
            ("host", "localhost:9000"),
            ("user-agent", "bcurl/1.0"),
        ]

        encoded = encode_headers(original_headers)
        decoded = decode_headers(encoded)

        self.assertEqual(len(decoded), len(original_headers))
        for orig, dec in zip(original_headers, decoded):
            self.assertEqual(orig[0].lower(), dec[0].lower())
            self.assertEqual(orig[1], dec[1])

    def test_encode_decode_literal_headers(self):
        original_headers = [
            (":status", "200"),
            ("x-custom-header", "CustomValue123"),
            ("cache-control", "no-cache"),
        ]

        encoded = encode_headers(original_headers)
        decoded = decode_headers(encoded)

        self.assertEqual(len(decoded), len(original_headers))
        self.assertEqual(decoded[1][0], "x-custom-header")
        self.assertEqual(decoded[1][1], "CustomValue123")

    def test_invalid_header_index(self):
        # Index 99 invalid
        bad_payload = bytes([0x80 | 99, 0x00, 0x01, 0x41])
        with self.assertRaises(ValueError):
            decode_headers(bad_payload)


if __name__ == "__main__":
    unittest.main()
