#!/usr/bin/env python3
"""
Extract LaunchTG with valid license key
"""

import os
import sys
import shutil
import time
import subprocess
from pathlib import Path

TEMP_DIR = os.environ.get('TEMP', r'C:\Users\Nicita\AppData\Local\Temp')
EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"

def main():
    print("="*60)
    print(" LaunchTG Extraction with License Key")
    print("="*60)

    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get existing _MEI folders
    existing = set()
    for item in os.listdir(TEMP_DIR):
        if item.startswith('_MEI'):
            existing.add(item)

    print(f"[*] TEMP: {TEMP_DIR}")
    print(f"[*] Existing _MEI: {len(existing)}")
    print(f"[*] License key: ACTIVATED")

    # Start process
    print(f"\n[*] Starting LaunchTG.exe with license...")

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

    # Monitor for 90 seconds
    print("[*] Monitoring for PyInstaller extraction...")

    found_mei = None

    for i in range(180):  # 90 seconds
        try:
            for item in os.listdir(TEMP_DIR):
                if item.startswith('_MEI') and item not in existing:
                    mei_path = os.path.join(TEMP_DIR, item)
                    print(f"\n[+] FOUND _MEI FOLDER: {item}")

                    # Wait for extraction to complete
                    time.sleep(3)

                    # Get size
                    try:
                        size = sum(f.stat().st_size for f in Path(mei_path).rglob('*') if f.is_file())
                        print(f"[*] Size: {size:,} bytes")
                    except:
                        pass

                    # Copy folder
                    dest = output_path / "extracted" / item
                    try:
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(mei_path, dest)
                        print(f"[+] Copied to: {dest}")
                        found_mei = dest
                    except Exception as e:
                        print(f"[!] Copy error: {e}")
                        # Try file by file
                        dest.mkdir(parents=True, exist_ok=True)
                        for root, dirs, files in os.walk(mei_path):
                            rel_dir = Path(root).relative_to(mei_path)
                            (dest / rel_dir).mkdir(parents=True, exist_ok=True)
                            for f in files:
                                try:
                                    shutil.copy2(
                                        os.path.join(root, f),
                                        dest / rel_dir / f
                                    )
                                except:
                                    pass
                        found_mei = dest

                    existing.add(item)
                    break

            if found_mei:
                break

            time.sleep(0.5)
            if i % 10 == 0:
                print(f"  {i//2}s...", end='', flush=True)

        except KeyboardInterrupt:
            print("\n[!] Interrupted")
            break

    print("\n")

    if not found_mei:
        print("[!] No _MEI folder found")

        # Check all temp locations
        print("\n[*] Checking all temp locations...")

        all_temps = [
            TEMP_DIR,
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            r'C:\Windows\Temp',
        ]

        for temp_loc in all_temps:
            if os.path.exists(temp_loc):
                print(f"\n  Checking: {temp_loc}")
                for item in os.listdir(temp_loc):
                    if '_MEI' in item or 'python' in item.lower():
                        print(f"    - {item}")

        # Try to kill process
        try:
            proc.terminate()
        except:
            pass

        return

    # List extracted files
    print("[*] Listing extracted files...")
    files = list(found_mei.rglob("*"))
    print(f"[*] Total files: {len(files)}")

    pyc_files = [f for f in files if f.suffix == '.pyc' or (f.is_file() and not f.suffix)]
    pyd_files = [f for f in files if f.suffix == '.pyd']
    dll_files = [f for f in files if f.suffix == '.dll']

    print(f"    - .pyc files: {len(pyc_files)}")
    print(f"    - .pyd files: {len(pyd_files)}")
    print(f"    - .dll files: {len(dll_files)}")

    # Decompile .pyc files
    print(f"\n[*] Decompiling {len(pyc_files)} .pyc files...")

    decompiled_path = output_path / "decompiled"
    decompiled_path.mkdir(exist_ok=True)

    success = 0
    failed = 0

    for pyc in pyc_files:
        try:
            rel = pyc.relative_to(found_mei)
            out = decompiled_path / rel.with_suffix('.py')
            out.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                [sys.executable, '-m', 'uncompyle6', str(pyc)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                success += 1
                if success <= 20:
                    print(f"  [OK] {rel}")
            else:
                failed += 1

        except Exception as e:
            failed += 1

    print(f"\n[*] Decompilation results:")
    print(f"    - Success: {success}")
    print(f"    - Failed: {failed}")

    # Kill process
    try:
        proc.terminate()
        print("[*] Process terminated")
    except:
        pass

    print(f"\n{'='*60}")
    print(f"[+] EXTRACTION COMPLETE!")
    print(f"[*] Extracted files: {output_path / 'extracted'}")
    print(f"[*] Decompiled source: {decompiled_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
