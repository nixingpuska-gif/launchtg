#!/usr/bin/env python3
"""
Ultimate PyInstaller/Python exe unpacker
Tries multiple methods to extract source code
"""

import os
import sys
import struct
import zlib
import marshal
import subprocess
from pathlib import Path

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def method_1_pyinstxtractor():
    """Try pyinstxtractor-ng"""
    print("\n[METHOD 1] PyInstaller Extractor NG...")

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pyinstxtractor_ng', EXE_PATH],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(EXE_PATH)
        )

        if result.returncode == 0:
            print("[+] Success!")
            return True
        else:
            print(f"[!] Failed: {result.stderr[:200]}")

    except Exception as e:
        print(f"[!] Error: {e}")

    return False

def method_2_extract_overlay():
    """Extract PE overlay"""
    print("\n[METHOD 2] PE Overlay Extraction...")

    try:
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

            # Find max section end
            max_end = 0
            for i in range(num_sections):
                section = f.read(40)
                raw_size = struct.unpack('<I', section[16:20])[0]
                raw_ptr = struct.unpack('<I', section[20:24])[0]
                end = raw_ptr + raw_size
                if end > max_end:
                    max_end = end

            # Get overlay
            f.seek(0, 2)
            file_size = f.tell()

            overlay_size = file_size - max_end

            if overlay_size > 1024:  # More than 1KB
                print(f"[*] Overlay size: {overlay_size:,} bytes at 0x{max_end:X}")

                f.seek(max_end)
                overlay = f.read()

                output_path = Path(OUTPUT_DIR)
                output_path.mkdir(parents=True, exist_ok=True)

                overlay_file = output_path / "overlay.bin"
                with open(overlay_file, 'wb') as out:
                    out.write(overlay)

                print(f"[+] Saved to: {overlay_file}")

                # Try to decompress
                try:
                    decompressed = zlib.decompress(overlay)
                    decomp_file = output_path / "overlay_decompressed.bin"
                    with open(decomp_file, 'wb') as out:
                        out.write(decompressed)
                    print(f"[+] Decompressed: {decomp_file}")
                    return True
                except:
                    pass

    except Exception as e:
        print(f"[!] Error: {e}")

    return False

def method_3_extract_all_zlib():
    """Extract all zlib streams"""
    print("\n[METHOD 3] Extract all zlib streams...")

    try:
        with open(EXE_PATH, 'rb') as f:
            data = f.read()

        output_path = Path(OUTPUT_DIR) / "zlib_streams"
        output_path.mkdir(parents=True, exist_ok=True)

        count = 0

        # Find all zlib headers
        for i in range(0, len(data) - 2):
            if data[i:i+2] in [b'\x78\x9c', b'\x78\x01', b'\x78\xda']:
                # Try to decompress
                for length in [1024*100, 1024*1024, 1024*1024*10]:
                    try:
                        chunk = data[i:i+length]
                        decompressed = zlib.decompress(chunk)

                        if len(decompressed) > 10000:  # Larger than 10KB
                            out_file = output_path / f"stream_{i:08X}.bin"
                            with open(out_file, 'wb') as out:
                                out.write(decompressed)

                            count += 1
                            if count <= 10:
                                print(f"  [OK] 0x{i:X}: {len(decompressed):,} bytes")

                            break
                    except:
                        continue

        print(f"[+] Extracted {count} zlib streams")
        if count > 0:
            return True

    except Exception as e:
        print(f"[!] Error: {e}")

    return False

def method_4_search_pyc():
    """Search for .pyc files directly in exe"""
    print("\n[METHOD 4] Search for embedded .pyc files...")

    try:
        with open(EXE_PATH, 'rb') as f:
            data = f.read()

        output_path = Path(OUTPUT_DIR) / "pyc_files"
        output_path.mkdir(parents=True, exist_ok=True)

        # Python magic numbers
        magics = {
            b'\x61\x0d\x0d\x0a': 'Python 3.9',
            b'\x6f\x0d\x0d\x0a': 'Python 3.10',
            b'\xa7\x0d\x0d\x0a': 'Python 3.11',
            b'\xcb\x0d\x0d\x0a': 'Python 3.12',
        }

        found = 0

        for magic, version in magics.items():
            pos = 0
            while True:
                pos = data.find(magic, pos)
                if pos == -1:
                    break

                # Try to extract
                try:
                    # Get potential .pyc file (up to 500KB)
                    pyc_data = data[pos:pos+500000]

                    out_file = output_path / f"file_{pos:08X}.pyc"
                    with open(out_file, 'wb') as out:
                        out.write(pyc_data)

                    found += 1
                    if found <= 5:
                        print(f"  [OK] {version} at 0x{pos:X}")

                except:
                    pass

                pos += 1

        print(f"[+] Found {found} potential .pyc files")
        if found > 0:
            return True

    except Exception as e:
        print(f"[!] Error: {e}")

    return False

def method_5_runtime_hook():
    """Create import hook to capture loaded modules"""
    print("\n[METHOD 5] Runtime import hook (requires manual exe run)...")

    hook_script = Path(OUTPUT_DIR) / "import_hook.py"

    hook_code = """
import sys
import marshal
import types
from pathlib import Path

output_dir = Path(r'""" + OUTPUT_DIR + """') / 'hooked_modules'
output_dir.mkdir(parents=True, exist_ok=True)

original_import = __builtins__.__import__

def hook_import(name, *args, **kwargs):
    module = original_import(name, *args, **kwargs)

    try:
        if hasattr(module, '__file__') and module.__file__:
            print(f"[HOOK] Loaded: {name} from {module.__file__}")

            # Try to get source
            if hasattr(module, '__cached__'):
                print(f"  Cached: {module.__cached__}")

    except:
        pass

    return module

__builtins__.__import__ = hook_import

print("[*] Import hook installed!")
"""

    with open(hook_script, 'w') as f:
        f.write(hook_code)

    print(f"[*] Hook script created: {hook_script}")
    print("[!] To use: Set PYTHONSTARTUP environment variable and run exe")

    return False

def main():
    print("="*60)
    print(" Ultimate Python EXE Unpacker")
    print("="*60)
    print(f"Target: {EXE_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*60)

    methods = [
        method_1_pyinstxtractor,
        method_2_extract_overlay,
        method_3_extract_all_zlib,
        method_4_search_pyc,
        method_5_runtime_hook,
    ]

    for method in methods:
        try:
            result = method()
            if result:
                print(f"\n[+] {method.__name__} SUCCESSFUL!")
        except Exception as e:
            print(f"\n[!] {method.__name__} crashed: {e}")

    print(f"\n{'='*60}")
    print(f"[*] Check {OUTPUT_DIR} for extracted files")
    print("="*60)

if __name__ == "__main__":
    main()
