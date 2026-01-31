#!/usr/bin/env python3
"""
Automatic PyInstaller extraction and decompilation script.
Runs the target exe, captures extracted files, and decompiles them.
"""

import os
import sys
import shutil
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Configuration
EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE"
TEMP_DIR = os.environ.get('TEMP', os.environ.get('TMP', r'C:\Users\Nicita\AppData\Local\Temp'))

class PyInstallerExtractor:
    def __init__(self):
        self.output_path = Path(OUTPUT_DIR)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.extracted_path = self.output_path / "extracted"
        self.decompiled_path = self.output_path / "decompiled"
        self.extracted_path.mkdir(exist_ok=True)
        self.decompiled_path.mkdir(exist_ok=True)

        self.existing_mei = set()
        self.found_mei = None
        self.stop_monitoring = False

    def get_existing_mei(self):
        """Get list of existing _MEI directories"""
        try:
            for item in os.listdir(TEMP_DIR):
                if item.startswith('_MEI'):
                    self.existing_mei.add(item)
            print(f"[*] Found {len(self.existing_mei)} existing _MEI directories")
        except Exception as e:
            print(f"[!] Error scanning temp: {e}")

    def monitor_temp(self):
        """Monitor temp folder for new _MEI directories"""
        print(f"[*] Monitoring {TEMP_DIR} for PyInstaller extraction...")

        while not self.stop_monitoring:
            try:
                for item in os.listdir(TEMP_DIR):
                    if item.startswith('_MEI') and item not in self.existing_mei:
                        mei_path = os.path.join(TEMP_DIR, item)
                        print(f"\n[+] FOUND NEW: {item}")

                        # Wait for extraction to complete
                        time.sleep(3)

                        # Copy files
                        dest = self.extracted_path / item
                        try:
                            shutil.copytree(mei_path, dest)
                            print(f"[+] Copied to: {dest}")
                            self.found_mei = dest
                        except Exception as e:
                            print(f"[!] Copy error: {e}")
                            # Try copying individual files
                            try:
                                dest.mkdir(exist_ok=True)
                                for f in os.listdir(mei_path):
                                    src = os.path.join(mei_path, f)
                                    try:
                                        if os.path.isfile(src):
                                            shutil.copy2(src, dest / f)
                                        else:
                                            shutil.copytree(src, dest / f)
                                    except:
                                        pass
                                self.found_mei = dest
                            except:
                                pass

                        self.existing_mei.add(item)

                time.sleep(0.5)
            except Exception as e:
                time.sleep(1)

    def run_exe(self):
        """Run the target executable"""
        print(f"\n[*] Starting: {EXE_PATH}")
        try:
            # Start process (don't wait for it to complete)
            process = subprocess.Popen(
                [EXE_PATH],
                cwd=os.path.dirname(EXE_PATH),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            print(f"[+] Process started with PID: {process.pid}")
            return process
        except Exception as e:
            print(f"[!] Failed to start exe: {e}")
            return None

    def decompile_pyc_files(self):
        """Decompile all .pyc files found"""
        if not self.found_mei:
            print("[!] No extracted files to decompile")
            return

        print(f"\n[*] Decompiling .pyc files from {self.found_mei}...")

        # Find all .pyc files
        pyc_files = list(self.found_mei.rglob("*.pyc"))
        print(f"[*] Found {len(pyc_files)} .pyc files")

        # Also look for files without extension that might be .pyc
        for f in self.found_mei.rglob("*"):
            if f.is_file() and not f.suffix:
                # Check if it's a .pyc file by magic bytes
                try:
                    with open(f, 'rb') as fp:
                        magic = fp.read(4)
                        # Python 3.x magic numbers
                        if magic[2:4] == b'\r\n':
                            pyc_files.append(f)
                except:
                    pass

        print(f"[*] Total potential .pyc files: {len(pyc_files)}")

        decompiled_count = 0
        failed_count = 0

        for pyc_file in pyc_files:
            try:
                # Create output path
                rel_path = pyc_file.relative_to(self.found_mei)
                out_file = self.decompiled_path / rel_path.with_suffix('.py')
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Try uncompyle6
                result = subprocess.run(
                    ['python', '-m', 'uncompyle6', '-o', str(out_file), str(pyc_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and out_file.exists():
                    decompiled_count += 1
                    if decompiled_count <= 10:
                        print(f"    [OK] {rel_path}")
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1

        print(f"\n[*] Decompilation results:")
        print(f"    - Success: {decompiled_count}")
        print(f"    - Failed: {failed_count}")

    def list_extracted_files(self):
        """List all extracted files"""
        if not self.found_mei:
            return

        print(f"\n[*] Extracted files:")

        categories = {
            'Python bytecode (.pyc)': [],
            'Python extensions (.pyd)': [],
            'DLLs (.dll)': [],
            'Other': []
        }

        for f in self.found_mei.rglob("*"):
            if f.is_file():
                if f.suffix == '.pyc':
                    categories['Python bytecode (.pyc)'].append(f.name)
                elif f.suffix == '.pyd':
                    categories['Python extensions (.pyd)'].append(f.name)
                elif f.suffix == '.dll':
                    categories['DLLs (.dll)'].append(f.name)
                else:
                    categories['Other'].append(f.name)

        for cat, files in categories.items():
            if files:
                print(f"\n  {cat}: {len(files)} files")
                for f in files[:10]:
                    print(f"    - {f}")
                if len(files) > 10:
                    print(f"    ... and {len(files) - 10} more")

    def run(self):
        """Main execution"""
        print("="*60)
        print(" PyInstaller Runtime Extraction & Decompilation")
        print("="*60)

        # Get existing _MEI directories
        self.get_existing_mei()

        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_temp, daemon=True)
        monitor_thread.start()

        # Run the executable
        process = self.run_exe()

        if process:
            # Wait for extraction (max 30 seconds)
            print("\n[*] Waiting for PyInstaller to extract files...")

            for i in range(60):  # 30 seconds
                if self.found_mei:
                    break
                time.sleep(0.5)
                sys.stdout.write('.')
                sys.stdout.flush()

            print()

            # Stop monitoring
            self.stop_monitoring = True

            # Kill the process
            try:
                process.terminate()
                print(f"[*] Process terminated")
            except:
                pass

        if self.found_mei:
            # List extracted files
            self.list_extracted_files()

            # Decompile
            self.decompile_pyc_files()

            print(f"\n{'='*60}")
            print(f"[+] EXTRACTION COMPLETE!")
            print(f"[*] Extracted files: {self.extracted_path}")
            print(f"[*] Decompiled source: {self.decompiled_path}")
            print(f"{'='*60}")
        else:
            print("\n[!] No files were extracted")
            print("[*] The exe may require:")
            print("    - License key")
            print("    - Administrator privileges")
            print("    - Network connection")

if __name__ == "__main__":
    extractor = PyInstallerExtractor()
    extractor.run()
