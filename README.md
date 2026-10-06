# HTTP-in-Binary: Two Tracks, One Protocol

An end-to-end implementation of **HTTP-in-Binary (BPROTO/1.0)**, featuring a custom 9-byte binary framed network protocol, HPACK-lite compressed header codec, persistent TCP server (`bserve`), verbose binary client (`bcurl`), automated test suite, specification, and complete technical explanation.

---

## 🚀 Quickstart

### 1. Run Server
```bash
./bserve ./www 9000
```

### 2. Fetch Resources using Client
```bash
# Basic request
./bcurl localhost:9000/index.html

# Verbose hexdump mode
./bcurl -v localhost:9000/hello.txt
```

### 3. Run Test Suite
```bash
python3 tests/run_tests.py
```

---

## 📄 Hand-in Deliverables & Documentation

1. **[SPEC.md](file:///home/manav/garage/network/http-in-binary/SPEC.md)**: Two-page formal protocol specification (Frame header widths, HPACK-lite static header table, extension rules, and client/server constraints).
2. **[HEXDUMP.md](file:///home/manav/garage/network/http-in-binary/HEXDUMP.md)**: Annotated byte-level hex dump of a complete binary request and response frame sequence.
3. **[PROJECT_EXPLANATION.md](file:///home/manav/garage/network/http-in-binary/PROJECT_EXPLANATION.md)**: Deep-dive project explanation covering Problem Overview, System Architecture, Code Walkthrough, Execution Guide, and Viva Key Concepts.

---

## 🛠️ Repository Structure

```
http-in-binary/
├── bproto/                     # Core Protocol Engine Library
│   ├── __init__.py
│   ├── constants.py            # Frame types, flags, header index table, status codes
│   ├── frame.py                # Binary frame serializer, socket I/O & unknown frame skipping
│   ├── header_codec.py         # HPACK-lite header encoder/decoder
│   └── utils.py                 # Hexdump formatter, URL parser, path sanitizer
├── www/                        # Document root directory
│   ├── index.html
│   └── hello.txt
├── tests/                      # Unit and integration test suite
│   ├── test_protocol.py        # Frame packing & header codec unit tests
│   ├── test_unknown_frame.py   # Unknown frame type skipping test
│   ├── test_server_client.py   # E2E server/client integration tests
│   └── run_tests.py            # Test runner
├── bserve                      # Track 1 Server executable script
├── bcurl                       # Track 2 Client executable script
├── SPEC.md                     # Formal 2-page Protocol Specification
├── HEXDUMP.md                  # Annotated Request/Response Hex Dump
├── PROJECT_EXPLANATION.md      # Detailed Architecture & Code Walkthrough
└── README.md                   # Repository Overview
```
