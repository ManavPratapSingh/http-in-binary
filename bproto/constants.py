"""
HTTP-in-Binary Protocol Constants (bproto)
"""

# Frame Header Sizes
FRAME_HEADER_SIZE = 9  # 3 bytes Length + 1 byte Type + 1 byte Flags + 4 bytes Stream ID

# Frame Types
FRAME_TYPE_HEADERS = 0x01
FRAME_TYPE_DATA = 0x02
FRAME_TYPE_PING = 0x03
FRAME_TYPE_RST_STREAM = 0x04
FRAME_TYPE_GOAWAY = 0x07

# Flags
FLAG_NONE = 0x00
FLAG_END_STREAM = 0x01  # Bit 0: Last frame of stream
FLAG_END_HEADERS = 0x04 # Bit 2: Complete header block

# Static Header Table (10 Common Headers)
STATIC_HEADER_TABLE = {
    1: ":method",
    2: ":path",
    3: ":status",
    4: "host",
    5: "user-agent",
    6: "content-type",
    7: "content-length",
    8: "server",
    9: "accept",
    10: "date",
}

# Reverse lookup for static header table (Name -> Index)
REVERSE_HEADER_TABLE = {name: index for index, name in STATIC_HEADER_TABLE.items()}

# HTTP Status Codes & Phrases
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_INTERNAL_ERROR = 500

STATUS_MESSAGES = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    500: "Internal Server Error",
}
