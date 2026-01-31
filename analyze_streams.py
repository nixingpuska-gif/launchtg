#!/usr/bin/env python3
"""Analyze extracted zlib streams for Python source/bytecode"""

import os
import struct
import marshal
from pathlib import Path

STREAMS_DIR = Path(r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\zlib_streams")
OUTPUT_DIR = Path(r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\analyzed")

def analyze_stream(stream_file):
    """Analyze a single stream"""

    print(f"\n[*] Analyzing: {stream_file.name}")

    with open(stream_file, 'rb') as f:
        data = f.read()

    print(f"    Size: {len(data):,} bytes")

    # Check for magic bytes
    magic = data[:4]
    print(f"    Magic: {magic.hex()}")

    # Check for ZIP
    if data[:2] == b'PK':
        print("    [+] ZIP archive detected!")

        import zipfile
        import io

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                print(f"    [+] ZIP contains {len(zf.namelist())} files")

                extract_dir = OUTPUT_DIR / stream_file.stem
                extract_dir.mkdir(parents=True, exist_ok=True)

                zf.extractall(extract_dir)
                print(f"    [+] Extracted to: {extract_dir}")

                for name in zf.namelist()[:20]:
                    print(f"        - {name}")

                return True

        except Exception as e:
            print(f"    [!] ZIP error: {e}")

    # Check for marshal data
    try:
        obj = marshal.loads(data)
        print(f"    [+] Marshal data: {type(obj)}")

        if isinstance(obj, dict):
            print(f"        Keys: {list(obj.keys())[:10]}")

    except:
        pass

    # Check for Python strings
    python_keywords = [b'__main__', b'__init__', b'import ', b'def ', b'class ']
    found_keywords = []

    for kw in python_keywords:
        if kw in data:
            found_keywords.append(kw.decode())

    if found_keywords:
        print(f"    [+] Python keywords found: {', '.join(found_keywords)}")

    # Search for .pyc references
    import re
    pyc_refs = re.findall(b'[\\x20-\\x7E]{3,50}\\.pyc', data)

    if pyc_refs:
        print(f"    [+] Found {len(set(pyc_refs))} .pyc references:")
        for ref in list(set(pyc_refs))[:10]:
            print(f"        - {ref.decode()}")

    # Look for structured data
    # Try to find repeated patterns that might be a file table
    return False

def main():
    print("="*60)
    print(" Zlib Stream Analyzer")
    print("="*60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for stream_file in sorted(STREAMS_DIR.glob("*.bin")):
        result = analyze_stream(stream_file)
        if result:
            success_count += 1

    print(f"\n{'='*60}")
    print(f"[*] Successfully processed: {success_count} streams")
    print(f"[*] Check: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
