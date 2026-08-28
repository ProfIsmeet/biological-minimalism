"""Windows DLL-loading workaround for `import torch`.

On this project's Windows development machine, `import torch` (PyTorch 2.6.0,
Python 3.13, CPU build) fails with:

    OSError: [WinError 1114] A dynamic link library (DLL) initialization
    routine failed. Error loading "...\\torch\\lib\\c10.dll" or one of its
    dependencies.

Diagnosis: the required MSVC runtime DLLs (vcruntime140.dll, vcruntime140_1.dll,
msvcp140.dll) are present system-wide, and every individual DLL under
`torch/lib/` loads fine via `ctypes.WinDLL` in isolation — so this is not a
missing-redistributable problem. The actual cause is that torch's own
`_load_dll_libraries()` (in `torch/__init__.py`) fails to correctly register
`torch/lib` as a DLL search directory *before* the OS resolves `c10.dll`'s own
dependencies on subsequent torch DLLs in this environment. Calling
`os.add_dll_directory()` on that same path ourselves, before `import torch`
runs, reliably fixes it (verified directly: every file under `torch/lib/`
loads via `ctypes.WinDLL` once the directory is registered, and `import torch`
then succeeds and produces working tensors).

This module must be imported (and `ensure_torch_dll_path()` called) BEFORE the
first `import torch` anywhere in the process. It is a no-op on non-Windows
platforms and if torch is not installed, so it is always safe to call.
"""

from __future__ import annotations

import importlib.util
import os
import sys

_done = False


def ensure_torch_dll_path() -> None:
    global _done
    if _done or sys.platform != "win32":
        return
    _done = True
    try:
        spec = importlib.util.find_spec("torch")
    except (ImportError, ValueError):
        return
    if spec is None or not spec.submodule_search_locations:
        return
    torch_dir = next(iter(spec.submodule_search_locations))
    lib_dir = os.path.join(torch_dir, "lib")
    if os.path.isdir(lib_dir):
        os.add_dll_directory(lib_dir)
