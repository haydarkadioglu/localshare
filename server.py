"""HTTP file-sharing server for LocalShare."""

import datetime
import html
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, unquote

from utils import format_size, get_file_icon


def _rfc5987_encode(filename: str) -> str:
    """Percent-encode a filename for use in RFC 5987 Content-Disposition."""
    return quote(filename, safe="")


def _content_disposition(filename: str) -> str:
    """
    Build a safe Content-Disposition header value that handles non-ASCII
    filenames via RFC 5987 (filename*=UTF-8''...).
    """
    try:
        filename.encode("latin-1")
        # Pure ASCII-safe name — use simple form
        return f'attachment; filename="{filename}"'
    except (UnicodeEncodeError, UnicodeDecodeError):
        encoded = _rfc5987_encode(filename)
        return f"attachment; filename*=UTF-8''{encoded}"


class FileShareHandler(BaseHTTPRequestHandler):
    """Serves a single shared directory over HTTP."""

    # Set by the GUI before the server starts.
    server_folder: str = ""

    # ── Logging ────────────────────────────────────────────────────────────

    def log_message(self, fmt, *args):  # suppress console noise
        pass

    # ── Request routing ────────────────────────────────────────────────────

    def do_GET(self):
        raw_path = unquote(self.path).split("?")[0]

        # Redirect bare root to /
        if raw_path == "":
            self._redirect("/")
            return

        base = os.path.normpath(self.server_folder)
        rel = raw_path.lstrip("/")
        target = os.path.normpath(os.path.join(base, rel)) if rel else base

        # Path-traversal guard
        if not target.startswith(base):
            self._send_error(403, "Forbidden")
            return

        if os.path.isdir(target):
            self._serve_directory(target, raw_path)
        elif os.path.isfile(target):
            self._serve_file(target)
        else:
            self._send_error(404, "Not Found")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _redirect(self, location: str):
        self.send_response(301)
        self.send_header("Location", location)
        self.end_headers()

    def _send_error(self, code: int, message: str):
        body = message.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── Directory listing ──────────────────────────────────────────────────

    def _serve_directory(self, full_path: str, url_path: str):
        if not url_path.endswith("/"):
            self._redirect(url_path + "/")
            return

        try:
            entries = os.listdir(full_path)
        except PermissionError:
            self._send_error(403, "Forbidden")
            return

        entries.sort(
            key=lambda x: (not os.path.isdir(os.path.join(full_path, x)), x.lower())
        )

        # ── Breadcrumb
        parts = [p for p in url_path.strip("/").split("/") if p]
        crumb_html = '<a href="/">🏠 Home</a>'
        cumulative = ""
        for i, part in enumerate(parts):
            cumulative += "/" + part
            if i == len(parts) - 1:
                crumb_html += f' / <span class="cur">{html.escape(part)}</span>'
            else:
                crumb_html += f' / <a href="{cumulative}/">{html.escape(part)}</a>'

        # ── Table rows
        rows = ""

        if url_path != "/":
            parent = url_path.rstrip("/").rsplit("/", 1)[0] + "/"
            rows += (
                f'<tr><td>📁</td>'
                f'<td><a href="{parent}">..</a></td>'
                f'<td></td><td></td></tr>'
            )

        for entry in entries:
            ep = os.path.join(full_path, entry)
            eu = url_path + quote(entry)
            if os.path.isdir(ep):
                eu += "/"
                icon = "📁"
                size_str = "—"
                row_cls = "d"
            else:
                icon = get_file_icon(entry)
                try:
                    size_str = format_size(os.path.getsize(ep))
                except OSError:
                    size_str = "—"
                row_cls = "f"

            try:
                dt = datetime.datetime.fromtimestamp(
                    os.path.getmtime(ep)
                ).strftime("%Y-%m-%d %H:%M")
            except OSError:
                dt = "—"

            rows += (
                f'<tr class="{row_cls}">'
                f'<td>{icon}</td>'
                f'<td><a href="{eu}">{html.escape(entry)}</a></td>'
                f'<td>{size_str}</td>'
                f'<td>{dt}</td>'
                f'</tr>'
            )

        if not rows:
            rows = (
                '<tr><td colspan="4" style="text-align:center;color:#555;'
                'padding:40px">Folder is empty</td></tr>'
            )

        page = _DIRECTORY_TEMPLATE.format(
            crumb=crumb_html,
            rows=rows,
        )
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── File download ──────────────────────────────────────────────────────

    def _serve_file(self, full_path: str):
        mime, _ = mimetypes.guess_type(full_path)
        if not mime:
            mime = "application/octet-stream"

        fname = os.path.basename(full_path)
        disposition = _content_disposition(fname)

        try:
            size = os.path.getsize(full_path)
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", disposition)
            self.end_headers()
            with open(full_path, "rb") as fh:
                while True:
                    chunk = fh.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (OSError, BrokenPipeError):
            pass


def create_server(folder: str, port: int) -> HTTPServer:
    """Create and return an HTTPServer bound to *port* serving *folder*."""
    FileShareHandler.server_folder = folder
    return HTTPServer(("0.0.0.0", port), FileShareHandler)


# ── HTML template ──────────────────────────────────────────────────────────────

_DIRECTORY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LocalShare</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:#111;color:#ddd;min-height:100vh}}
header{{background:linear-gradient(135deg,#1a1a2e,#16213e);
        padding:18px 28px;border-bottom:1px solid #222;
        display:flex;align-items:center;gap:12px}}
header h1{{font-size:1.25rem;color:#4fc3f7;font-weight:700}}
.crumb{{font-size:.8rem;color:#777;padding:10px 28px;
        border-bottom:1px solid #1a1a1a}}
.crumb a{{color:#4fc3f7;text-decoration:none}}
.crumb a:hover{{text-decoration:underline}}
.crumb .cur{{color:#ddd}}
.wrap{{padding:0 16px 40px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 14px;color:#666;font-size:.75rem;
    text-transform:uppercase;letter-spacing:.06em;
    border-bottom:1px solid #222}}
td{{padding:9px 14px;border-bottom:1px solid #181818;font-size:.9rem}}
tr:hover td{{background:#1a1a2e}}
tr.d td:nth-child(2) a{{color:#4fc3f7}}
tr.f td:nth-child(2) a{{color:#ddd}}
td:nth-child(1){{width:34px;font-size:1.1rem}}
td:nth-child(3){{color:#666;text-align:right;width:90px;font-size:.82rem}}
td:nth-child(4){{color:#555;font-size:.78rem;width:130px}}
a{{text-decoration:none}}
a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<header>
  <span style="font-size:1.6rem">📂</span>
  <h1>LocalShare</h1>
</header>
<div class="crumb">{crumb}</div>
<div class="wrap">
<table>
<thead>
  <tr>
    <th></th>
    <th>Name</th>
    <th style="text-align:right">Size</th>
    <th>Modified</th>
  </tr>
</thead>
<tbody>{rows}</tbody>
</table>
</div>
</body>
</html>"""
