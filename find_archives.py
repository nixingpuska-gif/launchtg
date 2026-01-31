#!/usr/bin/env python3
"""Search for embedded archives and extract them"""

import os
import struct
import zlib

def find_archives(filepath, output_dir):
    """Find and extract embedded archives"""

    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"[*] Analyzing: {filepath}")
    print(f"[*] Size: {len(data):,} bytes\n")

    # Search for zlib streams and try to decompress
    print("[+] Looking for zlib compressed streams...")

    zlib_positions = []
    for i in range(len(data) - 2):
        # zlib header: 78 9c (default), 78 01 (no compression), 78 da (best compression)
        if data[i:i+2] in [b'\x78\x9c', b'\x78\x01', b'\x78\xda']:
            zlib_positions.append(i)

    print(f"    Found {len(zlib_positions)} potential zlib streams")

    # Try to decompress largest ones
    print("\n[+] Attempting to decompress zlib streams...")

    successful_extracts = []
    for idx, pos in enumerate(zlib_positions[:100]):  # Check first 100
        try:
            # Try different lengths
            for length in [1024*1024*10, 1024*1024, 1024*100, 1024*10]:
                if pos + length > len(data):
                    length = len(data) - pos

                try:
                    decompressed = zlib.decompress(data[pos:pos+length])
                    if len(decompressed) > 1000:  # Only save if meaningful
                        successful_extracts.append((pos, len(decompressed), decompressed[:100]))

                        # Save large extracts
                        if len(decompressed) > 10000:
                            out_path = os.path.join(output_dir, f'zlib_{pos:08X}.bin')
                            with open(out_path, 'wb') as f:
                                f.write(decompressed)
                            print(f"    [OK] Extracted {len(decompressed):,} bytes from 0x{pos:X}")
                    break
                except:
                    continue
        except:
            pass

    print(f"\n    Successfully decompressed {len(successful_extracts)} streams")

    # Look for Python-specific patterns in decompressed data
    print("\n[+] Searching for Python patterns in extracted data...")

    extracted_files = []
    for f in os.listdir(output_dir):
        if f.startswith('zlib_'):
            extracted_files.append(os.path.join(output_dir, f))

    for ef in extracted_files:
        with open(ef, 'rb') as f:
            content = f.read()

        # Check for Python patterns
        patterns = {
            b'import ': 'Python import statement',
            b'def ': 'Python function definition',
            b'class ': 'Python class definition',
            b'__name__': 'Python module check',
            b'.pyc': 'Python bytecode reference',
            b'telethon': 'Telethon library',
            b'pyrogram': 'Pyrogram library',
        }

        found = []
        for pattern, desc in patterns.items():
            if pattern in content:
                found.append(desc)

        if found:
            print(f"    {os.path.basename(ef)}:")
            for f in found:
                print(f"        - {f}")

    # Try to find and extract pyc files
    print("\n[+] Searching for .pyc file headers in main data...")

    # Python 3.x magic numbers
    pyc_magics = {
        3430: '3.9',
        3460: '3.10',
        3495: '3.11',
        3531: '3.12',
    }

    for magic, version in pyc_magics.items():
        magic_bytes = struct.pack('<H', magic) + b'\r\n'
        count = data.count(magic_bytes)
        if count > 0:
            print(f"    Python {version} bytecode: {count} occurrences")

            # Extract first few pyc files
            pos = 0
            extracted = 0
            while extracted < 10:
                pos = data.find(magic_bytes, pos)
                if pos == -1:
                    break

                # Try to extract pyc
                try:
                    # pyc header is 16 bytes in Python 3.7+
                    pyc_data = data[pos:pos+100000]  # Assume max 100KB per pyc

                    out_path = os.path.join(output_dir, f'pyc_{pos:08X}.pyc')
                    with open(out_path, 'wb') as f:
                        f.write(pyc_data)

                    print(f"        [OK] Extracted pyc at 0x{pos:X}")
                    extracted += 1
                except:
                    pass

                pos += 1

    print("\n[*] Analysis complete!")

if __name__ == "__main__":
    exe_path = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\archives"

    find_archives(exe_path, output_dir)
