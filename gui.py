"""Tkinter GUI for LocalShare."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from server import create_server
from utils import get_local_ip


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LocalShare")
        self.root.geometry("500x390")
        self.root.resizable(False, False)
        self.root.configure(bg="#111")

        self._server = None
        self._current_url: str | None = None

        self.folder_var = tk.StringVar(value="No folder selected yet")
        self.port_var = tk.IntVar(value=8080)
        self.status_var = tk.StringVar(value="● Stopped")

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#1a1a2e", pady=16)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="📂  LocalShare",
            font=("Segoe UI", 17, "bold"),
            bg="#1a1a2e", fg="#4fc3f7",
        ).pack()
        tk.Label(
            hdr, text="Local network file sharing",
            font=("Segoe UI", 9),
            bg="#1a1a2e", fg="#666",
        ).pack(pady=(2, 0))

        body = tk.Frame(self.root, bg="#111", padx=28, pady=18)
        body.pack(fill="both", expand=True)

        # Folder row
        tk.Label(
            body, text="Shared Folder",
            font=("Segoe UI", 9, "bold"),
            bg="#111", fg="#777",
        ).pack(anchor="w")

        fr = tk.Frame(body, bg="#111")
        fr.pack(fill="x", pady=(4, 14))

        self._lbl_folder = tk.Label(
            fr, textvariable=self.folder_var,
            font=("Segoe UI", 9), bg="#1a1a2e", fg="#aaa",
            anchor="w", padx=10, pady=7, relief="flat", wraplength=330,
        )
        self._lbl_folder.pack(side="left", fill="x", expand=True)

        tk.Button(
            fr, text=" Browse ",
            command=self._pick_folder,
            bg="#4fc3f7", fg="#0d0d0d",
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=8, pady=7,
            cursor="hand2", activebackground="#81d4fa", bd=0,
        ).pack(side="right", padx=(8, 0))

        # Port row
        tk.Label(
            body, text="Port",
            font=("Segoe UI", 9, "bold"),
            bg="#111", fg="#777",
        ).pack(anchor="w")

        pf = tk.Frame(body, bg="#111")
        pf.pack(anchor="w", pady=(4, 16))
        tk.Entry(
            pf, textvariable=self.port_var, width=7,
            bg="#1a1a2e", fg="#ddd",
            font=("Consolas", 11), relief="flat",
            insertbackground="white",
        ).pack(ipady=6, ipadx=6)

        # Start / Stop button
        self._btn = tk.Button(
            body, text="▶   Start",
            command=self._toggle,
            bg="#4caf50", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", pady=10,
            cursor="hand2", activebackground="#66bb6a", bd=0,
        )
        self._btn.pack(fill="x", pady=(0, 14))

        # URL display
        url_box = tk.Frame(body, bg="#1a1a2e", padx=14, pady=12)
        url_box.pack(fill="x")

        self._lbl_url = tk.Label(
            url_box,
            text="—  server not running  —",
            font=("Consolas", 10),
            bg="#1a1a2e", fg="#444",
            cursor="hand2",
        )
        self._lbl_url.pack()

        self._lbl_hint = tk.Label(
            url_box, text="",
            font=("Segoe UI", 8),
            bg="#1a1a2e", fg="#555",
        )
        self._lbl_hint.pack()
        self._lbl_url.bind("<Button-1>", self._copy_url)

        # Status bar
        sb = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=5)
        sb.pack(fill="x", side="bottom")
        tk.Label(
            sb, textvariable=self.status_var,
            font=("Segoe UI", 8),
            bg="#1a1a2e", fg="#666",
        ).pack(side="left")

    # ── Actions ────────────────────────────────────────────────────────────

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Select a folder to share")
        if path:
            self.folder_var.set(path)
            self._lbl_folder.config(fg="#ddd")

    def _toggle(self):
        if self._server:
            self._stop()
        else:
            self._start()

    def _start(self):
        import os
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder first.")
            return

        port = self.port_var.get()

        try:
            self._server = create_server(folder, port)
        except OSError as exc:
            messagebox.showerror(
                "Port Error", f"Port {port} is unavailable:\n{exc}"
            )
            return

        threading.Thread(
            target=self._server.serve_forever, daemon=True
        ).start()

        ip = get_local_ip()
        url = f"http://{ip}:{port}/"
        self._current_url = url

        self._lbl_url.config(text=url, fg="#4fc3f7")
        self._lbl_hint.config(
            text="Click URL to copy to clipboard", fg="#555"
        )
        self._btn.config(
            text="⏹   Stop", bg="#e53935", activebackground="#ef5350"
        )
        self.status_var.set(f"● Running  |  {folder}")

    def _stop(self):
        if self._server:
            threading.Thread(
                target=self._server.shutdown, daemon=True
            ).start()
            self._server = None

        self._current_url = None
        self._lbl_url.config(text="—  server not running  —", fg="#444")
        self._lbl_hint.config(text="")
        self._btn.config(
            text="▶   Start", bg="#4caf50", activebackground="#66bb6a"
        )
        self.status_var.set("● Stopped")

    def _copy_url(self, _event=None):
        if self._current_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._current_url)
            self._lbl_hint.config(text="✓ Copied to clipboard", fg="#4caf50")
            self.root.after(
                2200,
                lambda: self._lbl_hint.config(
                    text="Click URL to copy to clipboard", fg="#555"
                ),
            )

    def on_close(self):
        self._stop()
        self.root.destroy()
