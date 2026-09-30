"""
Test Unknown Frame Type Skipping Requirement
"""

import unittest
import socket
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bproto import (
    Frame,
    FRAME_TYPE_HEADERS,
    FRAME_TYPE_DATA,
    FLAG_END_HEADERS,
    FLAG_END_STREAM,
    read_frame,
    write_frame,
    encode_headers,
)


class TestUnknownFrameSkipping(unittest.TestCase):

    def test_unknown_frame_skipping(self):
        # Create a socketpair to simulate stream communication
        server_sock, client_sock = socket.socketpair()

        try:
            # Send an unknown frame type 0xFE with payload b"v2_extension_data"
            unknown_frame = Frame(
                type_=0xFE,  # Unrecognized extension frame type
                flags=0x00,
                stream_id=1,
                payload=b"v2_extension_data_payload_12345",
            )

            # Send a valid HEADERS frame immediately after
            headers_payload = encode_headers([(":method", "GET"), (":path", "/index.html")])
            valid_frame = Frame(
                type_=FRAME_TYPE_HEADERS,
                flags=FLAG_END_HEADERS,
                stream_id=1,
                payload=headers_payload,
            )

            write_frame(client_sock, unknown_frame)
            write_frame(client_sock, valid_frame)

            # Receiver reads from socket with skip_unknown=True
            received = read_frame(server_sock, skip_unknown=True)

            self.assertIsNotNone(received)
            self.assertEqual(received.type, FRAME_TYPE_HEADERS)
            self.assertEqual(received.stream_id, 1)

        finally:
            server_sock.close()
            client_sock.close()


if __name__ == "__main__":
    unittest.main()
