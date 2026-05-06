"""
Build script for LocalShare.

Produces a single-file executable using PyInstaller.

Usage
-----
    python build.py                  # auto-detect platform
    python build.py --onefile        # single exe  (default)
    python build.py --onedir         # folder dist (faster startup)
    python build.py --debug          # keep console window (for debugging)

Requirements
------------
    pip install pyinstaller
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ENTRY = ROOT / "main.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "localshare.spec"

APP_NAME = "LocalShare"


def clean():
    for path in (DIST, BUILD, SPEC):
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    print("[build] Cleaned previous artifacts.")


def build(onefile: bool, debug: bool):
    system = platform.system()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
        "--clean",
    ]

    # Window mode: hide console on Windows/macOS unless debugging
    if not debug and system in ("Windows", "Darwin"):
        cmd += ["--windowed"]

    if onefile:
        cmd += ["--onefile"]
    else:
        cmd += ["--onedir"]

    # Platform-specific icon (place icon files next to build.py if desired)
    icon_map = {
        "Windows": ROOT / "icon.ico",
        "Darwin": ROOT / "icon.icns",
        "Linux": ROOT / "icon.png",
    }
    icon_path = icon_map.get(system)
    if icon_path and icon_path.exists():
        cmd += ["--icon", str(icon_path)]

    cmd.append(str(ENTRY))

    print(f"[build] Platform  : {system}")
    print(f"[build] Mode      : {'onefile' if onefile else 'onedir'}")
    print(f"[build] Debug     : {debug}")
    print(f"[build] Command   : {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print("\n[build] PyInstaller failed.")
        sys.exit(result.returncode)

    print(f"\n[build] Done. Output → {DIST}/")


def main():
    parser = argparse.ArgumentParser(description="Build LocalShare executable")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--onefile", dest="onefile", action="store_true", default=True,
        help="Single-file executable (default)",
    )
    mode.add_argument(
        "--onedir", dest="onefile", action="store_false",
        help="Directory bundle (faster startup)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Keep console window open for debugging",
    )
    parser.add_argument(
        "--clean-only", action="store_true",
        help="Only remove previous build artifacts",
    )
    args = parser.parse_args()

    clean()
    if not args.clean_only:
        build(onefile=args.onefile, debug=args.debug)


if __name__ == "__main__":
    main()
