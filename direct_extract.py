#!/usr/bin/env python3
"""Direct extraction - monitors and runs exe in same process context"""

import os
import sys
import shutil
import time
import subprocess
import ctypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

TEMP_DIR = os.environ.get('TEMP', os.environ.get('TMP', r'C:\Users\Nicita\AppData\Local\Temp'))
EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def copy_mei_folder(mei_path, dest_path):
    """Copy MEI folder contents"""
    try:
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(mei_path, dest_path)
        return True
    except PermissionError:
        # Try copying file by file
        os.makedirs(dest_path, exist_ok=True)
        for root, dirs, files in os.walk(mei_path):
            rel_root = os.path.relpath(root, mei_path)
            dest_root = os.path.join(dest_path, rel_root)
            os.makedirs(dest_root, exist_ok=True)
            for f in files:
                try:
                    shutil.copy2(os.path.join(root, f), os.path.join(dest_root, f))
                except:
                    pass
        return True
    except Exception as e:
        print(f"Copy error: {e}")
        return False

def main():
    print("="*60)
    print(" LaunchTG Extractor")
    print("="*60)
    print(f"Admin: {is_admin()}")
    print(f"TEMP: {TEMP_DIR}")

    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get existing MEI folders
    existing = set()
    for item in os.listdir(TEMP_DIR):
        if item.startswith('_MEI'):
            existing.add(item)
    print(f"Existing _MEI: {len(existing)}")

    # Start exe using cmd
    print(f"\n[*] Starting LaunchTG.exe...")

    try:
        # Use cmd /c start to launch
        proc = subprocess.Popen(
            f'cmd /c start "" "{EXE_PATH}"',
            shell=True,
            cwd=os.path.dirname(EXE_PATH)
        )
        print(f"[+] Launched via cmd")
    except Exception as e:
        print(f"[!] Launch failed: {e}")
        return

    # Monitor for 60 seconds
    print("[*] Monitoring for _MEI folders...")

    found = None
    for i in range(120):
        for item in os.listdir(TEMP_DIR):
            if item.startswith('_MEI') and item not in existing:
                mei_path = os.path.join(TEMP_DIR, item)
                print(f"\n[+] FOUND: {item}")

                # Wait for files to be written
                time.sleep(2)

                # Check size
                try:
                    size = sum(f.stat().st_size for f in Path(mei_path).rglob('*') if f.is_file())
                    print(f"[*] Size: {size:,} bytes")
                except:
                    pass

                # Copy
                dest = output_path / "extracted" / item
                if copy_mei_folder(mei_path, str(dest)):
                    print(f"[+] Copied to {dest}")
                    found = dest
                    existing.add(item)

        if found:
            break

        time.sleep(0.5)
        if i % 10 == 0:
            print(f"  {i//2}s...", end='', flush=True)

    if not found:
        print("\n[!] No _MEI folder found")

        # Check for other extraction locations
        print("\n[*] Checking alternative locations...")

        alt_locations = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            os.path.join(os.environ.get('APPDATA', ''), 'Local', 'Temp'),
            r'C:\Windows\Temp',
        ]

        for loc in alt_locations:
            if os.path.exists(loc):
                for item in os.listdir(loc):
                    if item.startswith('_MEI'):
                        print(f"  Found in {loc}: {item}")

        return

    # Decompile
    print(f"\n[*] Decompiling...")
    decompiled_path = output_path / "decompiled"
    decompiled_path.mkdir(exist_ok=True)

    pyc_files = list(found.rglob("*.pyc"))
    print(f"[*] Found {len(pyc_files)} .pyc files")

    success = 0
    for pyc in pyc_files:
        try:
            rel = pyc.relative_to(found)
            out = decompiled_path / rel.with_suffix('.py')
            out.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                [sys.executable, '-m', 'uncompyle6', str(pyc)],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout:
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                success += 1
                print(f"  [OK] {rel}")
        except:
            pass

    print(f"\n[+] Decompiled {success}/{len(pyc_files)} files")
    print(f"[*] Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
