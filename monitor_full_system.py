#!/usr/bin/env python3
"""
Monitor ALL file system changes when LaunchTG runs
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def get_all_files_in_directory(directory):
    """Get all files in directory"""
    files = {}
    try:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                try:
                    stat = os.stat(full_path)
                    files[full_path] = (stat.st_mtime, stat.st_size)
                except:
                    pass
    except:
        pass
    return files

def main():
    print("="*60)
    print(" Full System File Monitor")
    print("="*60)

    # Directories to monitor
    monitor_dirs = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.environ.get('APPDATA', ''),
        os.environ.get('LOCALAPPDATA', ''),
        os.path.dirname(EXE_PATH),  # Program directory
        r'C:\Windows\Temp',
    ]

    monitor_dirs = [d for d in monitor_dirs if d and os.path.exists(d)]

    print(f"[*] Monitoring {len(monitor_dirs)} directories")
    for d in monitor_dirs:
        print(f"    - {d}")

    # Get initial state
    print("\n[*] Scanning initial state...")
    before = {}
    for d in monitor_dirs:
        print(f"  Scanning {d}...")
        before.update(get_all_files_in_directory(d))

    print(f"[*] Initial files: {len(before)}")

    # Start exe
    print(f"\n[*] Starting: {EXE_PATH}")

    try:
        proc = subprocess.Popen(
            [EXE_PATH],
            cwd=os.path.dirname(EXE_PATH),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"[+] Process started: PID {proc.pid}")
    except Exception as e:
        print(f"[!] Error: {e}")
        return

    # Monitor for 30 seconds
    print("\n[*] Monitoring changes for 30 seconds...")

    new_files = []
    modified_files = []

    for i in range(60):
        time.sleep(0.5)

        # Scan again
        after = {}
        for d in monitor_dirs:
            after.update(get_all_files_in_directory(d))

        # Find new files
        for path in after:
            if path not in before:
                if path not in new_files:
                    new_files.append(path)
                    print(f"\n  [NEW] {path}")

                    # If it's a directory with Python files, copy it
                    if os.path.isdir(path):
                        # Check for .pyc files
                        has_pyc = False
                        for root, dirs, files in os.walk(path):
                            for f in files:
                                if f.endswith('.pyc') or f.endswith('.pyd'):
                                    has_pyc = True
                                    break
                            if has_pyc:
                                break

                        if has_pyc:
                            print(f"    [!] Contains Python files! Copying...")
                            output_path = Path(OUTPUT_DIR) / "found" / Path(path).name
                            try:
                                import shutil
                                if output_path.exists():
                                    shutil.rmtree(output_path)
                                shutil.copytree(path, output_path)
                                print(f"    [OK] Copied to {output_path}")
                            except Exception as e:
                                print(f"    [!] Error: {e}")

            elif after[path] != before[path]:
                if path not in modified_files:
                    modified_files.append(path)

        before = after

        if i % 10 == 0:
            print(f"  {i//2}s...", end='', flush=True)

    # Kill process
    try:
        proc.terminate()
        print("\n[*] Process terminated")
    except:
        pass

    print(f"\n{'='*60}")
    print(f"[*] Summary:")
    print(f"    - New files: {len(new_files)}")
    print(f"    - Modified files: {len(modified_files)}")

    if new_files:
        print(f"\n[+] New files created:")
        for f in new_files[:30]:
            print(f"    - {f}")

    print(f"{'='*60}")

if __name__ == "__main__":
    main()
