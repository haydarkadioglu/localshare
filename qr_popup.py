"""
QR code popup for LocalShare.

Draws the QR code on a tkinter Canvas — no Pillow required.
Only dependency: pip install qrcode
"""

import tkinter as tk
from tkinter import messagebox


def _make_matrix(url: str) -> list[list[bool]]:
    """Return the QR code boolean matrix for *url*."""
    try:
        import qrcode  # type: ignore
    except ImportError:
        return []

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.modules  # list[list[bool]]


def show_qr_popup(parent: tk.Misc, url: str) -> None:
    """
    Open a modal popup showing a QR code for *url*.
    Falls back to a plain text dialog if qrcode is not installed.
    """
    matrix = _make_matrix(url)

    if not matrix:
        # qrcode not installed — guide the user
        answer = messagebox.askquestion(
            "QR Code",
            "The 'qrcode' package is required to show a QR code.\n\n"
            "Install it with:\n  pip install qrcode\n\n"
            "Would you like to copy the URL to the clipboard instead?",
            parent=parent,
        )
        if answer == "yes":
            parent.clipboard_clear()
            parent.clipboard_append(url)
        return

    CELL = 7        # pixels per QR module
    MARGIN = 20     # white border around the code (pixels)
    size = len(matrix)
    canvas_px = size * CELL + MARGIN * 2

    popup = tk.Toplevel(parent)
    popup.title("QR Code — Public Link")
    popup.resizable(False, False)
    popup.configure(bg="#fff")
    popup.grab_set()  # modal

    # ── QR Canvas ────────────────────────────────────────────────────────
    cv = tk.Canvas(popup, width=canvas_px, height=canvas_px,
                   bg="#fff", highlightthickness=0)
    cv.pack(padx=0, pady=0)

    for row_idx, row in enumerate(matrix):
        for col_idx, module in enumerate(row):
            if module:
                x0 = MARGIN + col_idx * CELL
                y0 = MARGIN + row_idx * CELL
                cv.create_rectangle(
                    x0, y0, x0 + CELL, y0 + CELL,
                    fill="#000", outline="",
                )

    # ── URL label ────────────────────────────────────────────────────────
    lbl = tk.Label(
        popup, text=url,
        font=("Consolas", 9), bg="#fff", fg="#333",
        cursor="hand2",
    )
    lbl.pack(pady=(0, 6))

    # ── Copy button ──────────────────────────────────────────────────────
    copied_var = tk.StringVar(value="Copy URL")

    def _copy():
        parent.clipboard_clear()
        parent.clipboard_append(url)
        copied_var.set("✓ Copied!")
        popup.after(2000, lambda: copied_var.set("Copy URL"))

    tk.Button(
        popup, textvariable=copied_var,
        command=_copy,
        bg="#1565c0", fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat", padx=14, pady=6,
        cursor="hand2", activebackground="#1976d2", bd=0,
    ).pack(pady=(0, 12))

    # Center relative to parent
    popup.update_idletasks()
    px = parent.winfo_rootx() + (parent.winfo_width() - popup.winfo_width()) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - popup.winfo_height()) // 2
    popup.geometry(f"+{px}+{py}")
