#!/usr/bin/env python3
"""Simple memory dumper without external dependencies"""

import os
import sys
import time
import struct
import subprocess
from pathlib import Path
import ctypes
from ctypes import wintypes, c_void_p, c_size_t, byref, sizeof

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\memory_dump_simple"

PYTHON_MAGICS = {
    b'\x61\x0d\x0d\x0a': 'Python_3.9',
    b'\x6f\x0d\x0d\x0a': 'Python_3.10',
    b'\xa7\x0d\x0d\x0a': 'Python_3.11',
    b'\xcb\x0d\x0d\x0a': 'Python_3.12',
}

def main():
    print("="*60)
    print(" Simple Memory Dumper")
    print("="*60)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Start process
    print(f"\n[*] Starting: {EXE_PATH}")

    proc = subprocess.Popen(
        [EXE_PATH],
        cwd=os.path.dirname(EXE_PATH),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    print(f"[+] PID: {proc.pid}")

    # Wait
    print("[*] Waiting 15 seconds...")
    time.sleep(15)

    # Open process
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400

    h_process = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
        False,
        proc.pid
    )

    if not h_process:
        print("[!] Failed to open process")
        proc.terminate()
        return

    print(f"[+] Opened process")

    # Memory info structure
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
    extracted = 0

    MEM_COMMIT = 0x1000
    PAGE_READONLY = 0x02
    PAGE_READWRITE = 0x04

    print("[*] Scanning memory...")

    while address < 0x7FFFFFFFFFFF and extracted < 50:  # Limit to 50 regions
        result = kernel32.VirtualQueryEx(
            h_process,
            c_void_p(address),
            byref(mbi),
            sizeof(mbi)
        )

        if not result:
            break

        if (mbi.State == MEM_COMMIT and
            mbi.RegionSize < 100*1024*1024 and  # Skip huge regions
            mbi.Protect in [PAGE_READONLY, PAGE_READWRITE]):

            # Read
            buffer = ctypes.create_string_buffer(mbi.RegionSize)
            bytes_read = c_size_t(0)

            success = kernel32.ReadProcessMemory(
                h_process,
                c_void_p(mbi.BaseAddress),
                buffer,
                mbi.RegionSize,
                byref(bytes_read)
            )

            if success and bytes_read.value > 1000:
                data = buffer.raw[:bytes_read.value]

                # Check for Python
                has_python = False

                for magic, version in PYTHON_MAGICS.items():
                    if magic in data:
                        has_python = True
                        break

                # Check for strings
                if not has_python:
                    markers = [b'__main__', b'import ', b'.pyc']
                    count = sum(data.count(m) for m in markers)

                    if count >= 5:
                        has_python = True

                if has_python:
                    output_file = Path(OUTPUT_DIR) / f"mem_{mbi.BaseAddress:016X}.bin"
                    with open(output_file, 'wb') as f:
                        f.write(data)

                    extracted += 1
                    print(f"  [{extracted}] 0x{mbi.BaseAddress:X} ({bytes_read.value:,} bytes)")

        if mbi.BaseAddress is not None:
            address = mbi.BaseAddress + mbi.RegionSize
        else:
            address += 0x10000  # Skip if null

    kernel32.CloseHandle(h_process)

    # Kill process
    proc.terminate()

    print(f"\n[+] Extracted {extracted} memory regions")
    print(f"[*] Output: {OUTPUT_DIR}")

    # Search for .pyc in dumps
    print("\n[*] Searching for .pyc files...")

    pyc_dir = Path(OUTPUT_DIR) / "pyc_files"
    pyc_dir.mkdir(exist_ok=True)

    pyc_count = 0

    for dump_file in Path(OUTPUT_DIR).glob("mem_*.bin"):
        with open(dump_file, 'rb') as f:
            data = f.read()

        for magic, version in PYTHON_MAGICS.items():
            pos = 0
            while True:
                pos = data.find(magic, pos)
                if pos == -1:
                    break

                # Extract
                pyc_data = data[pos:min(pos+500000, len(data))]

                output_file = pyc_dir / f"{dump_file.stem}_{pos:08X}_{version}.pyc"
                with open(output_file, 'wb') as f:
                    f.write(pyc_data)

                pyc_count += 1
                print(f"  [OK] {output_file.name}")

                pos += len(magic)

    print(f"\n[+] Found {pyc_count} .pyc files")
    print("="*60)

if __name__ == "__main__":
    main()
