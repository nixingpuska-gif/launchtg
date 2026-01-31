#!/usr/bin/env python3
"""Extract PE overlay data where PyInstaller archive is typically stored"""

import struct
import os

def get_overlay(filepath, output_dir):
    """Extract PE overlay data"""

    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'rb') as f:
        # Read DOS header
        dos_header = f.read(64)
        pe_offset = struct.unpack('<I', dos_header[60:64])[0]

        f.seek(pe_offset)
        f.read(4)  # PE signature

        # COFF header
        coff = f.read(20)
        num_sections = struct.unpack('<H', coff[2:4])[0]
        opt_size = struct.unpack('<H', coff[16:18])[0]

        # Skip optional header
        f.read(opt_size)

        # Find end of sections
        max_end = 0
        for i in range(num_sections):
            section = f.read(40)
            raw_size = struct.unpack('<I', section[16:20])[0]
            raw_ptr = struct.unpack('<I', section[20:24])[0]

            section_end = raw_ptr + raw_size
            if section_end > max_end:
                max_end = section_end

        # Get file size
        f.seek(0, 2)
        file_size = f.tell()

        overlay_size = file_size - max_end

        print(f"[*] PE sections end at: 0x{max_end:X} ({max_end:,} bytes)")
        print(f"[*] File size: {file_size:,} bytes")
        print(f"[*] Overlay size: {overlay_size:,} bytes")

        if overlay_size > 0:
            print(f"\n[+] Extracting overlay...")

            f.seek(max_end)
            overlay = f.read()

            overlay_path = os.path.join(output_dir, 'overlay.bin')
            with open(overlay_path, 'wb') as out:
                out.write(overlay)

            print(f"[+] Saved to: {overlay_path}")

            # Analyze overlay
            print(f"\n[+] Overlay analysis:")
            print(f"    First 64 bytes: {overlay[:64].hex()}")

            # Search for PyInstaller markers
            if b'MEI' in overlay:
                pos = overlay.find(b'MEI')
                print(f"    [OK] MEI marker found at overlay offset 0x{pos:X}")

            if b'PYZ' in overlay:
                pos = overlay.find(b'PYZ')
                print(f"    [OK] PYZ marker found at overlay offset 0x{pos:X}")

            # Check last bytes for PyInstaller cookie
            print(f"\n[+] Last 88 bytes (PyInstaller cookie area):")
            cookie_area = overlay[-88:]
            print(f"    Hex: {cookie_area.hex()}")

            # Try to parse as PyInstaller cookie (struct at end of file)
            try:
                # PyInstaller 3.x/4.x cookie format
                # Last 24-88 bytes contain: magic + pkg_len + toc_pos + toc_len + pyver + pylibname
                magic_pos = cookie_area.find(b'MEI\x0c\x0b\x0a\x0b\x0e')
                if magic_pos != -1:
                    print(f"\n    [OK] Standard PyInstaller cookie found!")
                    cookie_start = magic_pos
                    print(f"    Cookie at offset: {cookie_start}")
                else:
                    # Try alternative
                    print(f"\n    [!] Standard cookie not found, checking alternatives...")

                    # Check if it's encrypted/obfuscated
                    if overlay[-24:-16] != b'\x00' * 8:
                        print(f"    Last 24 bytes might be modified cookie")

            except Exception as e:
                print(f"    Error parsing: {e}")

            return overlay_path
        else:
            print("[!] No overlay data found")
            return None

if __name__ == "__main__":
    exe_path = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\overlay"

    get_overlay(exe_path, output_dir)
