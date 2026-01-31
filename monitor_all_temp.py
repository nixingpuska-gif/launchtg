#!/usr/bin/env python3
"""Monitor ALL changes in TEMP folder"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

TEMP_DIR = Path(os.environ.get('TEMP', r'C:\Users\Nicita\AppData\Local\Temp'))
EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"

def get_folder_state():
    """Get current state of TEMP folder"""
    state = {}
    try:
        for item in TEMP_DIR.iterdir():
            try:
                stat = item.stat()
                state[str(item)] = (stat.st_mtime, stat.st_size if item.is_file() else 0)
            except:
                pass
    except:
        pass
    return state

def main():
    print("="*60)
    print(" TEMP Folder Monitor - All Changes")
    print("="*60)
    print(f"Monitoring: {TEMP_DIR}")
    print(f"Time: {datetime.now()}")

    # Get initial state
    before = get_folder_state()
    print(f"Initial items: {len(before)}")

    # Launch exe
    print(f"\n[*] Launching {EXE_PATH}...")
    try:
        proc = subprocess.Popen(
            f'cmd /c start "" "{EXE_PATH}"',
            shell=True,
            cwd=os.path.dirname(EXE_PATH)
        )
        print("[+] Launched")
    except Exception as e:
        print(f"[!] Failed: {e}")
        return

    # Wait and monitor
    print("[*] Monitoring changes for 30 seconds...")

    all_new = set()
    all_modified = set()

    for i in range(60):
        time.sleep(0.5)

        after = get_folder_state()

        # Find new items
        new_items = set(after.keys()) - set(before.keys())
        for item in new_items:
            if item not in all_new:
                all_new.add(item)
                print(f"\n  [NEW] {Path(item).name}")

        # Find modified items
        for item, (mtime, size) in after.items():
            if item in before:
                old_mtime, old_size = before[item]
                if mtime != old_mtime and item not in all_modified:
                    all_modified.add(item)
                    print(f"\n  [MOD] {Path(item).name}")

        before = after

        if i % 10 == 0:
            print(f"  {i//2}s...", end='', flush=True)

    print(f"\n\n{'='*60}")
    print(f"[*] Summary:")
    print(f"    New items: {len(all_new)}")
    print(f"    Modified items: {len(all_modified)}")

    if all_new:
        print(f"\n[+] NEW items created:")
        for item in sorted(all_new):
            p = Path(item)
            print(f"    - {p.name}")
            if p.is_dir():
                try:
                    files = list(p.rglob('*'))
                    print(f"      Contains {len(files)} items")
                    for f in files[:5]:
                        print(f"        {f.name}")
                except:
                    pass

    print("="*60)

if __name__ == "__main__":
    main()
