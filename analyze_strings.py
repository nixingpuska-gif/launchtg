#!/usr/bin/env python3
"""Extract readable strings and analyze packer type"""

import re
import os
from collections import Counter

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def extract_strings(data, min_length=4):
    """Extract printable ASCII strings"""
    pattern = b'[\\x20-\\x7E]{' + str(min_length).encode() + b',}'
    return re.findall(pattern, data)

def main():
    print("="*60)
    print(" String Analysis & Packer Detection")
    print("="*60)

    with open(EXE_PATH, 'rb') as f:
        data = f.read()

    print(f"[*] File size: {len(data):,} bytes")

    # Extract strings
    print("\n[*] Extracting strings...")
    strings = extract_strings(data, 6)
    print(f"[*] Found {len(strings)} strings")

    # Analyze packer signatures
    print("\n[+] Packer Detection:")

    packers = {
        'PyInstaller': [b'PyInstaller', b'pyi-', b'MEI', b'PYZ'],
        'Nuitka': [b'Nuitka', b'nuitka'],
        'py2exe': [b'py2exe', b'run_w.exe'],
        'PyArmor': [b'pyarmor', b'PYARMOR'],
        'Cython': [b'cython', b'.pyx'],
        'cx_Freeze': [b'cx_Freeze', b'initscripts'],
    }

    detected = []
    for packer, sigs in packers.items():
        for sig in sigs:
            if sig in data:
                detected.append(packer)
                print(f"    [OK] {packer} signature found: {sig.decode(errors='ignore')}")
                break

    # Look for Python-related strings
    print("\n[+] Python-related strings:")

    python_keywords = [
        b'python',
        b'import',
        b'__main__',
        b'__init__',
        b'.pyc',
        b'.pyd',
        b'PYTHONPATH',
    ]

    for kw in python_keywords:
        count = data.count(kw)
        if count > 0:
            print(f"    '{kw.decode()}': {count} occurrences")

    # Find interesting strings
    print("\n[+] Interesting strings (first 50):")

    interesting = []
    keywords = [b'telegram', b'session', b'api', b'token', b'key', b'password',
                b'license', b'config', b'sqlite', b'.db', b'http', b'https']

    for s in strings:
        s_lower = s.lower()
        for kw in keywords:
            if kw in s_lower:
                interesting.append(s)
                break

    for s in interesting[:50]:
        try:
            print(f"    {s.decode()}")
        except:
            pass

    # Check if it's actually a different packer
    print("\n[+] Advanced packer detection:")

    if b'This program cannot be run in DOS mode' in data:
        print("    - Standard PE executable")

    if b'UPX!' in data or b'UPX0' in data or b'UPX1' in data:
        print("    - UPX compressed")

    if b'.NET' in data or b'mscoree.dll' in data:
        print("    - .NET assembly")

    if b'AutoIt' in data:
        print("    - AutoIt script")

    # Try to detect embedded archive
    print("\n[+] Embedded archive detection:")

    archive_sigs = [
        (b'PK\x03\x04', 'ZIP archive'),
        (b'Rar!\x1a\x07', 'RAR archive'),
        (b'\x1f\x8b\x08', 'GZIP compressed'),
        (b'7z\xbc\xaf\x27\x1c', '7-Zip archive'),
    ]

    for sig, desc in archive_sigs:
        pos = data.find(sig)
        if pos != -1:
            print(f"    {desc} at offset 0x{pos:X}")

    # Conclusion
    print(f"\n{'='*60}")
    print("[*] ANALYSIS RESULT:")

    if not detected:
        print("    [!] NO STANDARD PACKER DETECTED")
        print("    [*] This might be:")
        print("        - Custom packer")
        print("        - Memory-only extraction")
        print("        - Encrypted/obfuscated binary")
        print("\n    [*] Recommendation: Use dynamic analysis (debugger/memory dump)")
    else:
        print(f"    [+] Detected: {', '.join(set(detected))}")

    print("="*60)

    # Save strings to file
    output_file = os.path.join(OUTPUT_DIR, "extracted_strings.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
        for s in strings:
            try:
                f.write(s.decode() + '\n')
            except:
                pass

    print(f"\n[*] All strings saved to: {output_file}")

if __name__ == "__main__":
    main()
