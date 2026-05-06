# LocalShare — Release Guide

This document covers how to build, package, and publish a release of LocalShare for each supported platform.

---

## Prerequisites

```bash
pip install pyinstaller
```

Python 3.10+ is required.  
On Linux you also need `python3-tk` installed (see README).

---

## Building

### Windows — Single EXE

```powershell
python build.py
```

Output: `dist\LocalShare.exe`

> PyInstaller embeds the Python runtime. No Python installation needed on the target machine.

### Windows — Folder Bundle (faster startup)

```powershell
python build.py --onedir
```

Output: `dist\LocalShare\LocalShare.exe`

### macOS — App Bundle

```bash
python build.py
```

Output: `dist/LocalShare`  
To create a proper `.app`, wrap it with `py2app` or package the PyInstaller output:

```bash
# Optional: codesign for Gatekeeper
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: YOUR NAME (TEAM_ID)" \
  dist/LocalShare
```

### Linux — AppImage / Binary

```bash
python build.py
```

Output: `dist/LocalShare`  
To create an AppImage, use [`appimagetool`](https://appimage.github.io/):

```bash
# Create AppDir structure
mkdir -p AppDir/usr/bin
cp dist/LocalShare AppDir/usr/bin/localshare
# ... add .desktop and icon, then:
appimagetool AppDir LocalShare-x86_64.AppImage
```

---

## Optional: Custom Icon

Place the appropriate icon file next to `build.py` **before** running the build:

| Platform | File       |
|----------|------------|
| Windows  | `icon.ico` |
| macOS    | `icon.icns`|
| Linux    | `icon.png` |

`build.py` auto-detects and applies the icon if present.

---

## Release Checklist

- [ ] Bump the version number (update `APP_NAME` in `build.py` if needed)
- [ ] Run on Windows and verify `dist\LocalShare.exe` launches correctly
- [ ] Run on macOS and verify the binary launches correctly
- [ ] Run on Linux and verify the binary launches correctly
- [ ] Test non-ASCII filenames (e.g. Turkish / Chinese characters) — should download without errors
- [ ] Test path traversal: `http://host:8080/../../../etc/passwd` should return 403
- [ ] Clean build artifacts: `python build.py --clean-only`

---

## Packaging for GitHub Releases

Recommended asset names:

| Asset                        | Platform       |
|------------------------------|----------------|
| `LocalShare-win-x64.exe`     | Windows 64-bit |
| `LocalShare-macos-arm64`     | macOS Apple Silicon |
| `LocalShare-macos-x64`       | macOS Intel    |
| `LocalShare-linux-x64`       | Linux 64-bit   |

Rename after build:

```powershell
# Windows
Rename-Item dist\LocalShare.exe LocalShare-win-x64.exe
```

```bash
# macOS / Linux
mv dist/LocalShare LocalShare-linux-x64   # or macos-arm64, etc.
```

Then upload the renamed files to the GitHub Release.

---

## Clean Build Artifacts

```bash
python build.py --clean-only
```

This removes `dist/`, `build/`, and `localshare.spec`.
