#!/usr/bin/env python3
"""Extract GZIP archive from exe and decompress"""

import os
import zlib
import gzip
from pathlib import Path

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def extract_gzip(exe_path, gzip_offset):
    """Extract GZIP data from exe"""

    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(exe_path, 'rb') as f:
        # Seek to GZIP offset
        f.seek(gzip_offset)

        # Read GZIP header
        gzip_header = f.read(10)
        print(f"[*] GZIP header: {gzip_header.hex()}")

        # Go back and try to decompress
        f.seek(gzip_offset)

        # Try different lengths
        for length in [10*1024*1024, 50*1024*1024, 100*1024*1024]:  # 10MB, 50MB, 100MB
            try:
                f.seek(gzip_offset)
                compressed_data = f.read(length)

                print(f"\n[*] Trying to decompress {length:,} bytes...")

                # Try zlib decompress
                try:
                    decompressed = zlib.decompress(compressed_data)
                    print(f"[+] zlib: Decompressed {len(decompressed):,} bytes")

                    out_file = output_path / f"decompressed_zlib_{gzip_offset:X}.bin"
                    with open(out_file, 'wb') as out:
                        out.write(decompressed)
                    print(f"[+] Saved to: {out_file}")

                    return out_file

                except:
                    pass

                # Try gzip decompress
                try:
                    decompressed = gzip.decompress(compressed_data)
                    print(f"[+] gzip: Decompressed {len(decompressed):,} bytes")

                    out_file = output_path / f"decompressed_gzip_{gzip_offset:X}.bin"
                    with open(out_file, 'wb') as out:
                        out.write(decompressed)
                    print(f"[+] Saved to: {out_file}")

                    return out_file

                except Exception as e:
                    pass

                # Try raw zlib (skip gzip header)
                try:
                    f.seek(gzip_offset + 10)  # Skip gzip header
                    raw_data = f.read(length - 10)
                    decompressed = zlib.decompress(raw_data, -zlib.MAX_WBITS)
                    print(f"[+] raw zlib: Decompressed {len(decompressed):,} bytes")

                    out_file = output_path / f"decompressed_raw_{gzip_offset:X}.bin"
                    with open(out_file, 'wb') as out:
                        out.write(decompressed)
                    print(f"[+] Saved to: {out_file}")

                    return out_file

                except Exception as e:
                    pass

            except Exception as e:
                print(f"[!] Error: {e}")

    return None

def analyze_decompressed(file_path):
    """Analyze decompressed data"""

    with open(file_path, 'rb') as f:
        data = f.read()

    print(f"\n[*] Analyzing decompressed data ({len(data):,} bytes)...")

    # Check for file signatures
    if data[:4] == b'PK\x03\x04':
        print("[+] This is a ZIP archive!")
        # Try to extract
        import zipfile
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                print(f"[+] ZIP contains {len(zf.namelist())} files")

                extract_dir = Path(OUTPUT_DIR) / "extracted_zip"
                extract_dir.mkdir(exist_ok=True)

                zf.extractall(extract_dir)
                print(f"[+] Extracted to: {extract_dir}")

                # List files
                for name in zf.namelist()[:30]:
                    print(f"    - {name}")

        except Exception as e:
            print(f"[!] ZIP extraction error: {e}")

    # Check for Python bytecode
    if b'.pyc' in data or b'__main__' in data:
        print("[+] Contains Python bytecode references")

    # Search for .pyc files in the data
    import re
    pyc_pattern = b'[\\x20-\\x7E]{3,50}\\.pyc'
    matches = re.findall(pyc_pattern, data)

    if matches:
        print(f"[+] Found {len(matches)} .pyc references:")
        for m in matches[:20]:
            try:
                print(f"    {m.decode()}")
            except:
                pass

def main():
    print("="*60)
    print(" GZIP Archive Extractor")
    print("="*60)

    gzip_offset = 0x5436295

    print(f"[*] Extracting GZIP from offset 0x{gzip_offset:X}")

    decompressed_file = extract_gzip(EXE_PATH, gzip_offset)

    if decompressed_file:
        analyze_decompressed(decompressed_file)
    else:
        print("\n[!] Failed to extract GZIP data")

    print("\n"+"="*60)

if __name__ == "__main__":
    main()
