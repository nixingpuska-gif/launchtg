#!/usr/bin/env python3
"""Analyze extracted zlib files"""

import os

def analyze_extracted_files(directory):
    """Analyze extracted files"""

    for filename in os.listdir(directory):
        if not filename.endswith('.bin'):
            continue

        filepath = os.path.join(directory, filename)

        with open(filepath, 'rb') as f:
            data = f.read()

        print(f"\n{'='*60}")
        print(f"[*] File: {filename}")
        print(f"[*] Size: {len(data):,} bytes")

        # First 64 bytes hex
        print(f"\n[+] First 64 bytes (hex):")
        print(data[:64].hex())

        # First 64 bytes as ASCII (printable chars only)
        print(f"\n[+] First 256 bytes (ASCII printable):")
        ascii_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:256])
        print(ascii_text)

        # Search for patterns
        print(f"\n[+] Pattern search:")

        patterns = [
            (b'PNG', 'PNG image'),
            (b'JFIF', 'JPEG image'),
            (b'GIF8', 'GIF image'),
            (b'<?xml', 'XML data'),
            (b'import', 'Python import'),
            (b'def ', 'Python function'),
            (b'class ', 'Python class'),
            (b'function', 'JavaScript function'),
            (b'<!DOCTYPE', 'HTML document'),
            (b'PK', 'ZIP archive'),
            (b'Rar', 'RAR archive'),
            (b'SQLite', 'SQLite database'),
        ]

        for pattern, desc in patterns:
            if pattern in data:
                pos = data.find(pattern)
                print(f"    [OK] {desc} at offset 0x{pos:X}")

        # Look for text strings
        print(f"\n[+] Readable strings (first 20):")
        import re
        strings = re.findall(b'[A-Za-z0-9_. ]{6,}', data)
        for s in strings[:20]:
            try:
                print(f"    - {s.decode('utf-8')}")
            except:
                pass

if __name__ == "__main__":
    directory = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\archives"
    analyze_extracted_files(directory)
