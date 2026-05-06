# LocalShare

A lightweight, zero-dependency local network file sharing tool with a GUI.  
Share any folder on your LAN — other devices browse and download files from a browser with no app required.

---

## Features

- **Zero dependencies** — uses Python's standard library only (`tkinter`, `http.server`)
- **Cross-platform** — Windows, macOS, Linux
- **Non-ASCII filename support** — RFC 5987 encoding for filenames with special characters
- **Path-traversal safe** — requests cannot escape the shared folder
- **Dark UI** with breadcrumb navigation and file-type icons
- Click the URL in the app to copy it to the clipboard

---

## Project Structure

```
.
├── main.py       # Entry point — launches the GUI
├── gui.py        # Tkinter window and all UI logic
├── server.py     # HTTP server, request handler, directory/file serving
├── utils.py      # Shared helpers (IP detection, file size, icons)
├── build.py      # PyInstaller build script
├── README.md
└── RELEASE.md    # Release checklist / packaging instructions
```

---

## Running from Source

### Requirements

- Python 3.10 or later
- `tkinter` must be available (included with most Python distributions)

### Clone the Repository

```bash
git clone https://github.com/haydarkadioglu/localshare.git
cd localshare
```

### Install Dependencies

```powershell
# Windows
pip install -r requirements.txt
```

```bash
# macOS / Linux
pip3 install -r requirements.txt
```

### Windows

```powershell
python main.py
```

> If tkinter is missing, reinstall Python and check **"tcl/tk and IDLE"** during setup.

### macOS

```bash
python3 main.py
```

> On Apple Silicon (M1/M2/M3), the system Python may lack tkinter.  
> Install via Homebrew: `brew install python-tk`

### Linux (Debian / Ubuntu / Kali)

```bash
sudo apt install python3-tk   # install tkinter if missing
pip3 install -r requirements.txt
python3 main.py
```

### Linux (Fedora / RHEL)

```bash
sudo dnf install python3-tkinter
pip3 install -r requirements.txt
python3 main.py
```

---

## How to Use

1. Run `python main.py`
2. Click **Browse** and select the folder you want to share
3. (Optional) Change the port number — default is `8080`
4. Click **Start**
5. Open the displayed URL (e.g. `http://192.168.1.10:8080/`) on any device on the same network

> Click the URL label in the app to copy it to the clipboard.

---

## Building a Standalone Executable

See [RELEASE.md](RELEASE.md) for full instructions.

Quick start:

```bash
pip install pyinstaller
python build.py              # single-file exe (default)
python build.py --onedir     # folder bundle (faster startup)
python build.py --debug      # keep console window
```

The output is placed in the `dist/` folder.

---

## Public Link via Tunneling

LocalShare can expose your server to the internet using a tunnel provider.  
Click **🌐 Get Public Link** in the app after starting the server.

### Option 1 — ngrok (recommended, works everywhere)

```bash
pip install pyngrok
```

On first use, ngrok will ask for an auth token. Sign up free at [ngrok.com](https://ngrok.com), then:

```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Option 2 — cloudflared (no account required)

Download the binary for your platform from [developers.cloudflare.com](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) and place it in your PATH.

| Platform | Install |
|----------|---------|
| Windows  | `winget install Cloudflare.cloudflared` |
| macOS    | `brew install cloudflared` |
| Linux    | Download `.deb` / `.rpm` / binary from the link above |

Once either provider is installed, the app auto-detects it — no extra configuration needed.

> **Note:** Public links are temporary (valid only while the app is running) and accessible to anyone who has the URL. Stop the tunnel when you're done.

---

## Security Notes

- The server listens on `0.0.0.0` — all devices on your network can access the shared folder.
- Stop the server when you no longer need to share.
- Only share folders you intend to be publicly readable on your local network.
- Path-traversal attacks are blocked; requests cannot navigate above the shared folder.

---

## License

MIT
