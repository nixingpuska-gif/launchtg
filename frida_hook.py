"""
Frida hook script for PyInstaller executables
Intercepts Python runtime, imports, and bytecode loading
"""

import frida
import sys
import time
import os
from pathlib import Path

OUTPUT_DIR = r"C:\Users\Nicita\Desktop\LaunchTG_SOURCE\frida_dump"

# Frida script to inject
FRIDA_SCRIPT = """

// Hook PyImport_ImportModule
Interceptor.attach(Module.findExportByName(null, "PyImport_ImportModule"), {
    onEnter: function(args) {
        var moduleName = Memory.readUtf8String(args[0]);
        send({type: "import", module: moduleName});
    }
});

// Hook marshal_loads (PyMarshal_ReadObjectFromString)
var marshalRead = Module.findExportByName(null, "PyMarshal_ReadObjectFromString");
if (marshalRead) {
    Interceptor.attach(marshalRead, {
        onEnter: function(args) {
            this.data = args[0];
            this.len = args[1].toInt32();
        },
        onLeave: function(retval) {
            if (this.data && this.len > 0) {
                var data = Memory.readByteArray(this.data, Math.min(this.len, 1024*1024));
                send({type: "marshal", size: this.len}, data);
            }
        }
    });
}

// Hook CreateFileW to see what files are created/opened
var createFileW = Module.findExportByName("kernel32.dll", "CreateFileW");
if (createFileW) {
    Interceptor.attach(createFileW, {
        onEnter: function(args) {
            var filename = Memory.readUtf16String(args[0]);
            if (filename.includes("_MEI") || filename.includes(".pyc") || filename.includes(".pyd")) {
                send({type: "file", path: filename, action: "open"});
            }
        }
    });
}

// Hook WriteFile to capture written data
var writeFile = Module.findExportByName("kernel32.dll", "WriteFile");
if (writeFile) {
    Interceptor.attach(writeFile, {
        onEnter: function(args) {
            this.buffer = args[1];
            this.bytesToWrite = args[2].toInt32();
        },
        onLeave: function(retval) {
            if (this.bytesToWrite > 0 && this.bytesToWrite < 10*1024*1024) {
                var data = Memory.readByteArray(this.buffer, Math.min(this.bytesToWrite, 1024*1024));
                send({type: "write", size: this.bytesToWrite}, data);
            }
        }
    });
}

// Hook VirtualAlloc to find memory regions
var virtualAlloc = Module.findExportByName("kernel32.dll", "VirtualAlloc");
if (virtualAlloc) {
    Interceptor.attach(virtualAlloc, {
        onLeave: function(retval) {
            if (!retval.isNull()) {
                send({type: "alloc", address: retval.toString(), size: this.context.r8});
            }
        }
    });
}

// Scan memory for Python bytecode
function scanForPython() {
    Process.enumerateRanges('r--', {
        onMatch: function(range) {
            try {
                var data = Memory.readByteArray(range.base, Math.min(range.size, 1024*1024));
                // Look for .pyc magic bytes
                send({type: "memory_scan", address: range.base.toString(), size: range.size}, data);
            } catch(e) {}
        },
        onComplete: function() {
            send({type: "scan_complete"});
        }
    });
}

// Scan after 5 seconds
setTimeout(scanForPython, 5000);

send({type: "ready"});
"""

def on_message(message, data):
    """Handle messages from Frida"""

    if message['type'] == 'send':
        payload = message.get('payload', {})
        msg_type = payload.get('type', '')

        if msg_type == 'ready':
            print("[+] Frida hook activated!")

        elif msg_type == 'import':
            module = payload.get('module', '')
            print(f"[IMPORT] {module}")

        elif msg_type == 'marshal':
            size = payload.get('size', 0)
            if data:
                output_file = Path(OUTPUT_DIR) / f"marshal_{int(time.time()*1000)}.pyc"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'wb') as f:
                    f.write(data)
                print(f"[MARSHAL] Captured {size} bytes -> {output_file.name}")

        elif msg_type == 'file':
            path = payload.get('path', '')
            action = payload.get('action', '')
            print(f"[FILE] {action}: {path}")

        elif msg_type == 'write':
            size = payload.get('size', 0)
            if data and size > 1000:  # Only save significant writes
                output_file = Path(OUTPUT_DIR) / f"write_{int(time.time()*1000)}.bin"
                with open(output_file, 'wb') as f:
                    f.write(data)
                print(f"[WRITE] Captured {size} bytes -> {output_file.name}")

        elif msg_type == 'alloc':
            addr = payload.get('address', '')
            size = payload.get('size', 0)
            print(f"[ALLOC] {addr} ({size} bytes)")

        elif msg_type == 'memory_scan':
            if data:
                # Check for Python magic bytes
                if b'\x61\x0d\x0d\x0a' in data or b'\x6f\x0d\x0d\x0a' in data or b'\xa7\x0d\x0d\x0a' in data:
                    output_file = Path(OUTPUT_DIR) / f"memscan_{int(time.time()*1000)}.bin"
                    with open(output_file, 'wb') as f:
                        f.write(data)
                    print(f"[MEMSCAN] Found Python bytecode -> {output_file.name}")

        elif msg_type == 'scan_complete':
            print("[*] Memory scan complete")

    elif message['type'] == 'error':
        print(f"[ERROR] {message.get('stack', message.get('description', 'Unknown'))}")

def main():
    print("="*60)
    print(" Frida Dynamic Analysis - LaunchTG")
    print("="*60)

    EXE_PATH = r"C:\Users\Nicita\Desktop\LaunchTGV4.2.1\LaunchTG.exe"

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print(f"[*] Target: {EXE_PATH}")
    print(f"[*] Output: {OUTPUT_DIR}")
    print(f"\n[*] Spawning process...")

    try:
        # Spawn the process
        pid = frida.spawn([EXE_PATH], cwd=os.path.dirname(EXE_PATH))
        session = frida.attach(pid)

        print(f"[+] Attached to PID: {pid}")

        # Load script
        script = session.create_script(FRIDA_SCRIPT)
        script.on('message', on_message)
        script.load()

        print("[*] Script loaded, resuming process...")

        # Resume the process
        frida.resume(pid)

        # Keep running for 60 seconds
        print("[*] Monitoring for 60 seconds...")
        print("[*] Press Ctrl+C to stop earlier\n")

        try:
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n[*] Stopping...")

        # Detach
        session.detach()

        # Kill process
        import subprocess
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)

        print(f"\n[+] Analysis complete!")
        print(f"[*] Check {OUTPUT_DIR} for captured data")

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
