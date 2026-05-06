"""Utility helpers for LocalShare."""

import os
import socket


def get_local_ip() -> str:
    """Return the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def format_size(size: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


_EXT_ICONS: dict[str, str] = {
    # Documents
    ".pdf": "📄", ".doc": "📝", ".docx": "📝",
    ".txt": "📄", ".md": "📄", ".rtf": "📄",
    # Spreadsheets / Presentations
    ".xls": "📊", ".xlsx": "📊", ".csv": "📊",
    ".ppt": "📊", ".pptx": "📊",
    # Images
    ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
    ".gif": "🖼️", ".webp": "🖼️", ".svg": "🖼️",
    ".bmp": "🖼️", ".ico": "🖼️", ".tiff": "🖼️",
    # Video
    ".mp4": "🎬", ".mkv": "🎬", ".avi": "🎬",
    ".mov": "🎬", ".webm": "🎬", ".flv": "🎬",
    # Audio
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵",
    ".ogg": "🎵", ".aac": "🎵", ".m4a": "🎵",
    # Archives
    ".zip": "📦", ".rar": "📦", ".7z": "📦",
    ".tar": "📦", ".gz": "📦", ".bz2": "📦",
    # Code
    ".py": "🐍", ".js": "📜", ".ts": "📜",
    ".html": "🌐", ".css": "🎨", ".json": "📋",
    ".xml": "📋", ".yaml": "📋", ".yml": "📋",
    ".sh": "⚙️", ".bat": "⚙️", ".ps1": "⚙️",
    # Executables / Installers
    ".exe": "⚙️", ".msi": "⚙️", ".dmg": "⚙️",
    ".deb": "⚙️", ".rpm": "⚙️", ".appimage": "⚙️",
}


def get_file_icon(filename: str) -> str:
    """Return an emoji icon for the given filename based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    return _EXT_ICONS.get(ext, "📄")
