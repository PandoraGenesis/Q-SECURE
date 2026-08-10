"""
protocol_utils.py — Dong goi / giai goi du lieu truyen qua TCP.

Quy uoc khung goi tin don gian: 4 byte dau tien = do dai payload
(big-endian), phan con lai la payload (vd: anh da ma hoa dang bytes,
hoac JSON metadata).
"""
import struct


def pack_message(payload: bytes) -> bytes:
    header = struct.pack(">I", len(payload))
    return header + payload


def unpack_header(header_bytes: bytes) -> int:
    """Tra ve do dai payload doc duoc tu 4 byte header."""
    return struct.unpack(">I", header_bytes)[0]
