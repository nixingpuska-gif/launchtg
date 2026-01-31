#!/usr/bin/env python3
"""
Extract encryption key from PyInstaller executable.
PyInstaller stores the AES key in the bootloader when using --key option.
"""

import os
import struct
import re
from pathlib import Path

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def find_pyinstaller_key(exe_path):
    """Search for PyInstaller encryption key in executable"""

    with open(exe_path, 'rb') as f:
        data = f.read()

    print(f"[*] Analyzing {exe_path}")
    print(f"[*] Size: {len(data):,} bytes")

    # Method 1: Look for key in bootloader strings
    print("\n[+] Method 1: Searching for key patterns...")

    # PyInstaller key is usually stored near specific strings
    key_indicators = [
        b'pyi_crypto_key',
        b'PYINSTALLER',
        b'MEI',
        b'archive_key',
    ]

    for indicator in key_indicators:
        pos = data.find(indicator)
        if pos != -1:
            # Look for 16/32 byte sequences nearby
            context = data[max(0, pos-100):pos+200]
            print(f"    Found '{indicator.decode(errors='ignore')}' at 0x{pos:X}")

    # Method 2: Look for AES key patterns (16 bytes of high entropy)
    print("\n[+] Method 2: Searching for AES key candidates...")

    # AES keys are often stored aligned and followed by specific patterns
    potential_keys = []

    # Search in bootloader section (first 500KB)
    bootloader = data[:500000]

    for i in range(0, len(bootloader) - 16, 4):
        chunk = bootloader[i:i+16]

        # Check if it looks like a key (high entropy, no nulls)
        if b'\x00\x00\x00\x00' not in chunk:
            unique_bytes = len(set(chunk))
            if unique_bytes >= 12:  # High entropy
                # Check if followed by recognizable pattern
                after = bootloader[i+16:i+32]
                if b'MEI' in after or b'PYZ' in after or b'\x00\x00\x00' in after:
                    potential_keys.append((i, chunk))

    if potential_keys:
        print(f"    Found {len(potential_keys)} potential keys")
        for pos, key in potential_keys[:5]:
            print(f"    0x{pos:X}: {key.hex()}")

    # Method 3: Look for tinyaes key storage
    print("\n[+] Method 3: Searching for tinyAES patterns...")

    # tinyAES stores key in specific format
    aes_patterns = [
        b'\x00' * 16,  # Empty key placeholder
        b'0123456789abcdef',  # Default key
    ]

    for pattern in aes_patterns:
        pos = data.find(pattern)
        if pos != -1:
            print(f"    Found pattern at 0x{pos:X}")

    # Method 4: Extract all 16-byte sequences that could be keys
    print("\n[+] Method 4: Extracting key candidates from .text section...")

    # Find .text section
    pe_offset = struct.unpack('<I', data[60:64])[0]
    num_sections = struct.unpack('<H', data[pe_offset+6:pe_offset+8])[0]
    opt_size = struct.unpack('<H', data[pe_offset+20:pe_offset+22])[0]

    section_offset = pe_offset + 24 + opt_size

    for i in range(num_sections):
        section = data[section_offset + i*40:section_offset + (i+1)*40]
        name = section[:8].rstrip(b'\x00').decode()
        raw_ptr = struct.unpack('<I', section[20:24])[0]
        raw_size = struct.unpack('<I', section[16:20])[0]

        if name == '.text':
            print(f"    .text section: 0x{raw_ptr:X} - 0x{raw_ptr+raw_size:X}")

            # Look for key initialization patterns
            text_data = data[raw_ptr:raw_ptr+raw_size]

            # Search for mov instructions that load key bytes
            key_loads = []
            for match in re.finditer(b'\xc7[\x00-\xff]{5}[\x00-\xff]{4}', text_data):
                # This could be mov [mem], imm32
                offset = match.start()
                key_loads.append((raw_ptr + offset, match.group()))

            if key_loads:
                print(f"    Found {len(key_loads)} potential key load instructions")

    # Method 5: Try to find the key by looking for pyimod patterns
    print("\n[+] Method 5: Searching for pyimod crypto patterns...")

    pyimod_pattern = b'pyimod'
    pos = data.find(pyimod_pattern)
    if pos != -1:
        print(f"    Found pyimod at 0x{pos:X}")
        # Key might be nearby
        context = data[pos-32:pos+128]
        print(f"    Context: {context[:64].hex()}")

    # Save all findings
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)

    with open(output_path / "key_analysis.txt", 'w') as f:
        f.write("PyInstaller Key Analysis\n")
        f.write("="*60 + "\n")
        f.write(f"File: {exe_path}\n")
        f.write(f"Size: {len(data):,} bytes\n\n")

        if potential_keys:
            f.write("Potential Keys:\n")
            for pos, key in potential_keys[:20]:
                f.write(f"  0x{pos:X}: {key.hex()}\n")

    print(f"\n[*] Analysis saved to {output_path / 'key_analysis.txt'}")

    return potential_keys

def try_decrypt_with_key(exe_path, key):
    """Try to decrypt PyInstaller archive with given key"""
    try:
        from Crypto.Cipher import AES
    except ImportError:
        print("[!] PyCryptodome not available")
        return False

    # This would attempt decryption - complex implementation
    return False

if __name__ == "__main__":
    keys = find_pyinstaller_key(EXE_PATH)

    if keys:
        print(f"\n[*] Found {len(keys)} potential encryption keys")
        print("[*] Manual decryption may be required")
