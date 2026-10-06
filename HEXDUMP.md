# Annotated Hexdump Walkthrough (HTTP-in-Binary)

This document provides a byte-level annotated hex dump of a complete request-response exchange over the **HTTP-in-Binary (BPROTO/1.0)** protocol.

---

## 1. Complete Binary Request Transaction

### Target URL
`localhost:9000/hello.txt`

### 1.1 Outgoing Request Frame (`HEADERS` Frame)

#### Raw Byte Sequence (Hex Dump)
```text
00000000: 00 00 37 01 05 00 00 00 01 81 00 03 47 45 54 82  ..7.........GET.
00000010: 00 0A 2F 68 65 6C 6C 6F 2E 74 78 74 84 00 0E 6C  ../hello.txt...l
00000020: 6F 63 61 6C 68 6F 73 74 3A 39 30 30 30 85 00 09  ocalhost:9000...
00000030: 62 63 75 72 6C 2F 31 2E 30                      bcurl/1.0
```

#### Detailed Byte-by-Byte Breakdown

| Byte Offset | Hex Bytes | Field Name | Decoded Value & Meaning |
| :---: | :---: | :--- | :--- |
| `0x00..0x02` | `00 00 37` | Payload Length | `55` bytes payload size ($24$-bit big-endian). |
| `0x03` | `01` | Frame Type | `0x01` = `HEADERS` frame. |
| `0x04` | `05` | Flags | `0x05` = `FLAG_END_HEADERS (0x04) \| FLAG_END_STREAM (0x01)`. |
| `0x05..0x08` | `00 00 00 01` | Stream ID | `1` (31-bit Stream ID, 1 bit reserved = 0). |
| **Header 1** | | | |
| `0x09` | `81` | Descriptor | `0x80 \| 1` $\rightarrow$ Static Index `1` (`:method`). |
| `0x0A..0x0B` | `00 03` | Value Length | `3` bytes. |
| `0x0C..0x0E` | `47 45 54` | Value Bytes | ASCII `"GET"`. |
| **Header 2** | | | |
| `0x0F` | `82` | Descriptor | `0x80 \| 2` $\rightarrow$ Static Index `2` (`:path`). |
| `0x10..0x11` | `00 0A` | Value Length | `10` bytes. |
| `0x12..0x1B` | `2F 68 65 6C 6C 6F 2E 74 78 74` | Value Bytes | ASCII `"/hello.txt"`. |
| **Header 3** | | | |
| `0x1C` | `84` | Descriptor | `0x80 \| 4` $\rightarrow$ Static Index `4` (`host`). |
| `0x1D..0x1E` | `00 0E` | Value Length | `14` bytes. |
| `0x1F..0x2C` | `6C 6F 63 ... 30` | Value Bytes | ASCII `"localhost:9000"`. |
| **Header 4** | | | |
| `0x2D` | `85` | Descriptor | `0x80 \| 5` $\rightarrow$ Static Index `5` (`user-agent`). |
| `0x2E..0x2F` | `00 09` | Value Length | `9` bytes. |
| `0x30..0x38` | `62 63 75 72 6C 2F 31 2E 30` | Value Bytes | ASCII `"bcurl/1.0"`. |

---

## 2. Incoming Response Frames

The server replies with two frames over the persistent connection:

### 2.1 Incoming Response `HEADERS` Frame

#### Raw Byte Sequence (Hex Dump)
```text
00000000: 00 00 3C 01 04 00 00 00 01 83 00 03 32 30 30 86  ..<.........200.
00000010: 00 19 74 65 78 74 2F 70 6C 61 69 6E 3B 20 63 68  ..text/plain; ch
00000020: 61 72 73 65 74 3D 75 74 66 2D 38 87 00 02 38 31  arset=utf-8...81
00000030: 88 00 0A 62 73 65 72 76 65 2F 31 2E 30          ...bserve/1.0
```

#### Detailed Byte-by-Byte Breakdown

| Byte Offset | Hex Bytes | Field Name | Decoded Value & Meaning |
| :---: | :---: | :--- | :--- |
| `0x00..0x02` | `00 00 3C` | Payload Length | `60` bytes header payload. |
| `0x03` | `01` | Frame Type | `0x01` = `HEADERS` frame. |
| `0x04` | `04` | Flags | `0x04` = `FLAG_END_HEADERS`. |
| `0x05..0x08` | `00 00 00 01` | Stream ID | `1`. |
| `0x09` | `83` | Descriptor | Static Index `3` (`:status`). |
| `0x0A..0x0E` | `00 03 32 30 30` | Value | Length `3`, Value `"200"`. |
| `0x0F` | `86` | Descriptor | Static Index `6` (`content-type`). |
| `0x10..0x2B` | `00 19 74 ... 38` | Value | Length `25`, Value `"text/plain; charset=utf-8"`. |
| `0x2C` | `87` | Descriptor | Static Index `7` (`content-length`). |
| `0x2D..0x30` | `00 02 38 31` | Value | Length `2`, Value `"81"`. |
| `0x31` | `88` | Descriptor | Static Index `8` (`server`). |
| `0x32..0x3C` | `00 0A 62 ... 30` | Value | Length `10`, Value `"bserve/1.0"`. |

---

### 2.2 Incoming Response `DATA` Frame

#### Raw Byte Sequence (Hex Dump)
```text
00000000: 00 00 51 02 01 00 00 00 01 48 65 6C 6C 6F 20 66  ..Q......Hello f
00000010: 72 6F 6D 20 48 54 54 50 2D 69 6E 2D 42 69 6E 61  rom HTTP-in-Bina
00000020: 72 79 21 0A 54 72 61 63 6B 20 31 20 28 53 65 72  ry!.Track 1 (Ser
00000030: 76 65 72 29 20 61 6E 64 20 54 72 61 63 6B 20 32  ver) and Track 2
00000040: 20 28 43 6C 69 65 6E 74 29 20 77 6F 72 6B 69 6E   (Client) workin
00000050: 67 2E 0A                                        g..
```

#### Detailed Byte-by-Byte Breakdown

| Byte Offset | Hex Bytes | Field Name | Decoded Value & Meaning |
| :---: | :---: | :--- | :--- |
| `0x00..0x02` | `00 00 51` | Payload Length | `81` bytes body payload size. |
| `0x03` | `02` | Frame Type | `0x02` = `DATA` frame. |
| `0x04` | `01` | Flags | `0x01` = `FLAG_END_STREAM`. |
| `0x05..0x08` | `00 00 00 01` | Stream ID | `1`. |
| `0x09..0x59` | `48 65 6C ... 0A` | Payload Bytes | Text: `"Hello from HTTP-in-Binary!\nTrack 1 (Server) and Track 2 (Client) working.\n"` |
