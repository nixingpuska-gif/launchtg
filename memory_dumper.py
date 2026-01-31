#!/usr/bin/env python3
"""
Process Memory Dumper for Python executables
Searches memory for Python bytecode and modules
"""

import os
import sys
import time
import struct
import subprocess
from pathlib import Path

try:
    import psutil
except ImportError:
    subprocess.run(['pip', 'install', 'psutil'], check=True)
    import psutil

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\memory_dump"

# Python magic numbers
PYTHON_MAGICS = {
    b'\x61\x0d\x0d\x0a': 'Python 3.9',
    b'\x6f\x0d\x0d\x0a': 'Python 3.10',
    b'\xa7\x0d\x0d\x0a': 'Python 3.11',
    b'\xcb\x0d\x0d\x0a': 'Python 3.12',
    b'\xd1\x0d\x0d\x0a': 'Python 3.13',
}

def start_process():
    """Start the target process"""

    print(f"[*] Starting: {EXE_PATH}")

    try:
        proc = subprocess.Popen(
            [EXE_PATH],
            cwd=os.path.dirname(EXE_PATH),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"[+] Process started: PID {proc.pid}")
        return proc

    except Exception as e:
        print(f"[!] Failed: {e}")
        return None

def dump_process_memory(pid):
    """Dump memory regions from process"""

    print(f"\n[*] Dumping memory from PID {pid}...")

    try:
        process = psutil.Process(pid)
        print(f"[*] Process: {process.name()}")

        # Get memory maps
        try:
            maps = process.memory_maps()
        except:
            maps = []

        print(f"[*] Found {len(maps)} memory regions")

        output_path = Path(OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)

        # Use Windows API to read memory
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # Open process
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400

        h_process = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        if not h_process:
            print(f"[!] Failed to open process")
            return 0

        print(f"[+] Opened process handle: {h_process}")

        # Query memory regions
        from ctypes import c_void_p, c_size_t, byref, sizeof

        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BaseAddress", c_void_p),
                ("AllocationBase", c_void_p),
                ("AllocationProtect", wintypes.DWORD),
                ("RegionSize", c_size_t),
                ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD),
                ("Type", wintypes.DWORD),
            ]

        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        region_count = 0
        extracted_count = 0

        # Memory state constants
        MEM_COMMIT = 0x1000
        PAGE_READONLY = 0x02
        PAGE_READWRITE = 0x04
        PAGE_EXECUTE_READ = 0x20
        PAGE_EXECUTE_READWRITE = 0x40

        while address < 0x7FFFFFFFFFFF:
            result = kernel32.VirtualQueryEx(
                h_process,
                c_void_p(address),
                byref(mbi),
                sizeof(mbi)
            )

            if not result:
                break

            # Check if region is committed and readable
            if (mbi.State == MEM_COMMIT and
                mbi.Protect in [PAGE_READONLY, PAGE_READWRITE, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE]):

                region_count += 1

                # Read region
                buffer = ctypes.create_string_buffer(mbi.RegionSize)
                bytes_read = c_size_t(0)

                success = kernel32.ReadProcessMemory(
                    h_process,
                    c_void_p(mbi.BaseAddress),
                    buffer,
                    mbi.RegionSize,
                    byref(bytes_read)
                )

                if success and bytes_read.value > 0:
                    data = buffer.raw[:bytes_read.value]

                    # Search for Python bytecode
                    found_python = False

                    for magic, version in PYTHON_MAGICS.items():
                        if magic in data:
                            print(f"\n[+] Found {version} bytecode at 0x{mbi.BaseAddress:X}")

                            # Extract region
                            output_file = output_path / f"memory_{mbi.BaseAddress:016X}_{version.replace(' ', '_')}.bin"
                            with open(output_file, 'wb') as f:
                                f.write(data)

                            print(f"    Saved {bytes_read.value:,} bytes to {output_file.name}")

                            extracted_count += 1
                            found_python = True
                            break

                    # Also look for common Python strings
                    if not found_python:
                        python_markers = [b'__main__', b'__init__.py', b'.pyc', b'telethon', b'pyrogram']

                        for marker in python_markers:
                            if data.count(marker) >= 3:  # Multiple occurrences
                                print(f"\n[+] Found Python strings at 0x{mbi.BaseAddress:X}")

                                output_file = output_path / f"memory_{mbi.BaseAddress:016X}_strings.bin"
                                with open(output_file, 'wb') as f:
                                    f.write(data)

                                print(f"    Saved {bytes_read.value:,} bytes to {output_file.name}")

                                extracted_count += 1
                                break

            address = mbi.BaseAddress + mbi.RegionSize

        kernel32.CloseHandle(h_process)

        print(f"\n[*] Scanned {region_count} memory regions")
        print(f"[+] Extracted {extracted_count} regions with Python data")

        return extracted_count

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

def extract_pyc_from_memory(dump_dir):
    """Extract .pyc files from memory dumps"""

    print(f"\n[*] Extracting .pyc files from dumps...")

    pyc_output = Path(OUTPUT_DIR) / "extracted_pyc"
    pyc_output.mkdir(parents=True, exist_ok=True)

    count = 0

    for dump_file in Path(dump_dir).glob("*.bin"):
        with open(dump_file, 'rb') as f:
            data = f.read()

        # Search for Python magic bytes
        for magic, version in PYTHON_MAGICS.items():
            pos = 0
            while True:
                pos = data.find(magic, pos)
                if pos == -1:
                    break

                # Try to extract pyc (assume max 500KB per module)
                pyc_data = data[pos:pos+500000]

                # Save
                output_file = pyc_output / f"{dump_file.stem}_{pos:08X}.pyc"
                with open(output_file, 'wb') as f:
                    f.write(pyc_data)

                count += 1
                print(f"  [OK] Extracted .pyc from {dump_file.name} offset 0x{pos:X}")

                pos += len(magic)

    print(f"[+] Extracted {count} .pyc files")
    return count

def main():
    print("="*60)
    print(" Process Memory Dumper")
    print("="*60)

    # Start process
    proc = start_process()

    if not proc:
        return

    pid = proc.pid

    # Wait for initialization
    print("\n[*] Waiting 10 seconds for initialization...")
    time.sleep(10)

    # Dump memory
    extracted = dump_process_memory(pid)

    # Extract .pyc files
    if extracted > 0:
        extract_pyc_from_memory(OUTPUT_DIR)

    # Kill process
    print("\n[*] Terminating process...")
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        try:
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
        except:
            pass

    print(f"\n{'='*60}")
    print(f"[+] Memory dump complete!")
    print(f"[*] Check: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
