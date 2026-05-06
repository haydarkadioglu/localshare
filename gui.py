"""Tkinter GUI for LocalShare."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

from server import create_server
from tunnel import TunnelError, available_providers, start_tunnel
from utils import get_local_ip
from qr_popup import show_qr_popup


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LocalShare")
        self.root.geometry("500x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#111")

        self._server = None
        self._current_url: str | None = None
        self._tunnel_stop: Callable | None = None
        self._tunnel_url: str | None = None

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

        # ── Combined URL / tunnel card ─────────────────────────────────
        card = tk.Frame(body, bg="#1a1a2e", padx=14, pady=12)
        card.pack(fill="x", pady=(0, 10))

        # LAN row
        lan_row = tk.Frame(card, bg="#1a1a2e")
        lan_row.pack(fill="x")
        tk.Label(
            lan_row, text="LAN",
            font=("Segoe UI", 7, "bold"), bg="#1a1a2e", fg="#555",
            width=5, anchor="w",
        ).pack(side="left")
        self._lbl_url = tk.Label(
            lan_row, text="—  server not running  —",
            font=("Consolas", 10), bg="#1a1a2e", fg="#444",
            cursor="hand2", anchor="w",
        )
        self._lbl_url.pack(side="left", fill="x", expand=True)
        self._lbl_hint = tk.Label(
            card, text="",
            font=("Segoe UI", 7), bg="#1a1a2e", fg="#555",
        )
        self._lbl_hint.pack(anchor="w", padx=(44, 0))
        self._lbl_url.bind("<Button-1>", self._copy_url)

        # separator
        tk.Frame(card, bg="#222", height=1).pack(fill="x", pady=(8, 8))

        # Public link row
        pub_row = tk.Frame(card, bg="#1a1a2e")
        pub_row.pack(fill="x")
        tk.Label(
            pub_row, text="WEB",
            font=("Segoe UI", 7, "bold"), bg="#1a1a2e", fg="#555",
            width=5, anchor="w",
        ).pack(side="left")
        self._lbl_tun_url = tk.Label(
            pub_row, text="—  no public link  —",
            font=("Consolas", 10), bg="#1a1a2e", fg="#444",
            cursor="hand2", anchor="w",
        )
        self._lbl_tun_url.pack(side="left", fill="x", expand=True)

        # QR button (right side of the WEB row)
        self._btn_qr = tk.Button(
            pub_row, text="QR",
            command=self._show_qr,
            bg="#1a1a2e", fg="#555",
            font=("Segoe UI", 7, "bold"),
            relief="flat", padx=5, pady=2,
            cursor="hand2", activebackground="#263238", bd=0,
            state="disabled",
        )
        self._btn_qr.pack(side="right", padx=(4, 0))
        self._lbl_tun_hint = tk.Label(
            card, text="",
            font=("Segoe UI", 7), bg="#1a1a2e", fg="#555",
        )
        self._lbl_tun_hint.pack(anchor="w", padx=(44, 0))
        self._lbl_tun_url.bind("<Button-1>", self._copy_tunnel_url)

        # Tunnel button
        self._btn_tunnel = tk.Button(
            body, text="🌐  Get Public Link",
            command=self._toggle_tunnel,
            bg="#37474f", fg="#aaa",
            font=("Segoe UI", 9, "bold"),
            relief="flat", pady=7,
            cursor="hand2", activebackground="#455a64", bd=0,
            state="disabled",
        )
        self._btn_tunnel.pack(fill="x")

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
        self._btn_tunnel.config(state="normal", bg="#1565c0", fg="white",
                                 activebackground="#1976d2")
        self.status_var.set(f"● Running  |  {folder}")

    def _stop(self):
        self._stop_tunnel_internal()
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
        self._btn_tunnel.config(state="disabled", bg="#37474f", fg="#aaa",
                                 text="🌐  Get Public Link")
        self.status_var.set("● Stopped")

    # ── Tunnel actions ─────────────────────────────────────────────────────

    def _toggle_tunnel(self):
        if self._tunnel_stop:
            self._stop_tunnel_internal()
        else:
            self._start_tunnel()

    def _start_tunnel(self):
        providers = available_providers()
        if not providers:
            messagebox.showerror(
                "No Tunnel Provider",
                "No tunnel provider found.\n\n"
                "localhost.run requires SSH — install OpenSSH:\n"
                "  • Windows: Settings → Optional Features → OpenSSH Client\n\n"
                "Or install cloudflared (no account needed):\n"
                "  • winget install Cloudflare.cloudflared\n"
                "  • brew install cloudflared  (macOS)\n"
                "  • https://developers.cloudflare.com/cloudflare-one/"
                "connections/connect-networks/downloads/",
            )
            return

        self._btn_tunnel.config(text="⏳  Connecting…", state="disabled")
        self.root.update_idletasks()

        port = self.port_var.get()

        def _worker():
            try:
                url, stop_fn = start_tunnel(port)
                self._tunnel_stop = stop_fn
                self._tunnel_url = url
                self.root.after(0, lambda: self._on_tunnel_up(url))
            except TunnelError as exc:
                self.root.after(0, lambda: self._on_tunnel_error(str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_tunnel_up(self, url: str):
        self._lbl_tun_url.config(text=url, fg="#81c784")
        self._lbl_tun_hint.config(text="Click URL to copy  •  valid for this session", fg="#555")
        self._btn_tunnel.config(
            text="🔴  Stop Public Link", state="normal",
            bg="#b71c1c", fg="white", activebackground="#c62828",
        )
        self._btn_qr.config(state="normal", fg="#4fc3f7")
        # Auto-show QR popup
        self.root.after(200, lambda: show_qr_popup(self.root, url))

    def _on_tunnel_error(self, msg: str):
        self._btn_tunnel.config(
            text="🌐  Get Public Link", state="normal",
            bg="#1565c0", fg="white", activebackground="#1976d2",
        )
        messagebox.showerror("Tunnel Error", msg)

    def _stop_tunnel_internal(self):
        if self._tunnel_stop:
            threading.Thread(target=self._tunnel_stop, daemon=True).start()
            self._tunnel_stop = None
        self._tunnel_url = None
        self._lbl_tun_url.config(text="—  no public link  —", fg="#444")
        self._lbl_tun_hint.config(text="")
        self._btn_qr.config(state="disabled", fg="#555")
        if self._server:  # server still running, re-enable button
            self._btn_tunnel.config(
                text="🌐  Get Public Link", state="normal",
                bg="#1565c0", fg="white", activebackground="#1976d2",
            )

    def _show_qr(self):
        if self._tunnel_url:
            show_qr_popup(self.root, self._tunnel_url)

    def _copy_tunnel_url(self, _event=None):
        if self._tunnel_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._tunnel_url)
            self._lbl_tun_hint.config(text="✓ Copied to clipboard", fg="#4caf50")
            self.root.after(
                2200,
                lambda: self._lbl_tun_hint.config(
                    text="Click URL to copy  •  valid for this session", fg="#555"
                ),
            )

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
