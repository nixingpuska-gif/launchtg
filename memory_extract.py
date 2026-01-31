#!/usr/bin/env python3
"""
Memory-based extraction for PyInstaller executables.
Dumps Python modules from running process memory.
"""

import os
import sys
import time
import subprocess
import ctypes
from ctypes import wintypes
from pathlib import Path

# Windows API
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def get_process_by_name(name):
    """Find process by name"""
    import subprocess
    result = subprocess.run(
        ['tasklist', '/FI', f'IMAGENAME eq {name}', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if name.lower() in line.lower():
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except:
                    pass
    return None

def dump_process_strings(pid, output_file):
    """Dump readable strings from process memory"""
    try:
        import pymem
        pm = pymem.Pymem(pid)

        print(f"[*] Connected to process {pid}")
        print(f"[*] Base address: {hex(pm.base_address)}")

        # Get all modules
        modules = list(pm.list_modules())
        print(f"[*] Found {len(modules)} modules")

        # Look for Python-related modules
        python_modules = []
        for mod in modules:
            name = mod.name.lower()
            if 'python' in name or '.pyd' in name:
                python_modules.append(mod)
                print(f"    - {mod.name}: {hex(mod.lpBaseOfDll)}")

        pm.close_process()
        return True

    except ImportError:
        print("[!] pymem not available, using alternative method")
        return False
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

def find_pyinstaller_temp():
    """Find PyInstaller temp folder by checking all possible locations"""
    locations = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Temp'),
        r'C:\Windows\Temp',
    ]

    for loc in locations:
        if not os.path.exists(loc):
            continue

        for item in os.listdir(loc):
            full_path = os.path.join(loc, item)
            if os.path.isdir(full_path):
                # Check for PyInstaller markers
                if item.startswith('_MEI') or item.startswith('_MEI'):
                    return full_path

                # Check for Python DLLs inside
                try:
                    for f in os.listdir(full_path):
                        if 'python' in f.lower() and f.endswith('.dll'):
                            return full_path
                except:
                    pass

    return None

def main():
    print("="*60)
    print(" PyInstaller Memory Extractor")
    print("="*60)

    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    # Start the process
    print(f"\n[*] Starting: {EXE_PATH}")

    try:
        proc = subprocess.Popen(
            [EXE_PATH],
            cwd=os.path.dirname(EXE_PATH),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"[+] Process started: PID {proc.pid}")
    except Exception as e:
        # Try via cmd
        try:
            subprocess.Popen(
                f'cmd /c start "" "{EXE_PATH}"',
                shell=True,
                cwd=os.path.dirname(EXE_PATH)
            )
            print("[+] Started via cmd")
            time.sleep(2)
            pid = get_process_by_name("LaunchTG.exe")
            if pid:
                print(f"[+] Found PID: {pid}")
        except Exception as e2:
            print(f"[!] Failed: {e2}")
            return

    # Wait for process to initialize
    print("[*] Waiting for initialization...")
    time.sleep(5)

    # Try to find temp folder
    print("\n[*] Searching for extraction folder...")
    temp_folder = find_pyinstaller_temp()

    if temp_folder:
        print(f"[+] Found: {temp_folder}")

        # Copy contents
        dest = output_path / "extracted"
        try:
            import shutil
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(temp_folder, dest)
            print(f"[+] Copied to: {dest}")
        except Exception as e:
            print(f"[!] Copy error: {e}")
    else:
        print("[!] No extraction folder found")

        # Try memory dump
        pid = get_process_by_name("LaunchTG.exe")
        if pid:
            print(f"\n[*] Attempting memory analysis of PID {pid}...")
            dump_process_strings(pid, output_path / "memory_strings.txt")

    # Kill process
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'LaunchTG.exe'],
                      capture_output=True)
        print("[*] Process terminated")
    except:
        pass

if __name__ == "__main__":
    main()
