#!/usr/bin/env python3
"""Extract and analyze .rsrc section from PE file"""

import struct
import os

def extract_rsrc_section(filepath, output_dir):
    """Extract .rsrc section from PE file"""

    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'rb') as f:
        # Read DOS header
        dos_header = f.read(64)
        pe_offset = struct.unpack('<I', dos_header[60:64])[0]

        f.seek(pe_offset)
        f.read(4)  # PE signature

        # Read COFF header
        coff_header = f.read(20)
        num_sections = struct.unpack('<H', coff_header[2:4])[0]
        optional_header_size = struct.unpack('<H', coff_header[16:18])[0]

        # Skip optional header
        f.read(optional_header_size)

        # Find .rsrc section
        print("[*] Searching for .rsrc section...")

        for i in range(num_sections):
            section_header = f.read(40)

            name = section_header[0:8].rstrip(b'\x00').decode('utf-8', errors='ignore')
            virt_size = struct.unpack('<I', section_header[8:12])[0]
            raw_size = struct.unpack('<I', section_header[16:20])[0]
            raw_ptr = struct.unpack('<I', section_header[20:24])[0]

            if name == '.rsrc':
                print(f"[+] Found .rsrc section:")
                print(f"    - Virtual size: {virt_size:,} bytes")
                print(f"    - Raw size: {raw_size:,} bytes")
                print(f"    - Raw pointer: 0x{raw_ptr:X}\n")

                # Extract section
                print("[*] Extracting .rsrc section...")
                f.seek(raw_ptr)
                rsrc_data = f.read(raw_size)

                output_file = os.path.join(output_dir, 'rsrc_section.bin')
                with open(output_file, 'wb') as out:
                    out.write(rsrc_data)

                print(f"[+] Extracted to: {output_file}")

                # Analyze first 1KB
                print(f"\n[*] First 512 bytes (hex):")
                print(rsrc_data[:512].hex())

                # Search for signatures
                print(f"\n[+] Searching for signatures in .rsrc...")

                signatures = {
                    b'MEI': 'PyInstaller MEI marker',
                    b'PYZ': 'PyInstaller PYZ archive',
                    b'python': 'Python reference',
                    b'PYTHONPATH': 'Python path variable',
                    b'\x1f\x8b\x08': 'GZIP compressed data',
                    b'PK\x03\x04': 'ZIP archive',
                    b'PK\x05\x06': 'ZIP end of central directory'
                }

                found = []
                for sig, desc in signatures.items():
                    positions = []
                    start = 0
                    while True:
                        pos = rsrc_data.find(sig, start)
                        if pos == -1:
                            break
                        positions.append(pos)
                        start = pos + 1
                        if len(positions) >= 10:  # Limit to first 10 occurrences
                            break

                    if positions:
                        found.append((desc, len(positions), positions[0]))
                        print(f"    [OK] {desc}: found {len(positions)} occurrence(s), first at offset 0x{positions[0]:X}")

                if not found:
                    print("    [!] No known signatures found")

                # Try to find PyInstaller TOC
                print(f"\n[+] Searching for PyInstaller Table of Contents...")
                # PyInstaller usually has a magic cookie at the end
                cookie_size = 24  # PyInstaller cookie is typically 24 bytes at the end
                if len(rsrc_data) > cookie_size:
                    cookie = rsrc_data[-cookie_size:]
                    print(f"    Last {cookie_size} bytes (potential PyInstaller cookie):")
                    print(f"    {cookie.hex()}")

                    # Try to parse as PyInstaller cookie
                    if b'MEI' in cookie:
                        print("    [OK] MEI signature in cookie - likely PyInstaller!")

                return output_file

    print("[!] .rsrc section not found")
    return None

if __name__ == "__main__":
    exe_path = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted"

    extracted = extract_rsrc_section(exe_path, output_dir)

    if extracted:
        print(f"\n{'='*60}")
        print("[*] Extraction complete!")
        print(f"[*] Next steps:")
        print(f"    1. Analyze {extracted}")
        print(f"    2. Try pyinstxtractor if PyInstaller detected")
        print(f"    3. Search for embedded Python bytecode (.pyc files)")
        print(f"{'='*60}")
