#!/usr/bin/env python3
"""
Exact UE4.27 UVisualQualitySettingSpec (.uasset + .uexp) parser and patcher
for Five Nights at Freddy's: Help Wanted 2.

Allows reading and replacing the Commands TArray<FVisualQualitySettingsCommand>
with byte-exact SerialSize and BulkDataStartOffset updates in the .uasset header.
"""

import struct
from typing import List, Tuple

PACKAGE_TAG = 0x9E2A83C1


def _read_fstring(buf: bytes, pos: int) -> Tuple[str, int]:
    (length,) = struct.unpack_from("<i", buf, pos)
    pos += 4
    if length == 0:
        return "", pos
    if length < 0:
        n = -length
        return buf[pos:pos + n * 2].decode("utf-16-le").rstrip("\x00"), pos + n * 2
    return buf[pos:pos + length].decode("utf-8", errors="replace").rstrip("\x00"), pos + length


def _write_fstring(s: str) -> bytes:
    if not s:
        return struct.pack("<i", 0)
    b = s.encode("ascii") + b"\x00"
    return struct.pack("<i", len(b)) + b


def _parse_uasset_names(uasset: bytes) -> List[str]:
    pos = 0
    tag, _legacy = struct.unpack_from("<Ii", uasset, pos)
    assert tag == PACKAGE_TAG, f"Invalid uasset tag: {hex(tag)}"
    pos += 12  # tag + legacy + legacy_ue3
    pos += 8   # ue4_ver + licensee_ver
    (num_cv,) = struct.unpack_from("<i", uasset, pos)
    pos += 4 + num_cv * 20
    pos += 4   # total_header_size
    _, pos = _read_fstring(uasset, pos)  # folder_name
    pos += 4   # package_flags
    name_count, name_off = struct.unpack_from("<ii", uasset, pos)

    names: List[str] = []
    np = name_off
    for _ in range(name_count):
        s, np = _read_fstring(uasset, np)
        np += 4  # hashes
        names.append(s)
    return names


def read_vq_commands(uasset: bytes, uexp: bytes) -> List[Tuple[str, str]]:
    """Read [(command, value), ...] from a UVisualQualitySettingSpec asset."""
    names = _parse_uasset_names(uasset)
    name_to_idx = {n: i for i, n in enumerate(names)}
    if "Commands" not in name_to_idx:
        return []

    pos = 0
    prop_name_idx, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    assert names[prop_name_idx] == "Commands", f"Unexpected property: {names[prop_name_idx]}"
    prop_type_idx, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    assert names[prop_type_idx] == "ArrayProperty"
    _arr_byte_size, = struct.unpack_from("<q", uexp, pos); pos += 8
    _inner_type_idx, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    _has_guid = uexp[pos]; pos += 1
    count, = struct.unpack_from("<i", uexp, pos); pos += 4

    # StructProperty header for array elements
    _s_name, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    _s_type, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    _s_size, = struct.unpack_from("<q", uexp, pos); pos += 8
    _s_struct_name, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
    pos += 16  # StructGuid
    pos += 1   # HasPropertyGuid

    cmds: List[Tuple[str, str]] = []
    for _ in range(count):
        cmd_str = ""
        val_str = ""
        while True:
            fname_idx, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
            fname = names[fname_idx]
            if fname == "None":
                break
            ftype_idx, _ = struct.unpack_from("<ii", uexp, pos); pos += 8
            assert names[ftype_idx] == "StrProperty"
            fsize, = struct.unpack_from("<q", uexp, pos); pos += 8
            pos += 1  # HasPropertyGuid
            sval, next_pos = _read_fstring(uexp, pos)
            assert next_pos - pos == fsize, f"StrProperty size mismatch: {next_pos - pos} != {fsize}"
            pos = next_pos
            if fname == "Command":
                cmd_str = sval
            elif fname == "Value":
                val_str = sval
        cmds.append((cmd_str, val_str))
    return cmds


def patch_vq_commands(uasset: bytes, uexp: bytes, new_commands: List[Tuple[str, str]]) -> Tuple[bytes, bytes]:
    """
    Rebuild UVisualQualitySettingSpec (.uasset, .uexp) with new_commands,
    updating ArrayProperty size, StructProperty size, and .uasset SerialSize/BulkDataStartOffset.
    """
    names = _parse_uasset_names(uasset)
    idx = {n: i for i, n in enumerate(names)}

    for req in ("Commands", "ArrayProperty", "StructProperty", "VisualQualitySettingsCommand",
                "Command", "Value", "StrProperty", "None"):
        assert req in idx, f"Missing required name {req} in NameMap: {names}"

    # Build struct elements payload
    elements_buf = bytearray()
    for cmd, val in new_commands:
        if cmd != "":
            c_bytes = _write_fstring(cmd)
            elements_buf += struct.pack("<ii", idx["Command"], 0)
            elements_buf += struct.pack("<ii", idx["StrProperty"], 0)
            elements_buf += struct.pack("<q", len(c_bytes))
            elements_buf += b"\x00"
            elements_buf += c_bytes
        if val != "":
            v_bytes = _write_fstring(val)
            elements_buf += struct.pack("<ii", idx["Value"], 0)
            elements_buf += struct.pack("<ii", idx["StrProperty"], 0)
            elements_buf += struct.pack("<q", len(v_bytes))
            elements_buf += b"\x00"
            elements_buf += v_bytes
        elements_buf += struct.pack("<ii", idx["None"], 0)

    # StructProperty array header (49 bytes: 8+8+8+8+16+1)
    struct_hdr = bytearray()
    struct_hdr += struct.pack("<ii", idx["Commands"], 0)
    struct_hdr += struct.pack("<ii", idx["StructProperty"], 0)
    struct_hdr += struct.pack("<q", len(elements_buf))
    struct_hdr += struct.pack("<ii", idx["VisualQualitySettingsCommand"], 0)
    struct_hdr += b"\x00" * 16
    struct_hdr += b"\x00"

    array_payload = struct.pack("<i", len(new_commands)) + struct_hdr + elements_buf

    new_uexp = bytearray()
    new_uexp += struct.pack("<ii", idx["Commands"], 0)
    new_uexp += struct.pack("<ii", idx["ArrayProperty"], 0)
    new_uexp += struct.pack("<q", len(array_payload))
    new_uexp += struct.pack("<ii", idx["StructProperty"], 0)
    new_uexp += b"\x00"
    new_uexp += array_payload
    # End of UObject properties
    new_uexp += struct.pack("<ii", idx["None"], 0)
    new_uexp += struct.pack("<I", 0)  # bHasGuid = 0
    new_uexp += struct.pack("<I", PACKAGE_TAG)
    new_uexp_bytes = bytes(new_uexp)

    # Update SerialSize (old_uexp_len - 4 -> new_uexp_len - 4) AND BulkDataStartOffset
    # (len(uasset) + old_uexp_len - 4 -> len(uasset) + new_uexp_len - 4) inside .uasset!
    old_serial = len(uexp) - 4
    new_serial = len(new_uexp_bytes) - 4
    old_bulk = len(uasset) + old_serial
    new_bulk = len(uasset) + new_serial

    new_uasset = bytearray(uasset)
    # Locate SerialSize (int64) in ExportMap (guaranteed unique at end of .uasset)
    old_serial_b = struct.pack("<q", old_serial)
    serial_pos = uasset.rfind(old_serial_b)
    assert serial_pos != -1, f"Could not locate SerialSize {old_serial} in uasset"
    new_uasset[serial_pos:serial_pos + 8] = struct.pack("<q", new_serial)

    # Update BulkDataStartOffset (int64) in FPackageFileSummary if present
    old_bulk_b = struct.pack("<q", old_bulk)
    bulk_pos = uasset.find(old_bulk_b)
    if bulk_pos != -1:
        new_uasset[bulk_pos:bulk_pos + 8] = struct.pack("<q", new_bulk)

    return bytes(new_uasset), new_uexp_bytes


if __name__ == "__main__":
    import os
    vq_dir = "/home/swoopy/.t3/userdata/providers/antigravity/ac0a3dfd6dddb20962cecff6ee5fe65e19d3923be20e52c5ab52ff877f7e4c32/antigravity-acp/brain/8ae5e54b-11a6-41ba-af91-42b4f493ac4f/scratch/hw2_vq/Thumper/Content/Data/VisualQualityOptions"
    checked = 0
    for root, _, files in os.walk(vq_dir):
        for fn in sorted(files):
            if not fn.endswith(".uexp"):
                continue
            base = os.path.join(root, fn[:-5])
            if not os.path.exists(base + ".uasset"):
                continue
            ua = open(base + ".uasset", "rb").read()
            ue = open(base + ".uexp", "rb").read()
            cmds = read_vq_commands(ua, ue)
            if not cmds:
                continue
            ua2, ue2 = patch_vq_commands(ua, ue, cmds)
            assert ua2 == ua, f"uasset mismatch on {fn}"
            assert ue2 == ue, f"uexp mismatch on {fn}"
            checked += 1
    print(f"Round-trip byte-for-byte identity verified on {checked} VisualQuality assets!")
