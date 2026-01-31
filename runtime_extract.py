#!/usr/bin/env python3
"""
Runtime extraction script for PyInstaller executables.
Monitors temp folder for _MEI* directories created by PyInstaller.

USAGE:
1. Run this script FIRST
2. Then run LaunchTG.exe
3. Script will detect and copy extracted files
"""

import os
import shutil
import time
import sys
from pathlib import Path
from datetime import datetime

def get_temp_dir():
    """Get Windows temp directory"""
    return os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp'))

def monitor_temp_folder(output_dir, timeout=120):
    """Monitor temp folder for PyInstaller extraction"""

    temp_dir = get_temp_dir()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[*] Runtime Extraction Script")
    print(f"[*] Monitoring: {temp_dir}")
    print(f"[*] Output: {output_dir}")
    print(f"[*] Timeout: {timeout} seconds")
    print(f"\n{'='*60}")
    print("[!] NOW RUN LaunchTG.exe AND WAIT...")
    print(f"{'='*60}\n")

    # Get existing _MEI directories
    existing_mei = set()
    for item in os.listdir(temp_dir):
        if item.startswith('_MEI'):
            existing_mei.add(item)

    print(f"[*] Existing _MEI directories: {len(existing_mei)}")

    start_time = time.time()
    found_new = False

    while time.time() - start_time < timeout:
        try:
            # Check for new _MEI directories
            for item in os.listdir(temp_dir):
                if item.startswith('_MEI') and item not in existing_mei:
                    mei_path = os.path.join(temp_dir, item)

                    print(f"\n[+] NEW PYINSTALLER DIRECTORY FOUND: {item}")
                    print(f"[*] Path: {mei_path}")

                    # Wait a bit for extraction to complete
                    time.sleep(2)

                    # Copy contents
                    dest_path = output_path / item
                    print(f"[*] Copying to: {dest_path}")

                    try:
                        shutil.copytree(mei_path, dest_path)
                        print(f"[+] Successfully copied!")

                        # List contents
                        files = list(dest_path.rglob('*'))
                        print(f"[*] Copied {len(files)} items")

                        # Show interesting files
                        print(f"\n[+] Interesting files:")
                        for f in files:
                            if f.suffix in ['.pyc', '.pyo', '.pyd', '.dll', '.so']:
                                print(f"    - {f.relative_to(dest_path)}")

                        found_new = True

                    except Exception as e:
                        print(f"[!] Copy error: {e}")

                    existing_mei.add(item)

            # Also check for other Python-related temp files
            for item in os.listdir(temp_dir):
                full_path = os.path.join(temp_dir, item)

                # Check for PYZ files or .pyc files
                if item.endswith(('.pyc', '.pyo', '.pyz')) and item not in existing_mei:
                    print(f"[+] Found Python file: {item}")
                    try:
                        shutil.copy(full_path, output_path / item)
                        print(f"    Copied!")
                    except:
                        pass
                    existing_mei.add(item)

            time.sleep(0.5)
            sys.stdout.write('.')
            sys.stdout.flush()

        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
            break

        except Exception as e:
            print(f"\n[!] Error: {e}")

    print(f"\n\n{'='*60}")

    if found_new:
        print("[+] Extraction complete!")
        print(f"[*] Check {output_dir} for extracted files")

        # Try to decompile .pyc files
        print(f"\n[*] To decompile .pyc files, use:")
        print(f"    pip install uncompyle6")
        print(f"    uncompyle6 -o output_dir/ *.pyc")
    else:
        print("[!] No new PyInstaller directories found")
        print("[*] Make sure LaunchTG.exe was running during monitoring")

    print(f"{'='*60}")

if __name__ == "__main__":
    output_dir = r"C:\Users\Nicita\Desktop\LaunchTG_runtime_extract"
    monitor_temp_folder(output_dir, timeout=120)
