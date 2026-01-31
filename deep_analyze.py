#!/usr/bin/env python3
"""Deep analysis of PyInstaller archive"""

import struct
import os

def deep_analyze(rsrc_file, output_dir):
    """Deep analysis of rsrc section"""

    os.makedirs(output_dir, exist_ok=True)

    with open(rsrc_file, 'rb') as f:
        data = f.read()

    print(f"[*] Loaded {len(data):,} bytes")

    # Find all MEI occurrences
    print("\n[+] Searching for 'MEI' markers...")
    pos = 0
    mei_positions = []
    while True:
        pos = data.find(b'MEI', pos)
        if pos == -1:
            break
        mei_positions.append(pos)
        pos += 1

    print(f"    Found {len(mei_positions)} 'MEI' markers")

    # Analyze context around each MEI
    for idx, mei_pos in enumerate(mei_positions[:5]):
        print(f"\n[*] MEI #{idx+1} at offset 0x{mei_pos:X}:")
        context = data[mei_pos:mei_pos+32]
        print(f"    Hex: {context.hex()}")
        print(f"    ASCII: {context}")

    # Search for PYZ archive
    print("\n[+] Searching for 'PYZ' markers...")
    pos = 0
    pyz_positions = []
    while True:
        pos = data.find(b'PYZ', pos)
        if pos == -1:
            break
        pyz_positions.append(pos)
        pos += 1

    print(f"    Found {len(pyz_positions)} 'PYZ' markers")

    for idx, pyz_pos in enumerate(pyz_positions[:3]):
        print(f"\n[*] PYZ #{idx+1} at offset 0x{pyz_pos:X}:")
        context = data[pyz_pos:pyz_pos+32]
        print(f"    Hex: {context.hex()}")

    # Search for .pyc magic bytes (Python 3.x)
    print("\n[+] Searching for Python bytecode magic...")
    pyc_magics = [
        (b'\x61\x0d\x0d\x0a', 'Python 3.9'),
        (b'\x6f\x0d\x0d\x0a', 'Python 3.10'),
        (b'\xa7\x0d\x0d\x0a', 'Python 3.11'),
        (b'\xcb\x0d\x0d\x0a', 'Python 3.12'),
        (b'\xd1\x0d\x0d\x0a', 'Python 3.13'),
    ]

    for magic, version in pyc_magics:
        count = data.count(magic)
        if count > 0:
            pos = data.find(magic)
            print(f"    {version} magic: {count} occurrences, first at 0x{pos:X}")

    # Look for ZIP signatures (PK)
    print("\n[+] Searching for ZIP signatures...")
    pk_count = data.count(b'PK\x03\x04')
    if pk_count > 0:
        pos = data.find(b'PK\x03\x04')
        print(f"    ZIP local file header: {pk_count} occurrences, first at 0x{pos:X}")

        # Try to extract ZIP
        zip_start = pos
        # Find end of central directory
        eocd = data.rfind(b'PK\x05\x06')
        if eocd != -1:
            zip_end = eocd + 22  # EOCD is at least 22 bytes
            print(f"    ZIP end of central directory at 0x{eocd:X}")

            # Extract ZIP
            zip_data = data[zip_start:zip_end]
            zip_path = os.path.join(output_dir, 'embedded.zip')
            with open(zip_path, 'wb') as f:
                f.write(zip_data)
            print(f"    [OK] Extracted potential ZIP to: {zip_path}")

    # Look for zlib compressed data
    print("\n[+] Searching for zlib-compressed data...")
    zlib_magic = b'\x78\x9c'  # Default compression
    zlib_count = data.count(zlib_magic)
    print(f"    zlib default compression: {zlib_count} occurrences")

    # Try to find PyInstaller cookie at the end of the original exe
    print("\n[+] Checking last 256 bytes for PyInstaller cookie...")
    tail = data[-256:]
    print(f"    Hex: {tail.hex()}")

    # Search for known strings
    print("\n[+] Searching for known strings...")
    strings_to_find = [
        b'base_library.zip',
        b'struct.pyi',
        b'PYZ-00.pyz',
        b'pyimod',
        b'_pyi_main',
    ]

    for s in strings_to_find:
        if s in data:
            pos = data.find(s)
            print(f"    [OK] '{s.decode()}' found at 0x{pos:X}")

    # Extract all text strings
    print(f"\n[+] Extracting readable strings...")

    import re
    strings = re.findall(b'[A-Za-z0-9_./\\\\-]{8,}', data)
    unique_strings = list(set(strings))

    # Filter interesting strings
    interesting = []
    keywords = [b'python', b'telegram', b'pyrogram', b'telethon', b'.py', b'import', b'session', b'api']

    for s in unique_strings:
        for kw in keywords:
            if kw in s.lower():
                interesting.append(s)
                break

    print(f"    Total strings: {len(unique_strings)}")
    print(f"    Interesting strings: {len(interesting)}")

    # Save interesting strings
    strings_file = os.path.join(output_dir, 'interesting_strings.txt')
    with open(strings_file, 'w', encoding='utf-8', errors='ignore') as f:
        for s in sorted(set(interesting))[:500]:
            f.write(s.decode('utf-8', errors='ignore') + '\n')

    print(f"    [OK] Saved to: {strings_file}")

    # Try alternative PyInstaller extraction
    print("\n[+] Trying alternative PyInstaller detection...")

    # Look for pyiboot pattern
    pyiboot_pos = data.find(b'pyiboot')
    if pyiboot_pos != -1:
        print(f"    [OK] 'pyiboot' found at 0x{pyiboot_pos:X}")

    # Look for LOADER pattern
    loader_pos = data.find(b'LOADER')
    if loader_pos != -1:
        print(f"    [OK] 'LOADER' found at 0x{loader_pos:X}")

if __name__ == "__main__":
    rsrc_file = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\rsrc_section.bin"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\analysis"

    deep_analyze(rsrc_file, output_dir)
