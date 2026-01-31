#!/usr/bin/env python3
"""
AES Key Brute-Force for PyInstaller
Tries all 1,722 key candidates against encrypted .rsrc section
"""

import os
import struct
import zlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[!] Installing pycryptodome...")
    import subprocess
    subprocess.run(['pip', 'install', 'pycryptodome'], check=True)
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\decrypted"

def load_key_candidates():
    """Load key candidates from analysis"""

    key_file = Path(r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\key_analysis.txt")

    if not key_file.exists():
        print("[!] Generating key candidates...")
        # Generate from exe
        with open(EXE_PATH, 'rb') as f:
            data = f.read(500000)  # First 500KB

        candidates = []
        # Look for 16-byte sequences with high entropy
        for i in range(0, len(data) - 16, 4):
            chunk = data[i:i+16]

            # Skip if has too many nulls
            if chunk.count(b'\x00') > 4:
                continue

            # Check entropy
            unique = len(set(chunk))
            if unique >= 12:
                candidates.append(chunk)

        print(f"[*] Generated {len(candidates)} candidates")
        return candidates[:2000]  # Limit to 2000

    else:
        # Load from file
        candidates = []
        with open(key_file, 'r') as f:
            for line in f:
                if '0x' in line and ':' in line:
                    try:
                        hex_part = line.split(':')[1].strip()
                        key_bytes = bytes.fromhex(hex_part)
                        if len(key_bytes) == 16:
                            candidates.append(key_bytes)
                    except:
                        pass

        print(f"[*] Loaded {len(candidates)} candidates from file")
        return candidates

def try_decrypt_key(key, encrypted_data, offset=0):
    """Try to decrypt with given key"""

    try:
        # Try different AES modes
        modes = [
            (AES.MODE_CBC, b'\x00'*16),  # CBC with null IV
            (AES.MODE_ECB, None),         # ECB
            (AES.MODE_CFB, b'\x00'*16),   # CFB
        ]

        for mode, iv in modes:
            try:
                if iv:
                    cipher = AES.new(key, mode, iv)
                else:
                    cipher = AES.new(key, mode)

                # Try to decrypt first 64KB
                chunk_size = min(64*1024, len(encrypted_data) - offset)
                encrypted_chunk = encrypted_data[offset:offset+chunk_size]

                decrypted = cipher.decrypt(encrypted_chunk)

                # Check if it looks like valid data
                # Look for markers
                markers = [
                    b'PK\x03\x04',  # ZIP
                    b'PYZ',          # PyInstaller PYZ
                    b'import ',      # Python code
                    b'__main__',     # Python module
                    b'\x61\x0d\x0d\x0a',  # Python 3.9 magic
                    b'\x6f\x0d\x0d\x0a',  # Python 3.10 magic
                ]

                for marker in markers:
                    if marker in decrypted[:1024]:
                        return (key, mode, iv, decrypted, marker)

                # Check entropy - decrypted data should have lower entropy
                unique_bytes = len(set(decrypted[:1024]))
                if unique_bytes < 200:  # Lower than encrypted data
                    # Might be valid
                    if b'\x00' * 20 not in decrypted[:1024]:  # Not all zeros
                        return (key, mode, iv, decrypted, b'LOW_ENTROPY')

            except Exception as e:
                continue

    except Exception as e:
        pass

    return None

def brute_force_keys(encrypted_data, keys):
    """Brute force all keys in parallel"""

    print(f"[*] Trying {len(keys)} keys with {os.cpu_count()} threads...")

    successful = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(try_decrypt_key, key, encrypted_data): key for key in keys}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()

            if result:
                key, mode, iv, decrypted, marker = result
                print(f"\n[+] FOUND VALID KEY!")
                print(f"    Key: {key.hex()}")
                print(f"    Mode: {mode}")
                print(f"    Marker: {marker}")

                successful.append(result)

                # Save decrypted data
                output_file = Path(OUTPUT_DIR) / f"decrypted_{key.hex()[:16]}.bin"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, 'wb') as f:
                    f.write(decrypted)

                print(f"    Saved: {output_file}")

            if (i + 1) % 100 == 0:
                print(f"  Tried {i+1}/{len(keys)} keys...", end='\r')

    print(f"\n[*] Completed {len(keys)} keys")
    return successful

def extract_rsrc():
    """Extract .rsrc section"""

    with open(EXE_PATH, 'rb') as f:
        # Read DOS header
        dos = f.read(64)
        pe_offset = struct.unpack('<I', dos[60:64])[0]

        f.seek(pe_offset)
        f.read(4)  # PE sig

        # COFF
        coff = f.read(20)
        num_sections = struct.unpack('<H', coff[2:4])[0]
        opt_size = struct.unpack('<H', coff[16:18])[0]

        f.read(opt_size)

        # Find .rsrc
        for i in range(num_sections):
            section = f.read(40)
            name = section[:8].rstrip(b'\x00').decode()

            if name == '.rsrc':
                raw_size = struct.unpack('<I', section[16:20])[0]
                raw_ptr = struct.unpack('<I', section[20:24])[0]

                f.seek(raw_ptr)
                return f.read(raw_size)

    return None

def main():
    print("="*60)
    print(" AES Key Brute-Force Attack")
    print("="*60)

    # Extract .rsrc
    print("\n[*] Extracting .rsrc section...")
    rsrc_data = extract_rsrc()

    if not rsrc_data:
        print("[!] Failed to extract .rsrc")
        return

    print(f"[+] Extracted {len(rsrc_data):,} bytes")

    # Load keys
    print("\n[*] Loading key candidates...")
    keys = load_key_candidates()

    if not keys:
        print("[!] No keys to try")
        return

    # Brute force
    print(f"\n[*] Starting brute-force attack...")
    results = brute_force_keys(rsrc_data, keys)

    print(f"\n{'='*60}")
    if results:
        print(f"[+] SUCCESS! Found {len(results)} valid key(s)")
        for key, mode, iv, _, marker in results:
            print(f"    Key: {key.hex()}")
            print(f"    Mode: {mode}")
            print(f"    Marker: {marker}")
    else:
        print("[!] No valid keys found")
        print("[*] Try:")
        print("    1. Different encryption offsets")
        print("    2. Custom key derivation functions")
        print("    3. Memory dump approach")

    print("="*60)

if __name__ == "__main__":
    main()
