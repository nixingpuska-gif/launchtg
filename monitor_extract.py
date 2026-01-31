#!/usr/bin/env python3
"""
Background monitor - run this, then manually start LaunchTG.exe as Administrator
"""

import os
import sys
import shutil
import time
import subprocess
from pathlib import Path

TEMP_DIR = os.environ.get('TEMP', r'C:\Users\Nicita\AppData\Local\Temp')
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def monitor_and_extract():
    output_path = Path(OUTPUT_DIR)
    extracted_path = output_path / "extracted"
    decompiled_path = output_path / "decompiled"

    output_path.mkdir(parents=True, exist_ok=True)
    extracted_path.mkdir(exist_ok=True)
    decompiled_path.mkdir(exist_ok=True)

    # Get existing _MEI directories
    existing_mei = set()
    for item in os.listdir(TEMP_DIR):
        if item.startswith('_MEI'):
            existing_mei.add(item)

    print("="*60)
    print(" PyInstaller Runtime Extractor")
    print("="*60)
    print(f"\n[*] Monitoring: {TEMP_DIR}")
    print(f"[*] Output: {OUTPUT_DIR}")
    print(f"[*] Existing _MEI folders: {len(existing_mei)}")
    print(f"\n{'='*60}")
    print("[!] NOW RUN LaunchTG.exe AS ADMINISTRATOR!")
    print("[!] Right-click -> Run as administrator")
    print(f"{'='*60}\n")

    found_mei = None
    start_time = time.time()
    timeout = 120  # 2 minutes

    while time.time() - start_time < timeout:
        try:
            for item in os.listdir(TEMP_DIR):
                if item.startswith('_MEI') and item not in existing_mei:
                    mei_path = os.path.join(TEMP_DIR, item)
                    print(f"\n[+] FOUND: {item}")

                    time.sleep(3)  # Wait for extraction

                    dest = extracted_path / item
                    try:
                        shutil.copytree(mei_path, dest, dirs_exist_ok=True)
                        print(f"[+] Copied to: {dest}")
                        found_mei = dest
                    except Exception as e:
                        print(f"[!] Error: {e}")
                        # Try individual files
                        dest.mkdir(exist_ok=True)
                        for f in os.listdir(mei_path):
                            try:
                                src = os.path.join(mei_path, f)
                                if os.path.isfile(src):
                                    shutil.copy2(src, dest / f)
                                else:
                                    shutil.copytree(src, dest / f, dirs_exist_ok=True)
                            except:
                                pass
                        found_mei = dest

                    existing_mei.add(item)

                    # Found! Now decompile
                    if found_mei:
                        print(f"\n[*] Starting decompilation...")

                        pyc_files = list(found_mei.rglob("*.pyc"))
                        print(f"[*] Found {len(pyc_files)} .pyc files")

                        success = 0
                        for pyc in pyc_files:
                            try:
                                rel = pyc.relative_to(found_mei)
                                out = decompiled_path / rel.with_suffix('.py')
                                out.parent.mkdir(parents=True, exist_ok=True)

                                result = subprocess.run(
                                    [sys.executable, '-m', 'uncompyle6', str(pyc)],
                                    capture_output=True, text=True, timeout=30
                                )

                                if result.returncode == 0:
                                    with open(out, 'w', encoding='utf-8') as f:
                                        f.write(result.stdout)
                                    success += 1
                                    print(f"    [OK] {rel}")
                            except Exception as e:
                                pass

                        print(f"\n[+] Decompiled {success}/{len(pyc_files)} files")
                        print(f"\n{'='*60}")
                        print(f"[+] DONE! Check: {OUTPUT_DIR}")
                        print(f"{'='*60}")
                        return True

            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n[!] Stopped")
            return False

    print(f"\n[!] Timeout - no extraction detected")
    return False

if __name__ == "__main__":
    monitor_and_extract()
