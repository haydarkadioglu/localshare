"""LocalShare — entry point."""

import sys


def _check_dependencies() -> None:
    """
    Pre-flight checks before importing any GUI code.
    Prints a clear, actionable error and exits if something is missing,
    instead of letting Python segfault at the C/Tcl layer.
    """
    # ── tkinter / Tcl-Tk ────────────────────────────────────────────────
    try:
        import tkinter as _tk  # noqa: F401
    except ModuleNotFoundError:
        _die(
            "tkinter is not installed.",
            {
                "Debian / Ubuntu / Kali": "sudo apt install python3-tk",
                "Fedora / RHEL":          "sudo dnf install python3-tkinter",
                "Arch":                   "sudo pacman -S tk",
                "macOS (Homebrew)":       "brew install python-tk",
                "Windows":                "Reinstall Python and tick 'tcl/tk and IDLE'",
            },
        )

    # ── Test that Tcl/Tk shared libraries actually load (catches segfault) ──
    try:
        import tkinter as _tk
        _root = _tk.Tk()
        _root.withdraw()
        _root.destroy()
    except Exception as exc:
        _die(
            f"tkinter failed to initialize: {exc}\n"
            "This usually means the Tcl/Tk C libraries are missing or mismatched.",
            {
                "Debian / Ubuntu / Kali": (
                    "sudo apt install --reinstall python3-tk tcl tk\n"
                    "  # If you used a custom Python build:\n"
                    "  sudo apt install tcl-dev tk-dev && pip install --force-reinstall tkinter"
                ),
                "macOS":   "brew reinstall python-tk",
                "Windows": "Reinstall Python from python.org",
            },
        )


def _die(message: str, fixes: dict) -> None:
    border = "─" * 60
    print(f"\n{border}", file=sys.stderr)
    print(f"  ERROR: {message}", file=sys.stderr)
    print(f"\n  Fix:", file=sys.stderr)
    for platform, cmd in fixes.items():
        print(f"\n    [{platform}]", file=sys.stderr)
        for line in cmd.splitlines():
            print(f"      {line}", file=sys.stderr)
    print(f"{border}\n", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    _check_dependencies()

    import tkinter as tk
    from gui import App

    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
