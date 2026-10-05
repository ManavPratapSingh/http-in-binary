"""
End-to-End Integration Tests for bserve and bcurl
"""

import unittest
import subprocess
import time
import socket
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bproto import (
    Frame,
    FRAME_TYPE_HEADERS,
    FRAME_TYPE_DATA,
    FLAG_END_HEADERS,
    write_frame,
    read_frame,
    encode_headers,
    decode_headers,
)


class TestServerClientIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.port = 9876
        cls.doc_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "www"))
        cls.bserve_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bserve"))
        cls.bcurl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bcurl"))

        # Launch server process
        cls.server_proc = subprocess.Popen(
            [sys.executable, cls.bserve_path, cls.doc_root, str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.5)  # Allow server to bind and listen

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        cls.server_proc.wait()

    def test_bcurl_get_200_ok(self):
        cmd = [sys.executable, self.bcurl_path, f"localhost:{self.port}/index.html"]
        res = subprocess.run(cmd, capture_output=True, text=True)

        self.assertEqual(res.returncode, 0)
        self.assertIn("Welcome to HTTP-in-Binary Server!", res.stdout)

    def test_bcurl_verbose_hexdump(self):
        cmd = [sys.executable, self.bcurl_path, "-v", f"localhost:{self.port}/hello.txt"]
        res = subprocess.run(cmd, capture_output=True, text=True)

        self.assertEqual(res.returncode, 0)
        self.assertIn("Hello from HTTP-in-Binary!", res.stdout)
        # Check stderr for verbose hexdump lines
        self.assertIn("> Send HEADERS frame", res.stderr)
        self.assertIn("< Recv HEADERS frame", res.stderr)
        self.assertIn("00000000:", res.stderr)

    def test_bcurl_get_404_not_found(self):
        cmd = [sys.executable, self.bcurl_path, f"localhost:{self.port}/non_existent_file.xyz"]
        res = subprocess.run(cmd, capture_output=True, text=True)

        self.assertNotEqual(res.returncode, 0)  # non-zero on 4xx/5xx
        self.assertIn("404 Not Found", res.stdout)

    def test_persistent_connection(self):
        # Open a single socket and send 3 consecutive request frames over the same TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", self.port))

        try:
            paths = ["/index.html", "/hello.txt", "/index.html"]
            for i, p in enumerate(paths, start=1):
                req_hdr = encode_headers([(":method", "GET"), (":path", p)])
                req_frame = Frame(
                    type_=FRAME_TYPE_HEADERS,
                    flags=FLAG_END_HEADERS,
                    stream_id=i,
                    payload=req_hdr,
                )
                write_frame(sock, req_frame)

                # Read response HEADERS
                resp_h = read_frame(sock)
                self.assertIsNotNone(resp_h)
                self.assertEqual(resp_h.type, FRAME_TYPE_HEADERS)
                headers = dict(decode_headers(resp_h.payload))
                self.assertEqual(headers.get(":status"), "200")

                # Read response DATA
                resp_d = read_frame(sock)
                self.assertIsNotNone(resp_d)
                self.assertEqual(resp_d.type, FRAME_TYPE_DATA)
                self.assertGreater(len(resp_d.payload), 0)
        finally:
            sock.close()

    def test_malformed_frame_400_response(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", self.port))

        try:
            # Send DATA frame first (invalid request frame type, expected HEADERS)
            bad_frame = Frame(type_=0x02, stream_id=1, payload=b"Invalid First Frame")
            write_frame(sock, bad_frame)

            resp_h = read_frame(sock)
            self.assertIsNotNone(resp_h)
            self.assertEqual(resp_h.type, FRAME_TYPE_HEADERS)
            headers = dict(decode_headers(resp_h.payload))
            self.assertEqual(headers.get(":status"), "400")
        finally:
            sock.close()


if __name__ == "__main__":
    unittest.main()
