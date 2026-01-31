#!/usr/bin/env python3
"""Check encryption type and protection method"""

import os

def check_protection(rsrc_file):
    """Check what protection is used"""

    with open(rsrc_file, 'rb') as f:
        data = f.read()

    print(f"[*] Checking protection methods...")

    # Find AES context
    aes_pos = data.find(b'AES')
    if aes_pos != -1:
        context = data[aes_pos-50:aes_pos+100]
        print(f"\n[+] AES marker context at 0x{aes_pos:X}:")
        print(f"    Hex: {context.hex()}")

        # Check for readable text
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)
        print(f"    ASCII: {text}")

    # Check for PyInstaller encryption key
    print(f"\n[+] Searching for PyInstaller encryption markers...")

    # PyInstaller with --key stores key in bootloader
    key_markers = [
        b'_PYARMOR',
        b'pyimod00_crypto_key',
        b'CRYPTO_KEY',
        b'archive_key',
    ]

    for marker in key_markers:
        if marker in data:
            pos = data.find(marker)
            print(f"    [OK] {marker.decode()} found at 0x{pos:X}")
            context = data[pos:pos+100]
            print(f"        Context: {context}")

    # Check for Cython
    print(f"\n[+] Checking for Cython markers...")
    cython_markers = [b'cython', b'Cython', b'.pyx', b'_cython']
    for marker in cython_markers:
        if marker in data:
            print(f"    [OK] {marker.decode()} found")

    # Check for Nuitka
    print(f"\n[+] Checking for Nuitka markers...")
    nuitka_markers = [b'nuitka', b'Nuitka', b'NUITKA']
    for marker in nuitka_markers:
        if marker in data:
            print(f"    [OK] {marker.decode()} found")

    # Check for common Python library strings that would survive encryption
    print(f"\n[+] Checking for unencrypted Python strings...")

    strings_to_find = [
        b'Traceback',
        b'Exception',
        b'Error',
        b'python',
        b'import',
        b'.dll',
        b'.pyd',
    ]

    for s in strings_to_find:
        count = data.count(s)
        if count > 0:
            pos = data.find(s)
            print(f"    '{s.decode()}': {count} occurrences, first at 0x{pos:X}")

    # Try to find PyInstaller runtime files
    print(f"\n[+] Searching for PyInstaller runtime references...")

    runtime_files = [
        b'_internal',
        b'_MEI',
        b'base_library',
        b'pyi_rth',
        b'pyiboot',
    ]

    for rf in runtime_files:
        if rf in data:
            pos = data.find(rf)
            print(f"    [OK] {rf.decode()} at 0x{pos:X}")

    # Check for UPX
    print(f"\n[+] Checking for UPX...")
    if b'UPX' in data:
        print(f"    [OK] UPX markers found")

    # Final verdict
    print(f"\n{'='*60}")
    print("[*] ANALYSIS SUMMARY:")

    if b'AES' in data or b'Crypto' in data:
        print("    - Archive appears to be ENCRYPTED")
        print("    - PyInstaller with --key or custom encryption")

    if b'PyInstaller' in data:
        print("    - PyInstaller packer detected")

    if b'pyarmor' in data.lower():
        print("    - PyArmor protection detected")

    print(f"\n[!] To decrypt, you would need:")
    print("    1. The encryption key (usually 16 bytes for AES)")
    print("    2. Or runtime extraction (run exe and dump memory)")
    print("    3. Or hook import functions during execution")
    print(f"{'='*60}")

if __name__ == "__main__":
    rsrc_file = r"C:\Users\Nicita\Desktop\LaunchTG_extracted\rsrc_section.bin"
    check_protection(rsrc_file)
