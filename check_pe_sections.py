#!/usr/bin/env python3
"""Check PE sections and detect compression/packing"""

import struct

def read_pe_sections(filepath):
    """Read and display PE file sections"""

    with open(filepath, 'rb') as f:
        # Read DOS header
        dos_header = f.read(64)
        if dos_header[:2] != b'MZ':
            print("[!] Not a valid PE file (missing MZ signature)")
            return

        # Get PE header offset
        pe_offset = struct.unpack('<I', dos_header[60:64])[0]
        f.seek(pe_offset)

        # Read PE signature
        pe_sig = f.read(4)
        if pe_sig != b'PE\x00\x00':
            print("[!] Not a valid PE file (missing PE signature)")
            return

        print("[+] Valid PE file detected\n")

        # Read COFF header
        coff_header = f.read(20)
        machine = struct.unpack('<H', coff_header[0:2])[0]
        num_sections = struct.unpack('<H', coff_header[2:4])[0]
        optional_header_size = struct.unpack('<H', coff_header[16:18])[0]

        print(f"[*] Machine type: 0x{machine:04X}")
        print(f"[*] Number of sections: {num_sections}")
        print(f"[*] Optional header size: {optional_header_size}\n")

        # Skip optional header
        f.read(optional_header_size)

        # Read section headers
        print("[+] PE Sections:")
        print("="*80)
        print(f"{'Name':<12} {'VirtSize':<12} {'VirtAddr':<12} {'RawSize':<12} {'Entropy':<10}")
        print("="*80)

        sections = []
        for i in range(num_sections):
            section_header = f.read(40)

            name = section_header[0:8].rstrip(b'\x00').decode('utf-8', errors='ignore')
            virt_size = struct.unpack('<I', section_header[8:12])[0]
            virt_addr = struct.unpack('<I', section_header[12:16])[0]
            raw_size = struct.unpack('<I', section_header[16:20])[0]
            raw_ptr = struct.unpack('<I', section_header[20:24])[0]

            # Calculate entropy for packed detection
            current_pos = f.tell()
            f.seek(raw_ptr)
            section_data = f.read(min(raw_size, 8192))  # Read first 8KB
            f.seek(current_pos)

            import math
            from collections import Counter

            if section_data:
                byte_counts = Counter(section_data)
                entropy = 0
                for count in byte_counts.values():
                    p = count / len(section_data)
                    entropy -= p * math.log2(p)
            else:
                entropy = 0

            sections.append({
                'name': name,
                'virt_size': virt_size,
                'virt_addr': virt_addr,
                'raw_size': raw_size,
                'raw_ptr': raw_ptr,
                'entropy': entropy
            })

            print(f"{name:<12} {virt_size:<12} 0x{virt_addr:<10X} {raw_size:<12} {entropy:<10.2f}")

        print("="*80)

        # Check for packing indicators
        print("\n[+] Packing indicators:")

        # High entropy indicates compression/encryption
        high_entropy_sections = [s for s in sections if s['entropy'] > 7.0]
        if high_entropy_sections:
            print(f"    ⚠ Found {len(high_entropy_sections)} high-entropy sections (likely packed/encrypted)")
            for s in high_entropy_sections:
                print(f"        - {s['name']}: entropy {s['entropy']:.2f}")

        # Check for UPX
        upx_sections = [s for s in sections if 'UPX' in s['name']]
        if upx_sections:
            print("    ⚠ UPX sections detected - file is UPX packed")
            print("    → Recommendation: Use 'upx -d LaunchTG.exe' to decompress")

        # Check for suspicious section names
        suspicious = [s for s in sections if s['name'] in ['.packed', '.stub', '.enigma', '.themida']]
        if suspicious:
            print(f"    ⚠ Suspicious section names detected:")
            for s in suspicious:
                print(f"        - {s['name']}")

        # Very large .data or .rdata sections might contain embedded resources
        large_data = [s for s in sections if s['name'] in ['.data', '.rdata'] and s['raw_size'] > 10*1024*1024]
        if large_data:
            print(f"    ℹ Large data sections found (may contain embedded Python/resources):")
            for s in large_data:
                print(f"        - {s['name']}: {s['raw_size']:,} bytes")

        print()

if __name__ == "__main__":
    exe_path = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"
    read_pe_sections(exe_path)
