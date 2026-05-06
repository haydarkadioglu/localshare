"""
Tunnel helpers for LocalShare.

Supported providers (in priority order — all free, no account required):
  1. localhost.run  — SSH-based, zero install (SSH is built-in on Win10+/macOS/Linux)
  2. cloudflared   — Cloudflare Quick Tunnel
                     install: https://developers.cloudflare.com/cloudflare-one/connections/
                              connect-networks/downloads/

Usage
-----
    from tunnel import start_tunnel

    url, stop = start_tunnel(8080)   # e.g. https://abc123.lhr.life
    ...
    stop()
"""

import re
import shutil
import subprocess
import threading
import time
from typing import Callable


class TunnelError(Exception):
    pass


# ── localhost.run (SSH, no install, no account) ───────────────────────────────

_LHR_URL_RE = re.compile(r"https://[a-zA-Z0-9\-]+\.lhr\.life")


def _try_localhost_run(port: int) -> tuple[str, Callable]:
    """
    Tunnel via localhost.run using SSH.
    SSH is built-in on Windows 10+, macOS, and all Linux distros.
    No account or binary install required.
    """
    ssh = shutil.which("ssh")
    if not ssh:
        raise TunnelError("ssh binary not found — install OpenSSH and try again")

    cmd = [
        ssh,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        # Use 127.0.0.1 explicitly — "localhost" may resolve to ::1 (IPv6)
        # while the HTTP server only listens on 0.0.0.0 (IPv4).
        "-R", f"80:127.0.0.1:{port}",
        "nokey@localhost.run",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url: str | None = None
    deadline = time.monotonic() + 30

    for line in proc.stdout:  # type: ignore[union-attr]
        m = _LHR_URL_RE.search(line)
        if m:
            url = m.group(0)
            break
        if time.monotonic() > deadline:
            proc.terminate()
            raise TunnelError("localhost.run did not return a URL within 30 s")

    if not url:
        proc.terminate()
        raise TunnelError("localhost.run closed the connection without a URL")

    def _drain():
        try:
            for _ in proc.stdout:  # type: ignore[union-attr]
                pass
        except Exception:
            pass

    threading.Thread(target=_drain, daemon=True).start()

    def stop():
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    return url, stop


# ── cloudflared Quick Tunnel ──────────────────────────────────────────────────

_CF_URL_RE = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")


def _try_cloudflared(port: int) -> tuple[str, Callable]:
    """Start a Cloudflare Quick Tunnel using the cloudflared binary."""
    binary = shutil.which("cloudflared")
    if not binary:
        raise TunnelError("cloudflared binary not found in PATH")

    cmd = [binary, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url: str | None = None
    timeout = 30  # seconds to wait for URL

    deadline = time.monotonic() + timeout
    for line in proc.stdout:  # type: ignore[union-attr]
        m = _CF_URL_RE.search(line)
        if m:
            url = m.group(0)
            break
        if time.monotonic() > deadline:
            proc.terminate()
            raise TunnelError("cloudflared did not provide a URL within timeout")

    if not url:
        proc.terminate()
        raise TunnelError("cloudflared exited without providing a URL")

    # Drain stdout in background so the pipe doesn't block
    def _drain():
        try:
            for _ in proc.stdout:  # type: ignore[union-attr]
                pass
        except Exception:
            pass

    threading.Thread(target=_drain, daemon=True).start()

    def stop():
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    return url, stop


# ── Public API ─────────────────────────────────────────────────────────────────

_PROVIDERS = [
    ("localhost.run", _try_localhost_run),
    ("cloudflared", _try_cloudflared),
]


def available_providers() -> list[str]:
    """Return names of providers that appear to be usable on this machine."""
    names = []
    if shutil.which("ssh"):
        names.append("localhost.run")
    if shutil.which("cloudflared"):
        names.append("cloudflared")
    return names


def start_tunnel(port: int, provider: str | None = None) -> tuple[str, Callable]:
    """
    Start a tunnel to *port* and return ``(public_url, stop_fn)``.

    Parameters
    ----------
    port:
        Local port the HTTP server is listening on.
    provider:
        ``"localhost.run"`` or ``"cloudflared"``.
        If *None*, the first available provider is used automatically.

    Raises
    ------
    TunnelError
        If no provider is available or the tunnel fails to start.
    """
    candidates = (
        [(name, fn) for name, fn in _PROVIDERS if name == provider]
        if provider
        else _PROVIDERS
    )

    last_err: Exception = TunnelError("No tunnel provider available")
    for name, fn in candidates:
        try:
            url, stop = fn(port)
            return url, stop
        except TunnelError as exc:
            last_err = exc

    raise last_err
