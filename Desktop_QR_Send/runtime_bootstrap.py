"""Select the matching Qt DLL layout from the device computer at runtime."""

from __future__ import print_function

import argparse
import ctypes
import datetime
import importlib.util
import os
from pathlib import Path
import runpy
import sys
import traceback


APP_DIR = Path(__file__).resolve().parent
VALID_QT_MODES = ("auto", "pyside", "conda", "system")
_DLL_DIRECTORY_HANDLES = []
_PRELOADED_QT_DLLS = []
_PRELOADED_SUPPORT_DLLS = []
_RUNTIME_INFO = None


def _startup_log(message):
    try:
        log_dir = APP_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with (log_dir / "startup.log").open("a", encoding="utf-8") as stream:
            stream.write("[{0}] {1}\n".format(timestamp, message))
    except OSError:
        pass


def _package_dir(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None
    locations = spec.submodule_search_locations
    if locations:
        return Path(next(iter(locations))).resolve()
    if spec.origin:
        return Path(spec.origin).resolve().parent
    return None


def _unique_existing_dirs(directories):
    result = []
    seen = set()
    for directory in directories:
        directory = Path(directory)
        if not directory.is_dir():
            continue
        resolved = directory.resolve()
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def _prepend_path(directories):
    current = [item for item in os.environ.get("PATH", "").split(os.pathsep) if item]
    combined = [str(path) for path in directories] + current
    unique = []
    seen = set()
    for item in combined:
        key = os.path.normcase(os.path.abspath(item))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    os.environ["PATH"] = os.pathsep.join(unique)


def _register_dll_directory(directory):
    if not hasattr(os, "add_dll_directory"):
        return
    try:
        # The handle must live until the GUI exits, otherwise Windows removes
        # the directory from its DLL search list.
        _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(directory)))
    except OSError as exc:
        _startup_log("Cannot register DLL directory {0}: {1}".format(directory, exc))


def _dll_exports(dll_path, symbol_name):
    """Inspect a PE export without resolving or running DLL dependencies."""
    if os.name != "nt":
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    load_library = kernel32.LoadLibraryExW
    load_library.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_uint32]
    load_library.restype = ctypes.c_void_p
    get_proc_address = kernel32.GetProcAddress
    get_proc_address.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    get_proc_address.restype = ctypes.c_void_p
    free_library = kernel32.FreeLibrary
    free_library.argtypes = [ctypes.c_void_p]
    free_library.restype = ctypes.c_int

    handle = load_library(str(dll_path), None, 0x00000001)
    if not handle:
        return False
    try:
        return bool(get_proc_address(handle, symbol_name.encode("ascii")))
    finally:
        free_library(handle)


def _find_compatible_icuuc(qt_dll_dir):
    """Select the ICU build expected by Qt6Core, not PATH's first ICU DLL."""
    directories = [
        qt_dll_dir,
        Path(sys.prefix) / "Library" / "bin",
        Path(sys.prefix),
        Path(sys.prefix) / "DLLs",
    ]
    directories.extend(
        Path(item) for item in os.environ.get("PATH", "").split(os.pathsep) if item
    )
    candidates = []
    for directory in _unique_existing_dirs(directories):
        candidate = directory / "icuuc.dll"
        if candidate.is_file():
            candidates.append(candidate.resolve())

    if not candidates:
        return None, []

    required_export = "UCNV_TO_U_CALLBACK_SUBSTITUTE"
    for candidate in candidates:
        if _dll_exports(candidate, required_export):
            return candidate, candidates
        _startup_log(
            "Rejected incompatible ICU DLL (missing {0}): {1}".format(
                required_export, candidate
            )
        )
    return None, candidates


def _qt_candidates(pyside_dir, mode):
    pyside_candidates = [
        pyside_dir,
        pyside_dir / "Qt" / "bin",
        pyside_dir / "Qt" / "lib",
    ]
    conda_candidates = [
        Path(sys.prefix) / "Library" / "bin",
        Path(sys.prefix) / "DLLs",
    ]
    if mode == "pyside":
        return pyside_candidates
    if mode == "conda":
        return conda_candidates
    if mode == "system":
        return []
    return pyside_candidates + conda_candidates


def _find_qt_dll_dir(pyside_dir, mode):
    for directory in _qt_candidates(pyside_dir, mode):
        if (directory / "Qt6Core.dll").is_file() and (directory / "Qt6Widgets.dll").is_file():
            return directory.resolve()
    return None


def _camera_runtime_dirs():
    candidates = []
    for variable in ("MVCAM_COMMON_RUNENV", "MVCAM_COMMON_RUNENV_V2", "MVCAM_SDK_PATH"):
        value = os.environ.get(variable)
        if value:
            candidates.append(Path(value))
    candidates.extend(
        [
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "Common Files" / "MVS" / "Runtime" / "Win64_x64",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "Common Files" / "MVS" / "Runtime" / "Win64_x64",
        ]
    )
    return _unique_existing_dirs(candidates)


def _preload_qt(qt_dll_dir):
    if os.name != "nt" or qt_dll_dir is None:
        return

    icuuc_dll, inspected_icu_dlls = _find_compatible_icuuc(qt_dll_dir)
    if inspected_icu_dlls and icuuc_dll is None:
        raise RuntimeError(
            "Qt6Core found only incompatible icuuc.dll files: {0}".format(
                ", ".join(str(path) for path in inspected_icu_dlls)
            )
        )
    if icuuc_dll is not None:
        _register_dll_directory(icuuc_dll.parent)
        _PRELOADED_SUPPORT_DLLS.append(ctypes.WinDLL(str(icuuc_dll)))
        _startup_log("Preloaded compatible ICU DLL: {0}".format(icuuc_dll))

    for filename in ("Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll"):
        dll_path = qt_dll_dir / filename
        if dll_path.is_file():
            _PRELOADED_QT_DLLS.append(ctypes.WinDLL(str(dll_path)))


def configure_runtime(mode=None):
    """Configure only paths discovered from the Python running on the device."""
    global _RUNTIME_INFO
    if _RUNTIME_INFO is not None:
        return _RUNTIME_INFO

    mode = (mode or os.environ.get("LASER_QT_MODE") or "auto").lower()
    if mode not in VALID_QT_MODES:
        raise RuntimeError("Unsupported Qt loading mode: {0}".format(mode))
    os.environ["LASER_QT_MODE"] = mode

    os.chdir(str(APP_DIR))
    app_dir_text = str(APP_DIR)
    if app_dir_text not in sys.path:
        sys.path.insert(0, app_dir_text)

    pyside_dir = _package_dir("PySide6")
    if pyside_dir is None:
        raise RuntimeError("The selected device Python does not contain PySide6")
    shiboken_dir = _package_dir("shiboken6")
    qt_dll_dir = _find_qt_dll_dir(pyside_dir, mode)

    if os.name == "nt" and mode != "system" and qt_dll_dir is None:
        raise RuntimeError("No matching Qt6 DLL directory was found for mode: {0}".format(mode))

    # Load and lock the selected Qt/ICU set before exposing Anaconda or MVS
    # directories that may contain unrelated DLLs with the same filenames.
    qt_dirs = []
    if qt_dll_dir is not None:
        qt_dirs.append(qt_dll_dir)
    qt_dirs.append(pyside_dir)
    if shiboken_dir is not None:
        qt_dirs.append(shiboken_dir)
    qt_dirs = _unique_existing_dirs(qt_dirs)

    _prepend_path(qt_dirs)
    for directory in qt_dirs:
        _register_dll_directory(directory)
    if mode != "system":
        _preload_qt(qt_dll_dir)

    runtime_dirs = _unique_existing_dirs(
        [Path(sys.prefix), Path(sys.prefix) / "DLLs"] + _camera_runtime_dirs()
    )
    selected_dirs = _unique_existing_dirs(qt_dirs + runtime_dirs)
    _prepend_path(selected_dirs)
    for directory in runtime_dirs:
        _register_dll_directory(directory)

    _RUNTIME_INFO = {
        "mode": mode,
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "pyside_dir": str(pyside_dir),
        "qt_dll_dir": str(qt_dll_dir) if qt_dll_dir is not None else "system",
        "dll_dirs": [str(directory) for directory in selected_dirs],
    }
    return _RUNTIME_INFO


def check_runtime(quiet=False, mode=None):
    info = configure_runtime(mode=mode)
    import PySide6
    from PySide6.QtCore import qVersion
    from PySide6.QtWidgets import QApplication  # noqa: F401

    message = (
        "Runtime OK | mode {mode} | Python {python_version} ({python}) | "
        "PySide6 {pyside_version} | Qt {qt_version} | Qt DLL: {qt_dll_dir}"
    ).format(pyside_version=PySide6.__version__, qt_version=qVersion(), **info)
    _startup_log(message)
    if not quiet:
        print("[OK] " + message)
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(description="Device runtime bootstrap")
    parser.add_argument("--check", action="store_true", help="check Qt without opening the GUI")
    parser.add_argument("--quiet", action="store_true", help="suppress successful check output")
    parser.add_argument("--qt-mode", choices=VALID_QT_MODES, default="auto")
    args = parser.parse_args(argv)

    if __name__ == "__main__":
        sys.modules.setdefault("runtime_bootstrap", sys.modules["__main__"])

    try:
        check_runtime(quiet=args.quiet, mode=args.qt_mode)
        if args.check:
            return 0
        runpy.run_path(str(APP_DIR / "main.py"), run_name="__main__")
        return 0
    except Exception as exc:
        details = "Runtime failed | mode {0} | Python {1} ({2}) | {3}: {4}\n{5}".format(
            args.qt_mode,
            sys.version.split()[0],
            sys.executable,
            type(exc).__name__,
            exc,
            traceback.format_exc(),
        )
        _startup_log(details)
        if not args.quiet:
            print("[ERROR] " + details, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
