# HTTP-in-Binary (BPROTO/1.0) Specification
*A Minimal, Binary-Framed Application Protocol for Web Transport*

---

## 1. Overview & Philosophy

**HTTP-in-Binary (BPROTO/1.0)** is a binary application-layer protocol designed to transport HTTP-style semantics (request methods, URIs, status codes, and header fields) over persistent TCP connections. 

Unlike ASCII-based HTTP/1.1 (which suffers from line parsing overhead, delimiter injection vulnerabilities, and verbose plain-text headers), BPROTO/1.0 utilizes:
1. **Fixed-Size Binary Frame Headers**: Rapid $O(1)$ 9-byte header parsing without scanning for `\r\n\r\n`.
2. **HPACK-lite Static Header Indexing**: Top 10 common header names are mapped to 1-byte static index codes, with arbitrary length-prefixed literal headers as fallbacks.
3. **Framed Multiplexing Readiness & Forward Compatibility**: Built-in 31-bit Stream IDs and explicit rules for skipping unrecognized frame types cleanly, leaving seamless room for V2 extensions.

---

## 2. Binary Framing Layer

Every unit of communication between client and server is encapsulated inside a binary **Frame**. A Frame consists of a fixed **9-byte (72-bit) Frame Header** followed by a variable-length **Payload**.

```
 +---------------------------------------------------------------+
 | 00 01 02 | 03      | 04     | 05 06 07 08                     |
 | Length   | Type    | Flags  | R | Stream ID (31 bits)          |
 | (24 bits)| (8 bits)|(8 bits)|(1)|                             |
 +---------------------------------------------------------------+
 | Payload Bytes (0 to 16,777,215 bytes)                         |
 | ...                                                           |
 +---------------------------------------------------------------+
```

### 2.1 Header Field Definitions & Width Rationale

| Field Name | Bit Width | Byte Range | Description & Architectural Defense |
| :--- | :---: | :---: | :--- |
| **Length** | 24 bits | `0..2` | Unsigned big-endian integer. Specifies payload size ($0$ to $16,777,215$ bytes, $\approx 16\text{ MB}$). *Rationale*: 24 bits prevents buffer-overflow/OOM attacks while supporting large payloads in a single frame (matching HTTP/2). |
| **Type** | 8 bits | `3` | Frame type identifier. *Rationale*: Allows up to 256 distinct frame control types. |
| **Flags** | 8 bits | `4` | Bitmask for frame control signals. *Rationale*: 8 boolean flag slots (`END_STREAM`, `END_HEADERS`, etc.). |
| **R** | 1 bit | `5 (bit 7)`| Reserved bit. MUST be set to `0` on transmit and ignored on receipt. |
| **Stream ID**| 31 bits | `5..8` | Unsigned 31-bit big-endian integer. *Rationale*: Uniquely identifies concurrent request/response streams. Stream `0x00000000` is reserved for connection-level frames (e.g., `GOAWAY`). |

---

## 3. Frame Types & Extension Rules

### 3.1 Registry of Core Frame Types

| Type Code | Name | Function / Description |
| :---: | :--- | :--- |
| `0x01` | **HEADERS** | Contains HPACK-lite encoded request/response header block. |
| `0x02` | **DATA** | Contains arbitrary binary or text application body bytes. |
| `0x03` | **PING** | Connection-level heartbeat check. Receiver echoes payload. |
| `0x04` | **RST_STREAM** | Terminates a stream prematurely due to error. |
| `0x07` | **GOAWAY** | Signals connection teardown. |

### 3.2 Frame Flags

- `FLAG_END_STREAM` (`0x01`): Indicates that this frame is the final frame sent on the specified stream.
- `FLAG_END_HEADERS` (`0x04`): Indicates that the complete header block is contained within this frame.

### 3.3 Mandatory Forward-Compatibility Rule (Skipping Unknown Frames)

> [!IMPORTANT]
> **Extensibility Clause**: A receiver encountering a Frame Type it does not recognize (`Type > 0x07` or unassigned) **MUST read the 24-bit Length field, consume exactly that many payload bytes from the socket, discard them, and resume stream processing**.
> 
> *Defense*: This strict rule ensures that future protocol additions (such as compression dictionaries, TLS extensions, or server push frames in V2) will not break existing V1 servers or clients.

---

## 4. Header Encoding (HPACK-lite)

Header blocks inside `HEADERS` frames are serialized using a 2-tier static indexing & literal scheme:

### 4.1 Static Header Table (Top 10 Headers)

| Index Code | Wire Byte (High Bit Set) | Header Name |
| :---: | :---: | :--- |
| **1** | `0x81` | `:method` |
| **2** | `0x82` | `:path` |
| **3** | `0x83` | `:status` |
| **4** | `0x84` | `host` |
| **5** | `0x85` | `user-agent` |
| **6** | `0x86` | `content-type` |
| **7** | `0x87` | `content-length` |
| **8** | `0x88` | `server` |
| **9** | `0x89` | `accept` |
| **10** | `0x8A` | `date` |

### 4.2 Header Field Wire Representation

1. **Indexed Name Representation**:
   - `Descriptor Byte` (1B): `0x80 | Static_Index` (e.g., `0x81` for `:method`).
   - `Value Length` (2B): `uint16_be` ($N$).
   - `Value Bytes` ($N$B): UTF-8 encoded string.

2. **Literal Name Representation**:
   - `Descriptor Byte` (1B): `0x00` (indicates literal name follows).
   - `Name Length` (2B): `uint16_be` ($M$).
   - `Name Bytes` ($M$B): UTF-8 encoded string (lowercase).
   - `Value Length` (2B): `uint16_be` ($N$).
   - `Value Bytes` ($N$B): UTF-8 encoded string.

---

## 5. Client & Server Protocol Lifecycle

### 5.1 Request Lifecycle (Track 2 — Client `bcurl`)
1. **Connection**: Client establishes a single TCP socket to `host:port`.
2. **Request Framing**: Client encodes `:method` (`GET`), `:path` (`/file`), `host`, and `user-agent` headers into a `HEADERS` frame with `FLAG_END_HEADERS | FLAG_END_STREAM`.
3. **Response Processing**: Client reads incoming frames on the socket:
   - Reads `HEADERS` frame, decodes `:status` and response headers.
   - Reads `DATA` frame(s) into memory/stdout until `FLAG_END_STREAM` is set.
4. **Exit Codes**: Exit `0` for $2\text{xx}/3\text{xx}$ responses; exit non-zero (e.g. `1`) for $4\text{xx}/5\text{xx}$ errors.
5. **Connection Invariant**: Client NEVER opens a second TCP connection for a request transaction.

### 5.2 Server Lifecycle (Track 1 — Server `bserve`)
1. **Listen**: Server binds TCP port (default `9000`) and serves files from `doc_root`.
2. **Persistent Connection**: Server keeps the client TCP socket open across multiple request/response frame pairs.
3. **Validation & Mapping**:
   - If frame is malformed or invalid type $\rightarrow$ Respond with status `400 Bad Request`.
   - If requested `:path` is absent or escapes `doc_root` or file is missing $\rightarrow$ Respond with status `404 Not Found`.
   - On success $\rightarrow$ Respond with status `200 OK`, `HEADERS` frame (`content-type`, `content-length`, `server`), followed by `DATA` frame containing payload bytes with `FLAG_END_STREAM`.
