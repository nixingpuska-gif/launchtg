#!/usr/bin/env python3
"""Manual PyInstaller archive extractor"""

import struct
import os
import zlib
import marshal

def find_and_extract_pyinstaller(rsrc_file, output_dir):
    """Find PyInstaller archive in rsrc section and extract manually"""

    os.makedirs(output_dir, exist_ok=True)

    with open(rsrc_file, 'rb') as f:
        data = f.read()

    print(f"[*] Loaded {len(data):,} bytes from rsrc section")

    # Find MEI marker
    mei_positions = []
    pos = 0
    while True:
        pos = data.find(b'MEI\x0c\x0b\x0a\x0b\x0e', pos)
        if pos == -1:
            break
        mei_positions.append(pos)
        pos += 1

    print(f"[+] Found {len(mei_positions)} MEI markers")

    for idx, mei_pos in enumerate(mei_positions[:3]):  # Check first 3
        print(f"\n[*] Analyzing MEI marker #{idx+1} at offset 0x{mei_pos:X}")

        # Try to parse PyInstaller header
        try:
            f_data = data[mei_pos:]

            # Skip MEI magic (8 bytes)
            offset = 8

            # Read package length
            pkg_len = struct.unpack('!I', f_data[offset:offset+4])[0]
            offset += 4

            # Read TOC position
            toc_pos = struct.unpack('!I', f_data[offset:offset+4])[0]
            offset += 4

            # Read TOC length
            toc_len = struct.unpack('!I', f_data[offset:offset+4])[0]
            offset += 4

            # Read Python version
            pyver = struct.unpack('!I', f_data[offset:offset+4])[0]
            offset += 4

            print(f"    Package length: {pkg_len:,}")
            print(f"    TOC position: {toc_pos:,}")
            print(f"    TOC length: {toc_len:,}")
            print(f"    Python version: {pyver}")

            if pkg_len > len(data) or toc_pos > pkg_len or toc_len > pkg_len:
                print(f"    [!] Invalid values, skipping")
                continue

            print(f"    [+] Valid PyInstaller header found!")

            # Extract TOC
            toc_data = f_data[toc_pos:toc_pos+toc_len]

            print(f"\n    [*] Parsing TOC entries...")

            # Parse TOC entries
            entries = []
            toc_offset = 0

            while toc_offset < len(toc_data):
                # Entry format: entrylen(4) + position(4) + uncmprlen(4) + comprflag(1) + typecode(1) + name(var)
                if toc_offset + 4 > len(toc_data):
                    break

                entry_len = struct.unpack('!I', toc_data[toc_offset:toc_offset+4])[0]

                if entry_len == 0 or toc_offset + entry_len > len(toc_data):
                    break

                entry_data = toc_data[toc_offset:toc_offset+entry_len]

                # Parse entry
                e_pos = struct.unpack('!I', entry_data[4:8])[0]
                e_uncmprlen = struct.unpack('!I', entry_data[8:12])[0]
                e_comprflag = entry_data[12]
                e_typecode = chr(entry_data[13])
                e_name = entry_data[14:].rstrip(b'\x00').decode('utf-8', errors='ignore')

                entries.append({
                    'position': e_pos,
                    'uncmprlen': e_uncmprlen,
                    'compressed': e_comprflag,
                    'typecode': e_typecode,
                    'name': e_name
                })

                toc_offset += entry_len

            print(f"    [+] Found {len(entries)} TOC entries")

            # Show first 20 entries
            print(f"\n    [*] First 20 entries:")
            for i, entry in enumerate(entries[:20]):
                print(f"        {i+1}. {entry['name']:<40} [{entry['typecode']}] {entry['uncmprlen']:>10,} bytes")

            # Extract files
            print(f"\n    [*] Extracting files...")

            extracted_count = 0
            for entry in entries:
                try:
                    # Get file data
                    file_data = f_data[entry['position']:entry['position']+entry['uncmprlen']]

                    # Decompress if needed
                    if entry['compressed']:
                        try:
                            file_data = zlib.decompress(file_data)
                        except:
                            pass

                    # Determine output path
                    safe_name = entry['name'].replace('\\', '_').replace('/', '_').replace('..', '_')
                    out_path = os.path.join(output_dir, safe_name)

                    # Save file
                    with open(out_path, 'wb') as out:
                        out.write(file_data)

                    extracted_count += 1

                    if extracted_count <= 10:
                        print(f"        [OK] Extracted: {safe_name}")

                except Exception as e:
                    if extracted_count <= 10:
                        print(f"        [!] Failed: {entry['name']} - {e}")

            print(f"\n    [+] Extracted {extracted_count}/{len(entries)} files to {output_dir}")

            return True

        except Exception as e:
            print(f"    [!] Error parsing: {e}")
            continue

    return False

if __name__ == "__main__":
    rsrc_file = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\rsrc_section.bin"
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\unpacked"

    if os.path.exists(rsrc_file):
        success = find_and_extract_pyinstaller(rsrc_file, output_dir)

        if success:
            print(f"\n{'='*60}")
            print("[*] Extraction successful!")
            print(f"[*] Check {output_dir} for extracted files")
            print(f"{'='*60}")
        else:
            print("\n[!] Could not extract PyInstaller archive")
    else:
        print(f"[!] File not found: {rsrc_file}")
