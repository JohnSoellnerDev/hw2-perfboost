#!/usr/bin/env python3
"""
UE4.27 Pak Builder (Pak Version 7 - universal, uncompressed or Zlib, with SHA-1 integrity).
Produces standard UE4 *_P.pak patch archives loadable by Help Wanted 2 (UE 4.27) via ~mods/.
"""

import hashlib
import os
import struct
import zlib
from pathlib import Path
from typing import Iterable, Tuple

PAK_MAGIC = 0x5A6F12E1
PAK_VERSION_7 = 7  # PakFile_Version_EncryptionKeyGuid: clean, unambiguous across UE 4.20-4.27


def _fstring(s: str) -> bytes:
    b = s.encode("utf-8") + b"\x00"
    return struct.pack("<i", len(b)) + b


def _pak_entry_bytes(offset: int, comp_size: int, uncomp_size: int, comp_method: int,
                     sha1_digest: bytes, blocks: list[tuple[int, int]] | None = None,
                     block_size: int = 0) -> bytes:
    # FPakEntry for Pak v7:
    # Offset (i64), Size (i64), UncompressedSize (i64), CompressionMethod (i32), Hash (20B)
    # If CompressionMethod != 0: NumBlocks (u32) + [(Start u64, End u64), ...]
    # Flags (u8), CompressionBlockSize (u32)
    out = bytearray()
    out += struct.pack("<qqqi", offset, comp_size, uncomp_size, comp_method)
    out += sha1_digest
    if comp_method != 0:
        assert blocks is not None
        out += struct.pack("<I", len(blocks))
        for bstart, bend in blocks:
            out += struct.pack("<QQ", bstart, bend)
    out += struct.pack("<BI", 0, block_size)
    return bytes(out)


def build_pak(entries: Iterable[Tuple[str, bytes]], output_path: str | Path,
              mount_point: str = "../../../", compress: bool = False) -> None:
    """
    Build a UE4.27-compatible Pak v7 archive.

    Args:
        entries: iterable of (pak_relative_path, raw_bytes), e.g.
                 ("Thumper/Config/DefaultEngine.ini", b"...")
        output_path: destination .pak path
        mount_point: UE4 mount point (default "../../../" for game root)
        compress: if True, compress files > 512 bytes with Zlib (method 1)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_entries = sorted(
        [(rel.replace("\\", "/").lstrip("/"), data) for rel, data in entries],
        key=lambda x: x[0],
    )

    index_records: list[tuple[str, bytes]] = []
    block_size = 65536

    with open(output_path, "wb") as f:
        for rel_path, raw in sorted_entries:
            entry_offset = f.tell()
            uncomp_size = len(raw)

            if compress and uncomp_size > 512:
                comp_method = 1  # COMPRESS_ZLIB in Pak v7
                comp_chunks = [
                    zlib.compress(raw[i:i + block_size], level=6)
                    for i in range(0, uncomp_size, block_size)
                ]
                # Calculate header size: 48 + 4 + 16*n + 5
                hdr_size = 48 + 4 + 16 * len(comp_chunks) + 5
                # In Pak v7, block offsets are relative to the start of the entry!
                blocks = []
                cur = hdr_size
                for ch in comp_chunks:
                    blocks.append((cur, cur + len(ch)))
                    cur += len(ch)
                payload = b"".join(comp_chunks)
                comp_size = len(payload)
                sha1 = hashlib.sha1(payload).digest()
                inline_hdr = _pak_entry_bytes(0, comp_size, uncomp_size, comp_method, sha1, blocks, block_size)
                index_hdr = _pak_entry_bytes(entry_offset, comp_size, uncomp_size, comp_method, sha1, blocks, block_size)
            else:
                comp_method = 0  # COMPRESS_None
                payload = raw
                comp_size = uncomp_size
                sha1 = hashlib.sha1(payload).digest()
                inline_hdr = _pak_entry_bytes(0, comp_size, uncomp_size, 0, sha1)
                index_hdr = _pak_entry_bytes(entry_offset, comp_size, uncomp_size, 0, sha1)

            f.write(inline_hdr)
            f.write(payload)
            index_records.append((rel_path, index_hdr))

        # Write index
        index_offset = f.tell()
        index_buf = bytearray()
        index_buf += _fstring(mount_point)
        index_buf += struct.pack("<i", len(index_records))
        for rel_path, index_hdr in index_records:
            index_buf += _fstring(rel_path)
            index_buf += index_hdr

        index_bytes = bytes(index_buf)
        index_size = len(index_bytes)
        index_hash = hashlib.sha1(index_bytes).digest()
        f.write(index_bytes)

        # Write v7 footer (61 bytes):
        # EncryptionKeyGuid (16B) + bEncryptedIndex (1B) + Magic (4B) + Version (4B)
        # + IndexOffset (8B) + IndexSize (8B) + IndexHash (20B)
        footer = bytearray()
        footer += b"\x00" * 16
        footer += b"\x00"
        footer += struct.pack("<IIQQ", PAK_MAGIC, PAK_VERSION_7, index_offset, index_size)
        footer += index_hash
        assert len(footer) == 61
        f.write(footer)


if __name__ == "__main__":
    print("ue4_pak module ready.")
