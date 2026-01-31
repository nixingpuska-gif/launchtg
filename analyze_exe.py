#!/usr/bin/env python3
"""Analyzer for LaunchTG.exe - detects packer type and extracts metadata"""

import struct
import os
import sys

def analyze_exe(filepath):
    """Analyze executable file to determine packer type"""

    print(f"[*] Analyzing: {filepath}")
    print(f"[*] File size: {os.path.getsize(filepath):,} bytes\n")

    with open(filepath, 'rb') as f:
        # Read first 8KB for signature detection
        header = f.read(8192)

        # Check for PyInstaller signatures
        pyinstaller_sigs = [
            b'MEI',
            b'PYZ-00.pyz',
            b'python',
            b'PyInstaller',
            b'_MEIPASS'
        ]

        print("[+] Checking for PyInstaller signatures:")
        for sig in pyinstaller_sigs:
            if sig in header:
                print(f"    ✓ Found: {sig.decode('utf-8', errors='ignore')}")

        # Read full file for deeper analysis
        f.seek(0)
        full_content = f.read()

        # Check for Python DLL references
        print("\n[+] Checking for Python DLL references:")
        import re
        python_dlls = re.findall(b'python[0-9]{2,3}\\.dll', full_content, re.IGNORECASE)
        if python_dlls:
            unique_dlls = set(python_dlls)
            for dll in unique_dlls:
                print(f"    ✓ Found: {dll.decode('utf-8', errors='ignore')}")

        # Search for PyInstaller archive marker
        print("\n[+] Searching for PyInstaller archive marker...")
        marker = b'MEI\014\013\012\013\016'  # PyInstaller magic bytes
        pos = full_content.find(marker)
        if pos != -1:
            print(f"    ✓ PyInstaller marker found at offset: {pos} (0x{pos:X})")

            # Try to read TOC (Table of Contents)
            f.seek(pos + len(marker))
            try:
                toc_pos = struct.unpack('!i', f.read(4))[0]
                toc_len = struct.unpack('!i', f.read(4))[0]
                print(f"    ✓ TOC Position: {toc_pos}")
                print(f"    ✓ TOC Length: {toc_len}")
            except:
                print("    ! Could not parse TOC metadata")

        # Check for Nuitka signatures
        print("\n[+] Checking for Nuitka signatures:")
        nuitka_sigs = [b'Nuitka', b'nuitka']
        for sig in nuitka_sigs:
            if sig in full_content:
                print(f"    ✓ Found: {sig.decode('utf-8')}")

        # Check for py2exe
        print("\n[+] Checking for py2exe signatures:")
        if b'py2exe' in full_content or b'PY2EXE' in full_content:
            print("    ✓ Found: py2exe signature")

        # Look for embedded resources
        print("\n[+] Searching for embedded Python resources:")
        pyz_refs = re.findall(b'[a-zA-Z0-9_-]+\\.pyz', full_content)
        if pyz_refs:
            print(f"    ✓ Found {len(set(pyz_refs))} .pyz references")
            for ref in list(set(pyz_refs))[:5]:
                print(f"        - {ref.decode('utf-8', errors='ignore')}")

        # Check for common Python libraries
        print("\n[+] Detecting embedded Python libraries:")
        common_libs = [
            b'telethon',
            b'pyrogram',
            b'requests',
            b'asyncio',
            b'sqlite3',
            b'colorama',
            b'beautifulsoup',
            b'pillow'
        ]

        found_libs = []
        for lib in common_libs:
            if lib in full_content:
                found_libs.append(lib.decode('utf-8'))

        if found_libs:
            print(f"    ✓ Found {len(found_libs)} libraries:")
            for lib in found_libs:
                print(f"        - {lib}")

    print("\n" + "="*60)
    print("[*] Analysis complete!")

    # Determine packer type
    if b'MEI' in header or b'PyInstaller' in full_content:
        print("[!] VERDICT: Likely PyInstaller packed executable")
        print("[*] Recommendation: Use pyinstxtractor.py to unpack")
    elif b'Nuitka' in full_content:
        print("[!] VERDICT: Likely Nuitka compiled executable")
    elif b'py2exe' in full_content:
        print("[!] VERDICT: Likely py2exe packed executable")
    else:
        print("[!] VERDICT: Unknown or custom packer")

    print("="*60)

if __name__ == "__main__":
    exe_path = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"

    if not os.path.exists(exe_path):
        print(f"[!] Error: File not found: {exe_path}")
        sys.exit(1)

    analyze_exe(exe_path)
