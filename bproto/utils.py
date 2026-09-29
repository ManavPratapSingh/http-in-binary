"""
Protocol Utilities: Hexdump Formatter, URL Parsing, and Safe Path Mapping
"""

import os
import urllib.parse
from typing import Optional


def format_hexdump(data: bytes, prefix: str = "") -> str:
    """
    Generate standard 16-byte aligned annotated hexdump string.
    Example line format:
    00000000: 00 00 2D 01 01 00 00 00 01 81 00 03 47 45 54 82  ..-.........GET.
    """
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_bytes = " ".join(f"{b:02X}" for b in chunk)
        ascii_chars = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        line = f"{prefix}{i:08X}: {hex_bytes:<47}  {ascii_chars}"
        lines.append(line)
    return "\n".join(lines)


def parse_url(url_str: str) -> tuple[str, int, str]:
    """
    Parse URL string into (host, port, path).
    Supports formats:
      - localhost:9000/index.html
      - http://localhost:9000/index.html
      - localhost:9000
    """
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        url_str = "http://" + url_str

    parsed = urllib.parse.urlparse(url_str)
    host = parsed.hostname or "localhost"
    port = parsed.port or 9000
    path = parsed.path or "/"

    if not path.startswith("/"):
        path = "/" + path

    return host, port, path


def sanitize_path(root_dir: str, req_path: str) -> Optional[str]:
    """
    Safely resolve requested path under root_dir.
    Returns absolute file path if valid and within root_dir, else None.
    """
    abs_root = os.path.abspath(root_dir)

    # Normalize request path (remove query string/fragment if present)
    req_path = req_path.split("?")[0].split("#")[0]
    # Remove leading slash for os.path.join
    rel_path = req_path.lstrip("/")

    target_path = os.path.abspath(os.path.join(abs_root, rel_path))

    # Path traversal safety check
    if not target_path.startswith(abs_root):
        return None

    # Handle directory request by appending index.html
    if os.path.isdir(target_path):
        target_path = os.path.join(target_path, "index.html")

    if os.path.isfile(target_path):
        return target_path

    return None
