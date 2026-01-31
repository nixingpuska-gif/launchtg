#!/usr/bin/env python3
"""Extract embedded ZIP from zlib file"""

import os
import zipfile
import io

def extract_embedded_zip(filepath, output_dir):
    """Find and extract embedded ZIP"""

    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"[*] Searching for ZIP in {filepath}")

    # Find ZIP signature
    pk_pos = data.find(b'PK\x03\x04')
    if pk_pos == -1:
        pk_pos = data.find(b'PK')

    if pk_pos == -1:
        print("[!] No ZIP signature found")
        return

    print(f"[+] ZIP found at offset 0x{pk_pos:X}")

    # Find end of ZIP
    eocd_pos = data.rfind(b'PK\x05\x06')
    if eocd_pos != -1:
        zip_end = eocd_pos + 22  # EOCD minimum size
        print(f"[+] ZIP EOCD at offset 0x{eocd_pos:X}")
    else:
        zip_end = len(data)
        print("[!] No EOCD found, using end of file")

    zip_data = data[pk_pos:zip_end]
    print(f"[+] ZIP size: {len(zip_data):,} bytes")

    # Save ZIP
    zip_path = os.path.join(output_dir, 'embedded.zip')
    with open(zip_path, 'wb') as f:
        f.write(zip_data)
    print(f"[+] Saved to: {zip_path}")

    # Try to extract
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf:
            print(f"\n[+] ZIP contents ({len(zf.namelist())} files):")
            for name in zf.namelist()[:30]:
                info = zf.getinfo(name)
                print(f"    - {name} ({info.file_size:,} bytes)")

            # Extract all
            extract_dir = os.path.join(output_dir, 'zip_contents')
            zf.extractall(extract_dir)
            print(f"\n[+] Extracted to: {extract_dir}")

    except Exception as e:
        print(f"[!] Error extracting ZIP: {e}")

        # Try to repair/extract manually
        print("[*] Trying manual extraction...")

if __name__ == "__main__":
    zlib_file = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\archives\zlib_00037D65.bin"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\zip_extract"

    extract_embedded_zip(zlib_file, output_dir)
