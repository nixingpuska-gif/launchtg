#!/usr/bin/env python3
"""Extract PYZ archive from rsrc section"""

import os
import struct
import zlib
import marshal

def extract_pyz(rsrc_file, output_dir):
    """Find and extract PYZ archive"""

    os.makedirs(output_dir, exist_ok=True)

    with open(rsrc_file, 'rb') as f:
        data = f.read()

    print(f"[*] Loaded {len(data):,} bytes")

    # Find PYZ markers
    pyz_positions = []
    pos = 0
    while True:
        pos = data.find(b'PYZ', pos)
        if pos == -1:
            break
        pyz_positions.append(pos)
        pos += 1

    print(f"[+] Found {len(pyz_positions)} PYZ markers")

    for idx, pyz_pos in enumerate(pyz_positions[:5]):
        print(f"\n[*] Analyzing PYZ #{idx+1} at offset 0x{pyz_pos:X}")

        # Read context
        context = data[pyz_pos:pyz_pos+100]
        print(f"    Context: {context[:50].hex()}")

        # Try to find TOC after PYZ marker
        # PYZ format: PYZ\0 + python_magic + toc_entries

        # Check for NULL after PYZ
        if pyz_pos + 4 < len(data) and data[pyz_pos+3:pyz_pos+4] == b'\x00':
            print(f"    [OK] PYZ header detected (PYZ\\0)")

            # Try to read python magic (4 bytes)
            magic = data[pyz_pos+4:pyz_pos+8]
            print(f"    Python magic bytes: {magic.hex()}")

            # Try to decompress following data
            for offset in range(8, 1000, 4):
                try:
                    compressed = data[pyz_pos+offset:pyz_pos+offset+100000]
                    decompressed = zlib.decompress(compressed)

                    if len(decompressed) > 100:
                        print(f"    [OK] Found zlib data at offset +{offset}, size: {len(decompressed)}")

                        # Try to unmarshal
                        try:
                            obj = marshal.loads(decompressed)
                            print(f"    [OK] Marshal data: {type(obj)}")

                            if isinstance(obj, dict):
                                print(f"        Keys: {list(obj.keys())[:10]}")

                        except:
                            pass

                        break
                except:
                    continue

    # Try to find base_library.zip
    print(f"\n[+] Searching for base_library.zip...")
    bl_pos = data.find(b'base_library')
    if bl_pos != -1:
        print(f"    Found at 0x{bl_pos:X}")
        context = data[bl_pos:bl_pos+200]
        print(f"    Context: {context}")

    # Search for .pyc files by looking for common Python module names
    print(f"\n[+] Searching for common Python modules...")

    modules = [
        b'telethon',
        b'pyrogram',
        b'asyncio',
        b'__main__',
        b'config',
        b'utils',
        b'main.py',
    ]

    for mod in modules:
        if mod in data:
            positions = []
            pos = 0
            while len(positions) < 5:
                pos = data.find(mod, pos)
                if pos == -1:
                    break
                positions.append(pos)
                pos += 1

            if positions:
                print(f"    [OK] '{mod.decode()}' found at: {[hex(p) for p in positions[:3]]}")

    # Try to find encrypted archive
    print(f"\n[+] Checking for encrypted/protected archive...")

    # Look for common encryption markers
    enc_markers = [
        (b'PYARMOR', 'PyArmor protection'),
        (b'pyarmor', 'pyarmor'),
        (b'ENCRYPTED', 'Encrypted marker'),
        (b'AES', 'AES encryption'),
    ]

    for marker, desc in enc_markers:
        if marker in data:
            pos = data.find(marker)
            print(f"    [!!] {desc} found at 0x{pos:X}")

if __name__ == "__main__":
    rsrc_file = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\rsrc_section.bin"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\pyz_extract"

    extract_pyz(rsrc_file, output_dir)
