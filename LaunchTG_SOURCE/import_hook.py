
import sys
import marshal
import types
from pathlib import Path

output_dir = Path(r'C:\Users\Nicita\Desktop\LaunchTG_SOURCE') / 'hooked_modules'
output_dir.mkdir(parents=True, exist_ok=True)

original_import = __builtins__.__import__

def hook_import(name, *args, **kwargs):
    module = original_import(name, *args, **kwargs)

    try:
        if hasattr(module, '__file__') and module.__file__:
            print(f"[HOOK] Loaded: {name} from {module.__file__}")

            # Try to get source
            if hasattr(module, '__cached__'):
                print(f"  Cached: {module.__cached__}")

    except:
        pass

    return module

__builtins__.__import__ = hook_import

print("[*] Import hook installed!")
