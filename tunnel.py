"""
Tunnel helpers for LocalShare.

Supported providers (in priority order):
  1. pyngrok  — pip install pyngrok  (wraps ngrok binary automatically)
  2. cloudflared — free Cloudflare Quick Tunnel, no account required
                   install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

Usage
-----
    from tunnel import start_tunnel, stop_tunnel

    url, stop = start_tunnel(8080)   # url = "https://xxxx.ngrok-free.app" or trycloudflare.com
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


# ── ngrok via pyngrok ─────────────────────────────────────────────────────────

def _try_pyngrok(port: int) -> tuple[str, Callable]:
    """Start an ngrok tunnel using the pyngrok package."""
    try:
        from pyngrok import ngrok, conf  # type: ignore
    except ImportError:
        raise TunnelError("pyngrok not installed")

    tunnel = ngrok.connect(port, "http")
    url: str = tunnel.public_url
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)

    def stop():
        try:
            ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
        except Exception:
            pass

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
    ("ngrok (pyngrok)", _try_pyngrok),
    ("cloudflared", _try_cloudflared),
]


def available_providers() -> list[str]:
    """Return names of providers that appear to be usable on this machine."""
    names = []
    # pyngrok
    try:
        import pyngrok  # noqa: F401  type: ignore
        names.append("ngrok (pyngrok)")
    except ImportError:
        pass
    # cloudflared
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
        ``"ngrok (pyngrok)"`` or ``"cloudflared"``.
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
