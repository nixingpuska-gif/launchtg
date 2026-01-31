#!/usr/bin/env python3
"""
Master script - runs all extraction methods in parallel
"""

import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPTS = [
    ("frida_hook.py", "Frida Dynamic Analysis", 90),
    ("aes_bruteforce.py", "AES Key Brute-Force", 300),
    ("memory_dumper.py", "Memory Dump", 60),
]

def run_script(script_name, description, timeout):
    """Run a single script"""

    print(f"\n[*] Starting: {description}")
    print(f"    Script: {script_name}")

    script_path = Path(r"C:\Users\Nicita\Desktop") / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        print(f"\n{'='*60}")
        print(f"[{description}] OUTPUT:")
        print('='*60)
        print(result.stdout)

        if result.stderr:
            print(f"\n[{description}] ERRORS:")
            print(result.stderr)

        return (description, result.returncode == 0, result.stdout)

    except subprocess.TimeoutExpired:
        print(f"\n[!] {description} timed out")
        return (description, False, "Timeout")

    except Exception as e:
        print(f"\n[!] {description} failed: {e}")
        return (description, False, str(e))

def collect_results():
    """Collect all extracted files"""

    print("\n" + "="*60)
    print(" Collecting Results")
    print("="*60)

    source_dir = Path(r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE")

    categories = {
        'Frida Dumps': source_dir / 'frida_dump',
        'Decrypted Files': source_dir / 'decrypted',
        'Memory Dumps': source_dir / 'memory_dump',
        'Memory .pyc': source_dir / 'memory_dump' / 'extracted_pyc',
    }

    total_files = 0

    for cat, path in categories.items():
        if path.exists():
            files = list(path.glob('*'))
            total_files += len(files)

            print(f"\n[+] {cat}: {len(files)} files")

            for f in files[:10]:
                size = f.stat().st_size
                print(f"    - {f.name} ({size:,} bytes)")

            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more")

    return total_files

def decompile_all_pyc():
    """Decompile all found .pyc files"""

    print("\n" + "="*60)
    print(" Decompiling .pyc Files")
    print("="*60)

    source_dir = Path(r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE")
    decompiled_dir = source_dir / "DECOMPILED"
    decompiled_dir.mkdir(exist_ok=True)

    # Find all .pyc files
    pyc_files = []

    for root in [source_dir / 'frida_dump', source_dir / 'memory_dump']:
        if root.exists():
            pyc_files.extend(root.rglob('*.pyc'))

    print(f"[*] Found {len(pyc_files)} .pyc files")

    success = 0
    failed = 0

    for pyc_file in pyc_files:
        try:
            # Try uncompyle6
            result = subprocess.run(
                [sys.executable, '-m', 'uncompyle6', str(pyc_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                # Save decompiled
                rel_path = pyc_file.relative_to(pyc_file.parents[1])
                out_file = decompiled_dir / rel_path.with_suffix('.py')
                out_file.parent.mkdir(parents=True, exist_ok=True)

                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)

                success += 1
                print(f"  [OK] {rel_path}")

            else:
                failed += 1

        except Exception as e:
            failed += 1

    print(f"\n[*] Decompilation results:")
    print(f"    - Success: {success}")
    print(f"    - Failed: {failed}")

    return success

def main():
    print("="*70)
    print(" ULTIMATE DECOMPILATION - LaunchTG v4.2.1")
    print(" Running 3 extraction methods in parallel")
    print("="*70)

    start_time = time.time()

    # Run all scripts in parallel
    print("\n[*] Starting parallel extraction...")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_script, script, desc, timeout): desc
            for script, desc, timeout in SCRIPTS
        }

        results = []

        for future in as_completed(futures):
            desc, success, output = future.result()
            results.append((desc, success))

            print(f"\n[{'✓' if success else '✗'}] {desc} completed")

    # Collect results
    total_files = collect_results()

    # Decompile
    decompiled = decompile_all_pyc()

    # Final summary
    elapsed = time.time() - start_time

    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70)

    print(f"\nTime elapsed: {elapsed:.1f} seconds")

    print(f"\nExtraction Methods:")
    for desc, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  [{status}] {desc}")

    print(f"\nResults:")
    print(f"  - Total files extracted: {total_files}")
    print(f"  - Successfully decompiled: {decompiled}")

    # Calculate recovery percentage
    if total_files > 0 or decompiled > 0:
        # Estimate based on typical PyInstaller app structure
        # Average has ~50-100 modules
        estimated_total = 80
        recovery_pct = min(100, (decompiled / estimated_total) * 100)

        print(f"\n  📊 ESTIMATED RECOVERY: {recovery_pct:.1f}%")

        if recovery_pct >= 95:
            print("  🎉 EXCELLENT - Almost complete recovery!")
        elif recovery_pct >= 80:
            print("  ✅ GOOD - Major functionality recovered")
        elif recovery_pct >= 50:
            print("  ⚠️  PARTIAL - Core modules recovered")
        else:
            print("  ❌ LIMITED - Additional methods needed")

    print(f"\nOutput directories:")
    print(f"  - Source files: C:\\Users\\Nicita\\Desktop\\LaunchTG_SOURCE\\DECOMPILED\\")
    print(f"  - Raw dumps: C:\\Users\\Nicita\\Desktop\\LaunchTG_SOURCE\\")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
